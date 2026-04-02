import tkinter as tk
from tkinter import ttk
from ui.modules.hardware_control import HardwareControlPanel
from ui.modules.experiment_params import ExperimentParamsPanel
from ui.modules.visualizer import CanvasVisualizer
from ui.components.card_frame import CardFrame

class RecordView(ttk.Frame):
    """
    具体的页面视图：录音采集功能主页面。
    主要职责：横向切割窗口（左右分栏），往里面塞入各种 Module。
    """
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller = controller  # 保存业务逻辑控制器的引用
        
        # 左右的分裂栏布局
        self.pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.pane.pack(fill="both", expand=True, padx=5, pady=5)

        self.left_frame = ttk.Frame(self.pane)
        self.right_frame = ttk.Frame(self.pane)
        
        # 配比左边占1，右边由于有画布图表占比例大
        self.pane.add(self.left_frame, weight=10)
        self.pane.add(self.right_frame, weight=12)

        # ---------------- 右侧拼装：动画画布库 ----------------
        self.visualizer_module = CanvasVisualizer(self.right_frame)

        # ---------------- 左侧拼装：各种控制组件 ----------------
        
        # 第一块拼装：硬件与马达控制器
        self.hw_panel = HardwareControlPanel(self.left_frame, controller=self.controller)
        
        # 第二块拼装：材质二分类实验参数设定器
        self.exp_panel = ExperimentParamsPanel(self.left_frame, controller=self.controller)
        
        # 第三块拼装：直接在页面上写的麦克风采样器 (也可以拆出去)
        # 这里演示了一半由自己写，不一定全要强制拆成模块
        self.audio_panel = CardFrame(self.left_frame, title="4. 核心采集控制", fill="both", expand=True)

        mic_frame = tk.Frame(self.audio_panel)
        mic_frame.pack(fill="x", pady=2)
        tk.Label(mic_frame, text="麦克风:").pack(side="left")
        self.controller.mic_combo = ttk.Combobox(mic_frame, width=22)
        self.controller.mic_combo.pack(side="left", padx=5)
        tk.Button(mic_frame, text="🔄", command=self.controller.refresh_mics).pack(side="left")

        # 将按钮绑定到业务控制器的业务方法上
        self.controller.btn_record = tk.Button(self.audio_panel, text="● 开始录入当前材质", 
                                              font=("Arial", 12, "bold"), bg="#ff9999", 
                                              command=self.controller.start_recording)
        self.controller.btn_record.pack(pady=10, fill="x")

        self.controller.btn_stop_record = tk.Button(self.audio_panel, text="⏹ 停止录音", 
                                                    command=self.controller.stop_recording, state="disabled")
        self.controller.btn_stop_record.pack(pady=5, fill="x")

        self.controller.status_label = tk.Label(self.audio_panel, text="状态: 初始化中...", fg="blue")
        self.controller.status_label.pack(pady=5)
