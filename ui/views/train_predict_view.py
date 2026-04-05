import os
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from config import ORIGIN_DATA_DIR, TEST_DIR
from ui.workers.ml_workers import TrainWorker, PredictWorker

class TrainPredictView(ttk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        
        # 队列通信机制
        self.log_queue = queue.Queue()
        
        self.setup_ui()
        self.check_queue()  # 定时通过after检查队列
        
    def setup_ui(self):
        # --- 1. 训练区域 ---
        train_lf = ttk.LabelFrame(self, text="💻 模型训练配置", padding=10)
        train_lf.pack(fill="x", padx=10, pady=5)
        
        # 实时获取 data_origin 下的子文件夹
        subfolders = self.get_origin_subfolders()
        
        ttk.Label(train_lf, text="类别1文件夹 (将设为1, 如钢):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cls1_combo = ttk.Combobox(train_lf, values=subfolders, width=20, state="readonly")
        self.cls1_combo.grid(row=0, column=1, sticky="w", padx=5)
        self.cls1_combo.bind("<<ComboboxSelected>>", self.on_cls_combo_selected)
        
        ttk.Label(train_lf, text="类别1标签名:").grid(row=0, column=2, sticky="e", padx=5)
        self.cls1_name_var = tk.StringVar(value="钢球")
        ttk.Entry(train_lf, textvariable=self.cls1_name_var, width=15).grid(row=0, column=3, sticky="w")
        
        ttk.Label(train_lf, text="类别0文件夹 (将设为0, 如铝):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.cls0_combo = ttk.Combobox(train_lf, values=subfolders, width=20, state="readonly")
        self.cls0_combo.grid(row=1, column=1, sticky="w", padx=5)
        self.cls0_combo.bind("<<ComboboxSelected>>", self.on_cls_combo_selected)
        
        ttk.Label(train_lf, text="类别0标签名:").grid(row=1, column=2, sticky="e", padx=5)
        self.cls0_name_var = tk.StringVar(value="铝球")
        ttk.Entry(train_lf, textvariable=self.cls0_name_var, width=15).grid(row=1, column=3, sticky="w")
        
        self.btn_train = tk.Button(train_lf, text="▶ 开始提取并训练", bg="#add8e6", command=self.start_training)
        self.btn_train.grid(row=2, column=0, columnspan=4, pady=10)
        
        # --- 2. 预测区域 ---
        predict_lf = ttk.LabelFrame(self, text="🔍 模型盲测模块", padding=10)
        predict_lf.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(predict_lf, text="选择盲测文件夹:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        
        self.predict_dir_var = tk.StringVar()
        ttk.Entry(predict_lf, textvariable=self.predict_dir_var, width=40, state="readonly").grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Button(predict_lf, text="默认 (选择上面某类同名)", command=self.select_default_test_dir).grid(row=0, column=2, padx=5)
        ttk.Button(predict_lf, text="浏览...", command=self.browse_test_dir).grid(row=0, column=3, padx=5)
        
        self.btn_predict = tk.Button(predict_lf, text="▶ 分析与预测", bg="#90ee90", command=self.start_prediction)
        self.btn_predict.grid(row=1, column=0, columnspan=4, pady=10)
        
        # --- 3. 日志与信息输出区域 ---
        log_lf = ttk.LabelFrame(self, text="📝 系统日志输出 (防卡防刷屏)", padding=5)
        log_lf.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = ScrolledText(log_lf, state="disabled", wrap="word", height=10)
        self.log_text.pack(fill="both", expand=True)

    def get_origin_subfolders(self):
        try:
            if not os.path.exists(ORIGIN_DATA_DIR):
                return []
            return [f.name for f in os.scandir(ORIGIN_DATA_DIR) if f.is_dir()]
        except Exception:
            return []

    def on_cls_combo_selected(self, event):
        # 联动将选择的文件夹名称映射给名称
        cmb = event.widget
        if cmb == self.cls1_combo:
            self.cls1_name_var.set(self.cls1_combo.get())
        elif cmb == self.cls0_combo:
            self.cls0_name_var.set(self.cls0_combo.get())

    def append_log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def start_training(self):
        cls1_folder = self.cls1_combo.get()
        cls0_folder = self.cls0_combo.get()
        
        if not cls1_folder or not cls0_folder:
            messagebox.showwarning("提示", "请先选择需要进行二分类的两个源文件夹！")
            return
            
        cls1_path = os.path.join(ORIGIN_DATA_DIR, cls1_folder)
        cls0_path = os.path.join(ORIGIN_DATA_DIR, cls0_folder)
        
        self.btn_train.config(state="disabled")
        self.append_log("--- 初始化深度学习网络，启动训练工作流 ---")
        
        worker = TrainWorker(cls1_path, cls0_path, self.log_queue)
        worker.start()

    def select_default_test_dir(self):
        # 获取与当前类别名称同名的测试文件夹
        target_name = self.cls1_combo.get() or self.cls0_combo.get()
        if not target_name:
            messagebox.showwarning("提示", "请先在上方配置区选择至少一个训练类别目录作为基础参照！")
            return
            
        candidate_path = os.path.join(TEST_DIR, target_name)
        if os.path.exists(candidate_path):
            self.predict_dir_var.set(candidate_path)
            self.append_log(f"已自动加载盲测目录: {candidate_path}")
        else:
            self.append_log(f"警告：未在该路径下找到同名文件夹: {candidate_path}")
            messagebox.showinfo("信息", f"不存在名为 {target_name} 的文件夹，请手动浏览。")

    def browse_test_dir(self):
        dir_path = filedialog.askdirectory(initialdir=TEST_DIR)
        if dir_path:
            self.predict_dir_var.set(dir_path)

    def start_prediction(self):
        test_dir = self.predict_dir_var.get()
        if not test_dir or not os.path.exists(test_dir):
            messagebox.showwarning("提示", "请先选择或浏览有效的测试文件夹路径！")
            return
            
        cls1_lbl = self.cls1_name_var.get()
        cls0_lbl = self.cls0_name_var.get()
        
        self.btn_predict.config(state="disabled")
        self.append_log("--- 启动盲测模块，即将批量预测 ---")
        
        worker = PredictWorker(test_dir, cls1_lbl, cls0_lbl, self.log_queue)
        worker.start()

    def check_queue(self):
        try:
            while True:
                msg_obj = self.log_queue.get_nowait()
                msg_type = msg_obj.get("type", "")
                msg_text = msg_obj.get("message", "")
                
                if msg_type in ["train_log", "predict_log"]:
                    self.append_log(msg_text)
                elif msg_type == "train_done":
                    self.append_log(msg_text)
                    self.btn_train.config(state="normal")
                    messagebox.showinfo("成功", "模型训练完成，请在日志中查看情况。")
                elif msg_type == "predict_done":
                    self.append_log(msg_text)
                    self.btn_predict.config(state="normal")
                elif msg_type == "error":
                    self.append_log("[错误] " + msg_text)
                    self.btn_train.config(state="normal")
                    self.btn_predict.config(state="normal")
        except queue.Empty:
            pass
        finally:
            self.after(200, self.check_queue)
