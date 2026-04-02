import tkinter as tk
from tkinter import ttk
from ui.components.card_frame import CardFrame
from ui.components.buttons import PrimaryButton, DangerButton, StandardButton

class HardwareControlPanel(CardFrame):
    """硬件串口与发动机马达控制相关的业务模块"""
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, title="1 & 2. 硬件与马达控制", **kwargs)
        self.controller = controller  # 指向顶层录音业务类
        
        # --- 串口设置 ---
        f_serial = tk.Frame(self)
        f_serial.pack(fill="x", pady=2)
        
        tk.Label(f_serial, text="选择串口:").grid(row=0, column=0, sticky="w")
        self.controller.port_combo = ttk.Combobox(f_serial, width=12)
        self.controller.port_combo.grid(row=0, column=1, padx=2)
        
        StandardButton(f_serial, text="刷新", command=self.controller.refresh_ports).grid(row=0, column=2, padx=2)
        self.controller.btn_connect = tk.Button(f_serial, text="连接", command=self.controller.toggle_serial, bg="#90EE90")
        self.controller.btn_connect.grid(row=0, column=3, padx=2)

        # --- 马达转速设置 ---
        f_motor = tk.Frame(self)
        f_motor.pack(fill="x", pady=(10,0))
        
        tk.Label(f_motor, text="输入转速:").grid(row=0, column=0, sticky="w")
        self.controller.speed_entry = tk.Entry(f_motor, width=12)
        self.controller.speed_entry.insert(0, "0")
        self.controller.speed_entry.grid(row=0, column=1, padx=5)
        
        StandardButton(f_motor, text="发送指令", command=self.controller.send_speed).grid(row=0, column=2, padx=5)
        DangerButton(f_motor, text="紧急停止电机", command=self.controller.stop_motor).grid(row=1, column=0, columnspan=3, pady=5)
