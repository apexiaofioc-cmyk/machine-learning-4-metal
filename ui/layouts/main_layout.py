import tkinter as tk
from tkinter import ttk
from ui.views.record_view import RecordView
from ui.views.settings_view import SettingsView
from ui.views.train_predict_view import TrainPredictView

class MainLayout:
    """
    第一层 Layouts (外壳与骨架)
    作用：设置整个顶层窗口的背景、标题、渲染样式、并组织两个主要的页面 (Views) 为选项卡结构。
    """
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("声音信号核心中枢 - 组件化高级版")
        self.root.geometry("900x850") # 设置稍大以容纳更多组件
        
        # 统一风格主题
        self.style = ttk.Style(self.root)
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        
        # 1. 创建骨架：多标签页容器
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # 2. 将 Views (页面级组件) 直接挂载到骨架上
        # -> 第一个页面子树：数据录入
        self.tab_record = RecordView(self.notebook, controller=self.controller)
        self.notebook.add(self.tab_record, text="🎙️ 录音采集模块")
        
        # -> 第二个页面子树：系统设置
        self.tab_settings = SettingsView(self.notebook, controller=self.controller)
        self.notebook.add(self.tab_settings, text="⚙️ 系统配置底层面板")

        # -> 第三个页面子树：训练与验证
        self.tab_train_predict = TrainPredictView(self.notebook, controller=self.controller)
        self.notebook.add(self.tab_train_predict, text="🧠 训练与盲测模块")

