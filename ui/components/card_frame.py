import tkinter as tk
from tkinter import ttk

class CardFrame(tk.LabelFrame):
    """带标题的统一卡片容器"""
    def __init__(self, parent, title, padx=10, pady=5, **kwargs):
        # 拦截用于 pack 的布局参数，防止传入 LabelFrame 导致 unknown option "-fill"
        pack_fill = kwargs.pop("fill", "x")
        pack_expand = kwargs.pop("expand", False)
        
        super().__init__(parent, text=title, font=("Arial", 10, "bold"), padx=padx, pady=pady, **kwargs)
        self.pack(fill=pack_fill, expand=pack_expand, padx=10, pady=5)
