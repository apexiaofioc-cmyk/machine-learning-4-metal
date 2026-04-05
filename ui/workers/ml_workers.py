import os
os.environ["KERAS_BACKEND"] = "tensorflow"
os.environ['WANDB_API_KEY'] = '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'

import threading
import queue
import numpy as np
from pathlib import Path
import keras
import wandb
from wandb.integration.keras import WandbMetricsLogger

import config as cfg
from data_utils import build_dataset
from model import build_cnn_model
from predict import load_system, predict_audio

class UILoggerCallback(keras.callbacks.Callback):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        acc = logs.get('accuracy', 0)
        val_acc = logs.get('val_accuracy', 0)
        loss = logs.get('loss', 0)
        val_loss = logs.get('val_loss', 0)
        
        msg = f"Epoch {epoch+1:02d} | loss: {loss:.4f} - acc: {acc:.4f} | val_loss: {val_loss:.4f} - val_acc: {val_acc:.4f}"
        self.log_queue.put({"type": "train_log", "message": msg})

class TrainWorker(threading.Thread):
    def __init__(self, folder1_path, folder0_path, log_queue):
        super().__init__(daemon=True)
        self.folder1_path = Path(folder1_path)
        self.folder0_path = Path(folder0_path)
        self.log_queue = log_queue

    def run(self):
        try:
            self.log_queue.put({"type": "train_log", "message": "1. 开始提取和预处理数据..."})
            X_train, y_train, X_test, y_test = build_dataset(self.folder1_path, self.folder0_path)
            
            if len(X_train) == 0:
                self.log_queue.put({"type": "error", "message": "未能加载数据，请检查所选文件夹是否包含 .wav 文件"})
                return

            self.log_queue.put({"type": "train_log", "message": f"真实生成的 X_train 形状: {X_train.shape}"})
            
            # 保存到 npy (兼容原有代码流程)
            save_dir = cfg.TRAIN_DATA_DIR
            Path.mkdir(save_dir, exist_ok=True)
            np.save(Path(save_dir/ "X_train.npy"), X_train)
            np.save(Path(save_dir/ "Y_train.npy"), y_train)
            np.save(Path(save_dir/ "X_test.npy"), X_test)
            np.save(Path(save_dir/ "Y_test.npy"), y_test)
            
            self.log_queue.put({"type": "train_log", "message": "2. 正在进行标准化..."})
            mean_val = np.mean(X_train)
            std_val = np.std(X_train)
            
            X_train_norm = (X_train - mean_val) / (std_val + 1e-7)
            X_test_norm = (X_test - mean_val) / (std_val + 1e-7)
        
            X_train_norm = X_train_norm.astype(np.float32)
            X_test_norm = X_test_norm.astype(np.float32)
            y_train = y_train.astype(np.float32)
            y_test = y_test.astype(np.float32)
            
            self.log_queue.put({"type": "train_log", "message": "3. 初始化Wandb并构建模型..."})
            
            # Wandb
            wandb.init(project="Machine Learning for metal", config={
                "learning_rate": cfg.LEARNING_RATE,
                "epochs": cfg.EPOCHS,
                "batch_size": cfg.BATCH_SIZE
            })
            
            input_shape = X_train_norm.shape[1:] 
            model = build_cnn_model(input_shape)
            
            model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=cfg.LEARNING_RATE), 
                loss='binary_crossentropy', 
                metrics=['accuracy']
            )
            
            self.log_queue.put({"type": "train_log", "message": "4. 开始训练(等待 Epoch 日志)..."})
            
            early_stopping = keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
            reduce_lr = keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6)
            ui_logger = UILoggerCallback(self.log_queue)
            wandb_callbacks = WandbMetricsLogger()

            history = model.fit(
                X_train_norm, y_train,
                epochs=cfg.EPOCHS, 
                batch_size=cfg.BATCH_SIZE,
                shuffle=True, 
                validation_data=(X_test_norm, y_test),
                callbacks=[early_stopping, reduce_lr, wandb_callbacks, ui_logger],
                verbose=0 
            )
            
            self.log_queue.put({"type": "train_log", "message": "5. 保存模型与标准化参数..."})
            Path.mkdir(cfg.MODEL_SAVE_DIR, exist_ok=True)
            model_path = Path(cfg.MODEL_SAVE_DIR/"metal_classifier.keras")
            model.save(model_path)
            
            np.save(Path(cfg.MODEL_SAVE_DIR/ "mean_val.npy"), mean_val)
            np.save(Path(cfg.MODEL_SAVE_DIR/ "std_val.npy"), std_val)
            
            wandb.finish()
            
            self.log_queue.put({"type": "train_done", "message": f"✅训练完成！资产已保存至: {cfg.MODEL_SAVE_DIR}"})
            
        except Exception as e:
            self.log_queue.put({"type": "error", "message": f"训练线程出错: {str(e)}"})

class PredictWorker(threading.Thread):
    def __init__(self, test_folder, label1_name, label0_name, log_queue):
        super().__init__(daemon=True)
        self.test_folder = Path(test_folder)
        self.label1_name = label1_name
        self.label0_name = label0_name
        self.log_queue = log_queue

    def run(self):
        try:
            self.log_queue.put({"type": "predict_log", "message": "正在加载预测模型..."})
            model, mean_val, std_val = load_system()
            
            wav_files = list(self.test_folder.rglob("*.wav"))
            if not wav_files:
                self.log_queue.put({"type": "predict_log", "message": f"文件夹 {self.test_folder.name} 是空的，请放入 .wav 文件"})
                self.log_queue.put({"type": "predict_done", "message": "盲测结束。"})
                return
            
            self.log_queue.put({"type": "predict_log", "message": f"找到 {len(wav_files)} 个音频文件，开始盲测..."})
            
            for wav in wav_files:
                final_prob = predict_audio(wav, model, mean_val, std_val)
                if final_prob is None:
                    self.log_queue.put({"type": "predict_log", "message": f"文件: {wav.name} 处理失败（可能切片过少或含静音）"})
                    continue
                
                if final_prob > 0.5:
                    result_label = self.label1_name
                    confidence = final_prob * 100
                else:
                    result_label = self.label0_name
                    confidence = (1 - final_prob) * 100
                
                self.log_queue.put({"type": "predict_log", "message": f"[{result_label}] ({confidence:.2f}%) : {wav.name}"})
            
            self.log_queue.put({"type": "predict_done", "message": "所有文件预测完毕！"})
            
        except FileNotFoundError as e:
            self.log_queue.put({"type": "error", "message": f"未找到模型: {str(e)}。请先完成训练。"})
        except Exception as e:
            self.log_queue.put({"type": "error", "message": f"盲测出错: {str(e)}"})
