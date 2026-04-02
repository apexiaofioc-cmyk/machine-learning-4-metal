import wave
import threading
import datetime
import os
import tkinter as tk
from tkinter import ttk, messagebox
import pyaudio
import serial
import serial.tools.list_ports

from ui.layouts.main_layout import MainLayout
from config import ORIGIN_DATA_DIR, TEST_DIR, SR, INCLUDE_SPEED, INCLUDE_TIMESTAMP, INCLUDE_BALL_COUNT

class DataCollectorApp:

    def __init__(self, root):
        self.root = root
        
        # --- 保持核心模型状态与底层变量 ---
        self.serial_port = None
        self.is_recording = False
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.auto_stop_id = None  
        self.current_speed = "0"  
        
        # 录音底层参数
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = SR
        self.SAVE_DIR = ORIGIN_DATA_DIR

        # --- 连接 UI ---
        # 实例化位于 Layout 的主视图骨架，把自己 (self) 传递过去作为业务处理器
        self.main_layout = MainLayout(self.root, controller=self)
        
        # 如果需要某些初始化执行，可以在这补上，因为组件创建后 `mic_combo` 就有了
        self.refresh_mics()
        self.refresh_ports()

    # ---------------- 隔离出来的核心业务/驱动代码 ----------------
    
    def refresh_mics(self):
        mics = []
        info = self.audio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(0, numdevices):
            if (self.audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                try:
                    device_name = self.audio.get_device_info_by_host_api_device_index(0, i).get('name')
                    mics.append(f"{i}: {device_name}")
                except Exception:
                    mics.append(f"{i}: 未知设备")
                    
        # 在面向对象数据驱动上，应当避免直接操作UI对象，但因重构进度所限，通过暴露变量方式调用
        self.mic_combo['values'] = mics
        if mics:
            self.mic_combo.current(0)
        else:
            self.mic_combo.set("未找到麦克风")

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)

    def toggle_serial(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.btn_connect.config(text="连接", bg="#90EE90")
            self.status_label.config(text="串口已断开")
        else:
            port = self.port_combo.get()
            if not port:
                messagebox.showerror("错误", "请选择串口")
                return
            try:
                self.serial_port = serial.Serial(port, 9600, timeout=1)
                self.btn_connect.config(text="断开", bg="#ff9999")
                self.status_label.config(text=f"已连接至 {port}")
            except Exception as e:
                messagebox.showerror("串口错误", f"无法打开串口:\n{e}")

    def send_speed(self):
        try:
            speed_val = float(self.speed_entry.get())
            if speed_val.is_integer():
                speed_str = str(int(speed_val))
            else:
                speed_str = str(speed_val)
            self.current_speed = speed_str 
            if self.serial_port and self.serial_port.is_open:
                command = f"V{speed_str}\n"
                self.serial_port.write(command.encode('utf-8'))
                self.status_label.config(text=f"已发送转速指令: {speed_str}")
            else:
                messagebox.showwarning("警告", "串口未连接！")
        except ValueError:
            messagebox.showerror("格式错误", "转速必须是有效的数字！")

    def stop_motor(self):
        self.speed_entry.delete(0, tk.END)
        self.speed_entry.insert(0, "0")
        self.send_speed()

    def start_recording(self):
        if self.is_recording: return
        try:
            record_time = int(self.time_entry.get())
            if record_time <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("格式错误", "录音时间必须是大于0的整数(秒)！")
            return

        current_label = self.class_var.get()
        if current_label == 0:
            ball_type = self.class0_name_var.get().strip() or "Class0_Unknown"
        else:
            ball_type = self.class1_name_var.get().strip() or "Class1_Unknown"

        sub_folder = ball_type
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        
        data_type = self.data_type_var.get()
        if data_type == "test":
            target_dir = os.path.join(TEST_DIR, sub_folder)
        else:
            target_dir = os.path.join(ORIGIN_DATA_DIR, sub_folder)
            
        if not os.path.exists(target_dir): os.makedirs(target_dir)

        filename_parts = [f"L{current_label}", ball_type]
        if INCLUDE_SPEED: filename_parts.append(f"v={self.current_speed}")
        if INCLUDE_BALL_COUNT:
            try:
                balls_count = int(self.balls_entry.get().strip())
                filename_parts.append(f"n={balls_count}")
            except ValueError:
                messagebox.showwarning("格式警告", "小球数量应为整数，将忽略小球数量参数！")
        if INCLUDE_TIMESTAMP: filename_parts.append(timestamp)
        base_name = "_".join(filename_parts) + ".wav"
        self.filename = os.path.join(target_dir, base_name)

        selected_mic = self.mic_combo.get()
        device_index = None 
        if selected_mic and ":" in selected_mic:
            try: device_index = int(selected_mic.split(":")[0])
            except ValueError: pass

        try:
            self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE, 
                                          input=True, input_device_index=device_index, frames_per_buffer=self.CHUNK)
        except Exception as e:
            messagebox.showerror("麦克风错误", f"无法打开音频设备:\n{e}")
            return

        self.is_recording = True
        self.frames = []
        
        self.btn_record.config(state="disabled")
        self.btn_stop_record.config(state="normal")
        self.status_label.config(text=f"录音中... (设定 {record_time}秒)", fg="red")

        threading.Thread(target=self._record_thread, daemon=True).start()
        self.auto_stop_id = self.root.after(record_time * 1000, self.stop_recording)

    def _record_thread(self):
        while self.is_recording:
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                self.frames.append(data)
            except Exception:
                break

    def stop_recording(self):
        if not self.is_recording: return
        if self.auto_stop_id:
            self.root.after_cancel(self.auto_stop_id)
            self.auto_stop_id = None
        self.is_recording = False
        self.status_label.config(text="正在保存数据...", fg="orange")
        self.root.update()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        try:
            wf = wave.open(self.filename, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
        except Exception as e:
            messagebox.showerror("保存错误", f"保存音频文件失败:\n{e}")

        # 如果录制时间结束，不要自动退出整个程序，只需停止当前录音即可
        self.btn_record.config(state="normal")
        self.btn_stop_record.config(state="disabled")
        self.status_label.config(text=f"保存成功: {os.path.basename(self.filename)}", fg="green")

    def on_closing(self):
        if self.is_recording: self.stop_recording()
        self.stop_motor() 
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.audio.terminate()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DataCollectorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
