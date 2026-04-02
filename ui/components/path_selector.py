import tkinter as tk
from tkinter import filedialog
from ui.components.buttons import StandardButton

class PathSelector(tk.Frame):
    """带标签、输入框、浏览按钮的路径选择器组件"""
    def __init__(self, parent, label_text, string_var, row_idx, **kwargs):
        super().__init__(parent, **kwargs)
        self.string_var = string_var
        
        tk.Label(self, text=label_text, width=20, anchor="e").grid(row=row_idx, column=0, sticky="e", pady=2, padx=5)
        tk.Entry(self, textvariable=self.string_var, width=25).grid(row=row_idx, column=1, padx=5)
        StandardButton(self, text="浏览...", command=self._browse_dir).grid(row=row_idx, column=2, padx=5)
        
    def _browse_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.string_var.set(dir_path)
