import wave
import threading
import datetime
import os
import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from tkinter import filedialog

import serial
import serial.tools.list_ports
import pyaudio

from config import (GATHER_DATA_DIR, ORIGIN_DATA_DIR, TRAIN_DATA_DIR, TEST_DIR, MODEL_SAVE_DIR, 
                    SR, BATCH_SIZE, EPOCHS, 
                    NAMING_PREFIX_ALUMI, NAMING_PREFIX_STEEL,
                    INCLUDE_TIMESTAMP, INCLUDE_SPEED)

class DataCollectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("声音信号采集系统 - 智能增强版")
        self.root.geometry("900x750") # 扩大UI界面，留出右侧动画和可视化区 
        
        # 应用现代主题
        self.style = ttk.Style(self.root)
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        
        # --- 变量初始化 ---
        self.serial_port = None
        self.is_recording = False
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.auto_stop_id = None  
        self.current_speed = "0"  
        
        # 录音参数
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = SR
        self.SAVE_DIR = GATHER_DATA_DIR #保存文件夹
        if not os.path.exists(self.SAVE_DIR):
            os.makedirs(self.SAVE_DIR)

        # 引入 Notebook 实现多标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.tab_record = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_record, text="🎙️ 录音采集")
        
        self.tab_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settings, text="⚙️ 参数与路径设置")

        self.setup_ui()
        self.setup_settings_ui()

    def setup_ui(self):
        # ================= Tab 1: 主功能页布局 (左右分栏) =================
        self.pane = ttk.PanedWindow(self.tab_record, orient=tk.HORIZONTAL)
        self.pane.pack(fill="both", expand=True, padx=5, pady=5)

        self.left_frame = ttk.Frame(self.pane)
        self.right_frame = ttk.Frame(self.pane)
        
        # 左侧控制面板占据 1 份，右侧动画区占据 1.2 份
        self.pane.add(self.left_frame, weight=10)
        self.pane.add(self.right_frame, weight=12)

        # ---------------- 右侧：动画可视化区域预留 ----------------
        frame_visual = tk.LabelFrame(self.right_frame, text="✨ 实时数据/动画可视化", font=("Arial", 11, "bold"), padx=10, pady=10)
        frame_visual.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.anim_canvas = tk.Canvas(frame_visual, bg="#1E1E1E")
        self.anim_canvas.pack(fill="both", expand=True)
        # 预留提示文本，之后可以替换为实时波形或小球动画
        self.anim_canvas.create_text(250, 250, text="[动画与可视化预留区]", fill="#888888", font=("Arial", 16, "bold"), tags="hint")
        self.anim_canvas.create_text(250, 280, text="后续可在此处绘制小球动态或频域图", fill="#666666", font=("Arial", 11), tags="hint")

        # ---------------- 左侧：数据采集控制面板 ----------------
        # ================= 1. 硬件连接 =================
        frame_serial = tk.LabelFrame(self.left_frame, text="1. 硬件连接 (串口)", padx=10, pady=5)
        frame_serial.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_serial, text="选择串口:").grid(row=0, column=0, sticky="w")
        self.port_combo = ttk.Combobox(frame_serial, width=12)
        self.port_combo.grid(row=0, column=1, padx=2)
        self.refresh_ports()
        tk.Button(frame_serial, text="刷新", command=self.refresh_ports).grid(row=0, column=2, padx=2)
        self.btn_connect = tk.Button(frame_serial, text="连接", command=self.toggle_serial, bg="#90EE90")
        self.btn_connect.grid(row=0, column=3, padx=2)

        # ================= 2. 发动机转速 =================
        frame_motor = tk.LabelFrame(self.left_frame, text="2. 马达转速设置", padx=10, pady=5)
        frame_motor.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_motor, text="输入转速:").grid(row=0, column=0, sticky="w")
        self.speed_entry = tk.Entry(frame_motor, width=12)
        self.speed_entry.insert(0, "0") 
        self.speed_entry.grid(row=0, column=1, padx=5)
        tk.Button(frame_motor, text="发送指令", command=self.send_speed).grid(row=0, column=2, padx=5)
        tk.Button(frame_motor, text="紧急停止电机", command=self.stop_motor, fg="red").grid(row=1, column=0, columnspan=3, pady=5)

        # ================= 3. 二分类实验参数设置 =================
        frame_exp = tk.LabelFrame(self.left_frame, text="3. 二分类材质与标签设定", padx=10, pady=10)
        frame_exp.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_exp, text="录制当前材质 (标签将自动绑定):", fg="#0052cc", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        self.class_var = tk.IntVar(value=0) # 0 或 1，记录当前选中的是哪个类

        # 类别 0 (原铝球)
        tk.Radiobutton(frame_exp, text="类别 0 (Label=0):", variable=self.class_var, value=0).grid(row=1, column=0, sticky="w")
        self.class0_name_var = tk.StringVar(value=NAMING_PREFIX_ALUMI)
        tk.Entry(frame_exp, textvariable=self.class0_name_var, width=14).grid(row=1, column=1, padx=5)

        # 类别 1 (原钢球)
        tk.Radiobutton(frame_exp, text="类别 1 (Label=1):", variable=self.class_var, value=1).grid(row=2, column=0, sticky="w", pady=5)
        self.class1_name_var = tk.StringVar(value=NAMING_PREFIX_STEEL)
        tk.Entry(frame_exp, textvariable=self.class1_name_var, width=14).grid(row=2, column=1, padx=5)

        # 录制时间
        tk.Label(frame_exp, text="设定录音时间(秒):").grid(row=3, column=0, sticky="w", pady=5)
        self.time_entry = tk.Entry(frame_exp, width=10)
        self.time_entry.insert(0, "10") 
        self.time_entry.grid(row=3, column=1, sticky="w")

        # ================= 4. 数据采集核心 =================
        frame_audio = tk.LabelFrame(self.left_frame, text="4. 数据采集", padx=10, pady=10)
        frame_audio.pack(fill="both", expand=True, padx=10, pady=5)

        mic_frame = tk.Frame(frame_audio)
        mic_frame.pack(fill="x", pady=2)
        tk.Label(mic_frame, text="录音设备:").pack(side="left")
        self.mic_combo = ttk.Combobox(mic_frame, width=22)
        self.mic_combo.pack(side="left", padx=5)
        tk.Button(mic_frame, text="刷新", command=self.refresh_mics).pack(side="left")
        self.refresh_mics() # 初始化

        self.btn_record = tk.Button(frame_audio, text="● 开始录制当前材质", font=("Arial", 12, "bold"), bg="#ff9999", command=self.start_recording)
        self.btn_record.pack(pady=10, fill="x")

        self.btn_stop_record = tk.Button(frame_audio, text="⏹ 提前结束录音", font=("Arial", 10), command=self.stop_recording, state="disabled")
        self.btn_stop_record.pack(pady=5, fill="x")

        self.status_label = tk.Label(frame_audio, text="状态: 待机中...", fg="blue", font=("Arial", 10))
        self.status_label.pack(pady=5)

    def setup_settings_ui(self):
        # ================= 设置标签页 =================
        self.settings_vars = {}
        
        # 尝试读取 config.json
        self.settings_file = Path("settings.json").resolve()
        self.current_settings = {}
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.current_settings = json.load(f)
            except:
                pass

        # === 路径配置区 ===
        f_paths = tk.LabelFrame(self.tab_settings, text="📁 核心路径配置", padx=10, pady=10)
        f_paths.pack(fill="x", padx=10, pady=5)
        
        paths = [
            ("录音保存主目录 (Gather)", "gather_data_dir", str(GATHER_DATA_DIR)),
            ("原始数据目录 (Origin)", "origin_data_dir", str(ORIGIN_DATA_DIR)),
            ("训练数据目录 (Train)", "train_data_dir", str(TRAIN_DATA_DIR)),
            ("盲测数据目录 (Test)", "test_dir", str(TEST_DIR)),
            ("模型保存目录 (Model)", "model_save_dir", str(MODEL_SAVE_DIR))
        ]
        
        for i, (label_text, key, fallback_val) in enumerate(paths):
            tk.Label(f_paths, text=label_text).grid(row=i, column=0, sticky="e", pady=2)
            # 如果 JSON 中没有，则向全局变量请求回显
            var = tk.StringVar(value=self.current_settings.get(key, fallback_val))
            self.settings_vars[key] = var
            tk.Entry(f_paths, textvariable=var, width=25).grid(row=i, column=1, padx=5)
            tk.Button(f_paths, text="浏览...", command=lambda k=key: self._browse_dir(k)).grid(row=i, column=2)

        # === 其他参数区 ===
        f_params = tk.LabelFrame(self.tab_settings, text="⚙️ 命名与训练参数", padx=10, pady=10)
        f_params.pack(fill="x", padx=10, pady=5)

        params = [
            ("铝球文件前缀:", "naming_prefix_alumi", NAMING_PREFIX_ALUMI),
            ("钢球文件前缀:", "naming_prefix_steel", NAMING_PREFIX_STEEL),
            ("Epochs (训练轮数):", "epochs", EPOCHS),
            ("Batch Size:", "batch_size", BATCH_SIZE),
            ("采样率 (SR):", "sr", SR)
        ]

        for i, (label_text, key, fallback_val) in enumerate(params):
            tk.Label(f_params, text=label_text).grid(row=i, column=0, sticky="e", pady=2)
            var = tk.StringVar(value=str(self.current_settings.get(key, fallback_val)))
            self.settings_vars[key] = var
            tk.Entry(f_params, textvariable=var, width=15).grid(row=i, column=1, sticky="w", padx=5)

        # 选项框
        self.settings_vars["include_speed"] = tk.BooleanVar(value=self.current_settings.get("include_speed", INCLUDE_SPEED))
        tk.Checkbutton(f_params, text="自动包含马达转速到文件名", variable=self.settings_vars["include_speed"]).grid(row=5, column=0, columnspan=2, sticky="w")
        
        self.settings_vars["include_timestamp"] = tk.BooleanVar(value=self.current_settings.get("include_timestamp", INCLUDE_TIMESTAMP))
        tk.Checkbutton(f_params, text="自动包含时间戳到文件名", variable=self.settings_vars["include_timestamp"]).grid(row=6, column=0, columnspan=2, sticky="w")

        # 底部按钮
        tk.Button(self.tab_settings, text="💾 立即保存配置 (需重启应用生效)", bg="#90EE90", font=("Arial", 11, "bold"), command=self.save_settings).pack(pady=20)

    def _browse_dir(self, key):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.settings_vars[key].set(dir_path)

    def save_settings(self):
        new_settings = self.current_settings.copy()
        for k, v in self.settings_vars.items():
            val = v.get()
            if isinstance(val, str):
                if val.isdigit(): val = int(val)
                elif val.replace('.','',1).isdigit() and val.count('.')<2: val = float(val)
            new_settings[k] = val
            
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(new_settings, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("成功", "配置已保存至 settings.json！\n部分改动（如下一次录音的保存路径、材质名称等）将在重启程序后生效。")
        except Exception as e:
            messagebox.showerror("保存失败", f"发生错误：{e}")

    # --- 麦克风选择功能 (新增) ---
    def refresh_mics(self):
        """扫描系统中所有的音频输入设备"""
        mics = []
        info = self.audio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        
        for i in range(0, numdevices):
            # 只要 maxInputChannels > 0，就说明它是麦克风（输入设备）
            if (self.audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                try:
                    # 获取设备名称，处理可能出现的中文乱码
                    device_name = self.audio.get_device_info_by_host_api_device_index(0, i).get('name')
                    # 格式： "编号: 设备名"
                    mics.append(f"{i}: {device_name}")
                except Exception:
                    mics.append(f"{i}: 未知设备")
                    
        self.mic_combo['values'] = mics
        if mics:
            self.mic_combo.current(0) # 默认选中第一个
        else:
            self.mic_combo.set("未找到麦克风")

    # --- 串口与马达控制 ---
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
            # 1. 尝试将输入转换为浮点数 (float) 而不是整数 (int)
            speed_val = float(self.speed_entry.get())
            
            # 2. 智能格式化：如果是像 1500.0 这样的整数，就去掉小数点变成 1500
            if speed_val.is_integer():
                speed_str = str(int(speed_val))
            else:
                speed_str = str(speed_val)
                
            self.current_speed = speed_str # 保存当前转速用于命名
            
            if self.serial_port and self.serial_port.is_open:
                # 组合指令，例如 "V1500.5\n"
                command = f"V{speed_str}\n"
                self.serial_port.write(command.encode('utf-8'))
                self.status_label.config(text=f"已发送转速指令: {speed_str}")
            else:
                messagebox.showwarning("警告", "串口未连接！\n(当前仅记录转速数值用于文件命名)")
        except ValueError:
            # 3. 修改报错提示
            messagebox.showerror("格式错误", "转速必须是有效的数字（可以是整数或小数）！")

    def stop_motor(self):
        self.speed_entry.delete(0, tk.END)
        self.speed_entry.insert(0, "0")
        self.send_speed()

    # --- 录音功能 ---
    def start_recording(self):
        if self.is_recording:
            return

        # 1. 检查时间输入
        try:
            record_time = int(self.time_entry.get())
            if record_time <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("格式错误", "录音时间必须是大于0的整数(秒)！")
            return

        # 2. 获取当前类标和自定义材料名称
        current_label = self.class_var.get()
        if current_label == 0:
            ball_type = self.class0_name_var.get().strip() or "Class0_Unknown"
            sub_folder = ball_type # 直接将材料名作为子文件夹
        else:
            ball_type = self.class1_name_var.get().strip() or "Class1_Unknown"
            sub_folder = ball_type

        timestamp = datetime.datetime.now().strftime("%H%M%S")
        target_dir = os.path.join(self.SAVE_DIR, sub_folder)
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # 根据配置决定文件名后缀 (包含 label 号码、材质名、转速、时间戳)
        filename_parts = [f"L{current_label}", ball_type]
        if INCLUDE_SPEED:
            filename_parts.append(f"v={self.current_speed}")
        if INCLUDE_TIMESTAMP:
            filename_parts.append(timestamp)

        base_name = "_".join(filename_parts) + ".wav"
        self.filename = os.path.join(target_dir, base_name)

        # 3. ✅ 获取选中的麦克风编号
        selected_mic = self.mic_combo.get()
        device_index = None # 默认不传参数
        if selected_mic and ":" in selected_mic:
            try:
                # 提取字符串前面的编号，例如 "1: USB Microphone" 提取出 1
                device_index = int(selected_mic.split(":")[0])
            except ValueError:
                pass

        # 4. 打开音频流
        try:
            self.stream = self.audio.open(format=self.FORMAT, 
                                          channels=self.CHANNELS,
                                          rate=self.RATE, 
                                          input=True, 
                                          input_device_index=device_index, # ✅ 传入麦克风编号
                                          frames_per_buffer=self.CHUNK)
        except Exception as e:
            messagebox.showerror("麦克风错误", f"无法打开指定的音频设备:\n{e}\n请尝试刷新或选择其他设备。")
            return

        self.is_recording = True
        self.frames = []
        
        # 更新UI
        self.btn_record.config(state="disabled")
        self.btn_stop_record.config(state="normal")
        self.status_label.config(text=f"🔴 录音中... (设定时间: {record_time}秒)", fg="red")

        # 启动后台录音线程
        threading.Thread(target=self._record_thread, daemon=True).start()

        # 设定倒计时自动停止
        self.auto_stop_id = self.root.after(record_time * 1000, self.stop_recording)

    def _record_thread(self):
        while self.is_recording:
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                self.frames.append(data)
            except Exception:
                break

    def stop_recording(self):
        if not self.is_recording:
            return

        if self.auto_stop_id:
            self.root.after_cancel(self.auto_stop_id)
            self.auto_stop_id = None

        self.is_recording = False
        self.status_label.config(text="正在保存数据...", fg="orange")
        self.root.update()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        # 保存文件
        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        self.btn_record.config(state="normal")
        self.btn_stop_record.config(state="disabled")
        self.status_label.config(text=f" 保存成功: {os.path.basename(self.filename)}", fg="green")

    def on_closing(self):
        if self.is_recording:
            self.stop_recording()
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
