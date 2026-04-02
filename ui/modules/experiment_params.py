import tkinter as tk
from tkinter import ttk
from ui.components.card_frame import CardFrame

from config import NAMING_PREFIX_ALUMI, NAMING_PREFIX_STEEL

class ExperimentParamsPanel(CardFrame):
    """二分类材料选取、参数录入模块"""
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, title="3. 二分类材质与标签设定", **kwargs)
        self.controller = controller
        
        tk.Label(self, text="录制当前材质 (标签将自动绑定):", fg="#0052cc", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        self.controller.class_var = tk.IntVar(value=0) # 0 或 1，记录当前选中的是哪个类

        # 类别 0 (原铝球)
        tk.Radiobutton(self, text="类别 0 (Label=0):", variable=self.controller.class_var, value=0).grid(row=1, column=0, sticky="w")
        self.controller.class0_name_var = tk.StringVar(value=NAMING_PREFIX_ALUMI)
        tk.Entry(self, textvariable=self.controller.class0_name_var, width=14).grid(row=1, column=1, padx=5)

        # 类别 1 (原钢球)
        tk.Radiobutton(self, text="类别 1 (Label=1):", variable=self.controller.class_var, value=1).grid(row=2, column=0, sticky="w", pady=5)
        self.controller.class1_name_var = tk.StringVar(value=NAMING_PREFIX_STEEL)
        tk.Entry(self, textvariable=self.controller.class1_name_var, width=14).grid(row=2, column=1, padx=5)

        # 录制时间
        tk.Label(self, text="设定录音时间(秒):").grid(row=3, column=0, sticky="w", pady=5)
        self.controller.time_entry = tk.Entry(self, width=10)
        self.controller.time_entry.insert(0, "10") 
        self.controller.time_entry.grid(row=3, column=1, sticky="w")

        # 小球数量
        tk.Label(self, text="设定小球数量(个):").grid(row=4, column=0, sticky="w", pady=5)
        self.controller.balls_entry = tk.Entry(self, width=10)
        self.controller.balls_entry.insert(0, "10")
        self.controller.balls_entry.grid(row=4, column=1, sticky="w")
