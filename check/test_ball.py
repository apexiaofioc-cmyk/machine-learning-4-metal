import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import os

def analyze_multiple_folders(file_paths, sr=44100, n_fft=2048):
    """
    分析并展示多段不同路径音频的物理特征
    :param file_paths: 包含 5 个文件完整路径的列表
    """
    n = len(file_paths)
    # 动态调整画布高度，5个文件建议高度设为 25
    plt.figure(figsize=(20, 4 * n)) 
    
    for i, path in enumerate(file_paths):
        # 提取文件夹名和文件名，方便在图中标识
        folder_name = os.path.basename(os.path.dirname(path))
        file_name = os.path.basename(path)
        label = f"[{folder_name}] {file_name}"

        # 1. 加载并归一化
        y, _ = librosa.load(path, sr=sr)
        y = librosa.util.normalize(y)
        
        # --- 子图 1: 波形图 ---
        plt.subplot(n, 3, i * 3 + 1)
        librosa.display.waveshow(y, sr=sr, alpha=0.6, color='blue')
        plt.title(f"Wave: {label}", fontsize=10)
        plt.ylabel("Amp")

        # --- 子图 2: STFT (线性频率) ---
        plt.subplot(n, 3, i * 3 + 2)
        D = librosa.stft(y, n_fft=n_fft)
        S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
        # 注意：这里固定 y 轴到 20kHz，方便肉眼横向对比不同材质的高频峰
        librosa.display.specshow(S_db, sr=sr, n_fft=n_fft, x_axis='time', y_axis='linear')
        plt.ylim(0, 20000) 
        plt.title("STFT (0-20kHz)", fontsize=10)

        # --- 子图 3: Mel-Spectrogram ---
        plt.subplot(n, 3, i * 3 + 3)
        M = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, n_fft=n_fft)
        M_db = librosa.power_to_db(M, ref=np.max)
        librosa.display.specshow(M_db, sr=sr, x_axis='time', y_axis='mel')
        plt.title("Mel Scale", fontsize=10)

    plt.tight_layout()
    plt.show()

# --- 实验配置：在此处输入你的 5 个文件路径 ---
# 你可以随意组合不同文件夹下的 WAV 文件
my_files = [
    r'D:\fdurop\machinelearning\machine-learning-4-metal\check\304ball\L0_304ball_v=1.5_n=10_191415.wav',
    r'D:\fdurop\machinelearning\machine-learning-4-metal\check\420ball\L0_420ball_v=1.5_n=10_191603.wav',
    r'D:\fdurop\machinelearning\machine-learning-4-metal\check\alball\L0_alball_v=1.5_n=10_192245.wav',
    r'D:\fdurop\machinelearning\machine-learning-4-metal\check\carbon_steel\L0_carbon_steel_v=1.5_n=10_192053.wav',
    r'D:\fdurop\machinelearning\machine-learning-4-metal\check\GCR15\L0_GCR15_v=1.5_n=10_191748.wav'
]

# 调用分析
analyze_multiple_folders(my_files)