import os
import json
import random
from pathlib import Path
import numpy

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# 获取当前 config.py 所在的绝对目录 (项目根目录)
BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "settings.json"

# 提供一个默认的 fallback，以防 JSON 文件不存在或被误删
_DEFAULT_CONFIG = {
    "origin_data_dir": "data_origin",
    "train_data_dir": "data_train",
    "test_dir": "data_test",
    "model_save_dir": "model",
    "model_name": "metal_classifier.keras",
    "gather_data_dir": "data_origin",
    "batch_size": 32,
    "epochs": 50,
    "learning_rate": 0.001,
    "steel_label": 1,
    "alumi_label": 0,
    "random_state": False,
    "sr": 44100,
    "duration": 0.5,
    "overlap": 0.5,
    "n_fft": 2048,
    "hop_length": 1024,
    "naming_prefix_alumi": "Alball",
    "naming_prefix_steel": "Stball",
    "include_timestamp": True,
    "include_speed": True,
    "include_ball_count": True
}

# 1. 自动读取并应用
_current_config = _DEFAULT_CONFIG.copy()
if SETTINGS_FILE.exists():
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            _loaded = json.load(f)
            _current_config.update(_loaded)
    except Exception as e:
        print(f"Warning: 读取 {SETTINGS_FILE} 失败，使用默认配置。({e})")

# 2. 导出所有参数供其他模块使用 (与原变量名一致)
# -- 音频参数 --
SR = _current_config["sr"]
DURATION = _current_config["duration"]
OVERLAP = _current_config["overlap"]
N_FFT = _current_config["n_fft"]
HOP_LENGTH = _current_config["hop_length"]

# -- 训练参数 --
BATCH_SIZE = _current_config["batch_size"]
EPOCHS = _current_config["epochs"]
LEARNING_RATE = _current_config["learning_rate"]
steel_lable = _current_config["steel_label"] # 注意原拼写是 lable，为了兼容其他文件暂时保留
alumi_lable = _current_config["alumi_label"]
random_state = _current_config["random_state"]

# -- UI与命名参数 --
NAMING_PREFIX_ALUMI = _current_config["naming_prefix_alumi"]
NAMING_PREFIX_STEEL = _current_config["naming_prefix_steel"]
INCLUDE_TIMESTAMP = _current_config.get("include_timestamp", True)
INCLUDE_SPEED = _current_config.get("include_speed", True)
INCLUDE_BALL_COUNT = _current_config.get("include_ball_count", True)

# -- 路径配置 (使用 pathlib 拼接路径) --
# 为了支持绝对路径和相对路径，我们进行简单判断
def _resolve_path(path_str):
    p = Path(path_str)
    if p.is_absolute():
        return p
    return BASE_DIR / p

ORIGIN_DATA_DIR = _resolve_path(_current_config["origin_data_dir"])
TRAIN_DATA_DIR = _resolve_path(_current_config["train_data_dir"])
TEST_DIR = _resolve_path(_current_config["test_dir"])
MODEL_SAVE_DIR = _resolve_path(_current_config["model_save_dir"])
MODEL_NAME = _current_config["model_name"]
GATHER_DATA_DIR = _resolve_path(_current_config["gather_data_dir"])


def set_seed_42(rs_flag, seed=42):
    """
    设定随机数种子为42
    """
    if (rs_flag == False):
        import keras
        random.seed(seed)
        numpy.random.seed(seed)               # NumPy
        keras.utils.set_random_seed(seed)     # Keras
        print("0.已固定随机数种子为42")
    else:
        print("0.随机数种子未固定")

def init_project_dirs():
    """
    初始化项目所需的文件夹
    """
    ORIGIN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    # GATHER_DATA_DIR, TRAIN_DATA_DIR 等如果需要也可以一起创建
    TRAIN_DATA_DIR.mkdir(parents=True, exist_ok=True)
    GATHER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("项目目录初始化完成。")

if __name__ == "__main__":
    init_project_dirs()