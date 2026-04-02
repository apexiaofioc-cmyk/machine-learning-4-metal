import tkinter as tk
from tkinter import ttk

class PrimaryButton(tk.Button):
    """主按钮，如确认、连接、开始"""
    def __init__(self, parent, text, command, **kwargs):
        super().__init__(parent, text=text, command=command, bg="#90EE90", font=("Arial", 11, "bold"), **kwargs)

class DangerButton(tk.Button):
    """危险操作按钮，如停止、断开"""
    def __init__(self, parent, text, command, **kwargs):
        super().__init__(parent, text=text, command=command, fg="red", font=("Arial", 10), **kwargs)

class StandardButton(tk.Button):
    """普通按钮"""
    def __init__(self, parent, text, command, **kwargs):
        super().__init__(parent, text=text, command=command, **kwargs)
