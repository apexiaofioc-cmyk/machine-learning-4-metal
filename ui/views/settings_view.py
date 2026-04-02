import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from ui.components.card_frame import CardFrame
from ui.components.path_selector import PathSelector
from ui.components.buttons import PrimaryButton

from config import (GATHER_DATA_DIR, ORIGIN_DATA_DIR, TRAIN_DATA_DIR, TEST_DIR, MODEL_SAVE_DIR, 
                    SR, BATCH_SIZE, EPOCHS, 
                    NAMING_PREFIX_ALUMI, NAMING_PREFIX_STEEL,
                    INCLUDE_TIMESTAMP, INCLUDE_SPEED)

class SettingsView(ttk.Frame):
    """
    配置与设置的页面。
    主要职责：展示各种配置参数，修改和进行文件 JSON 操作。
    由于 JSON 逻辑也属于业务的纯配置写入部分，可以在内部自给自足。
    """
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller = controller
        self.settings_vars = {}
        
        self.settings_file = Path("settings.json").resolve()
        self.current_settings = {}
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.current_settings = json.load(f)
            except:
                pass

        self._build_ui()

    def _build_ui(self):
        # === 路径配置区 (使用 PathSelector 组件) ===
        f_paths = CardFrame(self, title="📁 核心路径配置", padx=10, pady=10)
        
        paths = [
            ("录音保存主目录 (Gather)", "gather_data_dir", str(GATHER_DATA_DIR)),
            ("原始数据目录 (Origin)", "origin_data_dir", str(ORIGIN_DATA_DIR)),
            ("训练数据目录 (Train)", "train_data_dir", str(TRAIN_DATA_DIR)),
            ("盲测数据目录 (Test)", "test_dir", str(TEST_DIR)),
            ("模型保存目录 (Model)", "model_save_dir", str(MODEL_SAVE_DIR))
        ]
        
        for i, (label_text, key, fallback_val) in enumerate(paths):
            var = tk.StringVar(value=self.current_settings.get(key, fallback_val))
            self.settings_vars[key] = var
            PathSelector(f_paths, label_text=label_text, string_var=var, row_idx=i).pack(fill="x", pady=2)

        # === 其他参数区 (普通 Label + Entry) ===
        f_params = CardFrame(self, title="⚙️ 命名与全局训练参数")

        params = [
            ("标签1文件前缀:", "naming_prefix_alumi", NAMING_PREFIX_ALUMI),
            ("标签2文件前缀:", "naming_prefix_steel", NAMING_PREFIX_STEEL),
            ("Epochs (训练轮数):", "epochs", EPOCHS),
            ("Batch Size:", "batch_size", BATCH_SIZE),
            ("采样率 (SR):", "sr", SR)
        ]

        # 用 Frame 撑开表格
        grid_frame = tk.Frame(f_params)
        grid_frame.pack(fill="x")
        for i, (label_text, key, fallback_val) in enumerate(params):
            tk.Label(grid_frame, text=label_text).grid(row=i, column=0, sticky="e", pady=2)
            var = tk.StringVar(value=str(self.current_settings.get(key, fallback_val)))
            self.settings_vars[key] = var
            tk.Entry(grid_frame, textvariable=var, width=15).grid(row=i, column=1, sticky="w", padx=5)

        # 选项框
        self.settings_vars["include_speed"] = tk.BooleanVar(value=self.current_settings.get("include_speed", INCLUDE_SPEED))
        tk.Checkbutton(grid_frame, text="自动包含马达转速到文件名", variable=self.settings_vars["include_speed"]).grid(row=5, column=0, columnspan=2, sticky="w")
        
        self.settings_vars["include_timestamp"] = tk.BooleanVar(value=self.current_settings.get("include_timestamp", INCLUDE_TIMESTAMP))
        tk.Checkbutton(grid_frame, text="自动包含时间戳到文件名", variable=self.settings_vars["include_timestamp"]).grid(row=6, column=0, columnspan=2, sticky="w")

        # 底部按钮组件
        PrimaryButton(self, text="💾 立即保存配置 (需重启应用生效)", command=self.save_settings).pack(pady=20)

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
            messagebox.showinfo("成功", "配置已成功保存至 settings.json 取代临时系统配置参数！")
        except Exception as e:
            messagebox.showerror("保存失败", f"发生错误：{e}")
