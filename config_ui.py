import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# 获取项目根目录，以便定位 settings.json
BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "settings.json"

# 默认参数字典（当无文件时使用）
DEFAULT_SETTINGS = {
    # 路径配置（默认相对项目根目录）
    "origin_data_dir": "data_origin",
    "train_data_dir": "data_train",
    "test_dir": "data_test",
    "model_save_dir": "model",
    "model_name": "metal_classifier.keras",
    "gather_data_dir": "data_origin",
    
    # 训练/模型参数
    "batch_size": 32,
    "epochs": 50,
    "learning_rate": 0.001,
    "steel_label": 1,
    "alumi_label": 0,
    "random_state": False,
    
    # 音频参数
    "sr": 44100,
    "duration": 0.5,
    "overlap": 0.5,
    "n_fft": 2048,
    "hop_length": 1024,
    
    # 录音与命名方式
    "naming_prefix_alumi": "Alball",
    "naming_prefix_steel": "Stball",
    "include_timestamp": True,
    "include_speed": True
}

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 合并默认值，防止旧版本的 JSON 缺少新字典里的键
                for k, v in DEFAULT_SETTINGS.items():
                    data.setdefault(k, v)
                return data
        except Exception as e:
            print(f"读取配置失败，使用默认值：{e}")
    return DEFAULT_SETTINGS.copy()

def save_settings(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class ConfigUIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("全局参数配置")
        self.root.geometry("600x650")
        
        self.settings = load_settings()
        self.vars = {} # 存储所有 Entry 和 Checkbutton 的变量
        
        self.setup_ui()
        
    def setup_ui(self):
        # 使用 Notebook 方便以后扩展标签页
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- Tab 1: 路径与项目配置 ---
        f_paths = ttk.Frame(notebook)
        notebook.add(f_paths, text="📁 路径配置")
        self.build_path_frame(f_paths)
        
        # --- Tab 2: 音频与训练参数 ---
        f_params = ttk.Frame(notebook)
        notebook.add(f_params, text="⚙️ 训练与音频")
        self.build_params_frame(f_params)
        
        # --- Tab 3: 录音与命名 ---
        f_record = ttk.Frame(notebook)
        notebook.add(f_record, text="🎙️ 采集命名")
        self.build_record_frame(f_record)
        
        # 底部保存按钮
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", pady=10)
        tk.Button(btn_frame, text="💾 保存配置并退出", bg="#90EE90", font=("Arial", 11, "bold"), 
                  command=self.save_and_exit).pack(pady=5)

    def _add_entry(self, parent, row, label_text, key, width=30):
        tk.Label(parent, text=label_text).grid(row=row, column=0, sticky="e", padx=5, pady=5)
        var = tk.StringVar(value=str(self.settings.get(key, "")))
        entry = tk.Entry(parent, textvariable=var, width=width)
        entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        self.vars[key] = var
        return entry

    def build_path_frame(self, parent):
        keys = [
            ("原始数据存放目录 (Origin)", "origin_data_dir"),
            ("训练数据目录 (Train)", "train_data_dir"),
            ("测试数据目录 (Test)", "test_dir"),
            ("模型保存目录 (Model)", "model_save_dir"),
            ("模型文件名称", "model_name"),
            ("录音保存总目录 (Gather)", "gather_data_dir")
        ]
        
        for i, (label, key) in enumerate(keys):
            self._add_entry(parent, i, label, key, 40)
            
            # 增加一个游览按钮
            if key != "model_name":
                tk.Button(parent, text="浏览...", command=lambda k=key: self._browse_dir(k)).grid(row=i, column=2, padx=5)
                
    def _browse_dir(self, key):
        dir_path = filedialog.askdirectory(initialdir=BASE_DIR)
        if dir_path:
            # 尽量使用相对路径存储
            try:
                rel_path = os.path.relpath(dir_path, BASE_DIR)
                self.vars[key].set(rel_path)
            except:
                self.vars[key].set(dir_path)

    def build_params_frame(self, parent):
        # 训练参数
        lf_train = tk.LabelFrame(parent, text="训练参数", padx=10, pady=10)
        lf_train.pack(fill="x", padx=10, pady=5)
        self._add_entry(lf_train, 0, "Batch Size:", "batch_size", 10)
        self._add_entry(lf_train, 1, "Epochs:", "epochs", 10)
        self._add_entry(lf_train, 2, "Learning Rate:", "learning_rate", 10)
        self._add_entry(lf_train, 3, "Steel Label (钢球):", "steel_label", 10)
        self._add_entry(lf_train, 4, "Alumi Label (铝球):", "alumi_label", 10)
        
        # 音频参数
        lf_audio = tk.LabelFrame(parent, text="音频处理参数", padx=10, pady=10)
        lf_audio.pack(fill="x", padx=10, pady=5)
        self._add_entry(lf_audio, 0, "采样率 (SR):", "sr", 10)
        self._add_entry(lf_audio, 1, "单段时长 (Duration):", "duration", 10)
        self._add_entry(lf_audio, 2, "重叠率 (Overlap):", "overlap", 10)
        self._add_entry(lf_audio, 3, "N_FFT:", "n_fft", 10)
        self._add_entry(lf_audio, 4, "步长 (Hop Length):", "hop_length", 10)

    def build_record_frame(self, parent):
        lf = tk.LabelFrame(parent, text="文件名与前缀", padx=10, pady=10)
        lf.pack(fill="x", padx=10, pady=5)
        
        self._add_entry(lf, 0, "铝球材质文件前缀:", "naming_prefix_alumi", 20)
        self._add_entry(lf, 1, "钢球材质文件前缀:", "naming_prefix_steel", 20)
        
        # Checkbuttons
        self.vars["include_speed"] = tk.BooleanVar(value=self.settings.get("include_speed", True))
        tk.Checkbutton(lf, text="文件名包含马达转速 (例如 _v=1500)", variable=self.vars["include_speed"]).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        self.vars["include_timestamp"] = tk.BooleanVar(value=self.settings.get("include_timestamp", True))
        tk.Checkbutton(lf, text="文件名包含时间戳 (例如 _123456)", variable=self.vars["include_timestamp"]).grid(row=3, column=0, columnspan=2, sticky="w", pady=5)

    def save_and_exit(self):
        try:
            # 将变量写回字典 (简单转换类型)
            new_settings = {}
            for k, v in self.vars.items():
                val = v.get()
                # 尝试转换整数和浮点
                if isinstance(val, str):
                    if val.isdigit():
                        val = int(val)
                    else:
                        try:
                            val = float(val)
                        except:
                            pass
                new_settings[k] = val
            
            save_settings(new_settings)
            messagebox.showinfo("成功", "参数已成功保存！\n如果在其他窗口运行，请重启程序以应用新设置。")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("保存失败", f"发生错误：{e}")

if __name__ == "__main__":
    app = tk.Tk()
    ConfigUIApp(app)
    app.mainloop()