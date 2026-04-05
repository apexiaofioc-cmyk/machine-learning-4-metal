import librosa
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import cosine

def check_system_steady_state(file_path, window_sec=1.0, sr=44100):
    """
    通过分段对比分析信号是否达到稳态
    :param window_sec: 分段检查的时间窗口（建议与你之后的训练窗长一致）
    """
    # 1. 加载音频
    y, _ = librosa.load(file_path, sr=sr)
    duration = librosa.get_duration(y=y, sr=sr)
    
    # 将音频切分为固定长度的片段
    samples_per_window = int(window_sec * sr)
    num_windows = int(len(y) / samples_per_window)
    
    psds = []      # 存储每段的功率谱
    rms_values = [] # 存储每段的有效值（能量）

    for i in range(num_windows):
        start = i * samples_per_window
        end = start + samples_per_window
        chunk = y[start:end]
        
        # 计算该段的 RMS 能量
        rms = np.sqrt(np.mean(chunk**2))
        rms_values.append(rms)
        
        # 计算该段的功率谱密度 (PSD)
        # 使用线性频率，关注频率能量分布
        stft = np.abs(librosa.stft(chunk, n_fft=2048))
        psd = np.mean(stft, axis=1)
        psds.append(psd)

    # 2. 计算稳定性指标
    # 计算相邻片段频谱的余弦相似度 (Cosine Similarity)
    # 1.0 表示完全一致，越接近 1 说明频谱特征越稳定
    similarities = []
    for i in range(len(psds) - 1):
        sim = 1 - cosine(psds[i], psds[i+1])
        similarities.append(sim)

    # 3. 可视化诊断图
    plt.figure(figsize=(15, 10))

    # 子图 1: 能量稳定性 (RMS Trend)
    plt.subplot(2, 1, 1)
    plt.plot(np.arange(num_windows) * window_sec, rms_values, marker='o', color='b')
    plt.title("Energy Stability (RMS per Window)")
    plt.xlabel("Time (s)")
    plt.ylabel("RMS Amplitude")
    plt.grid(True, alpha=0.3)

    # 子图 2: 频谱一致性 (Spectral Similarity)
    plt.subplot(2, 1, 2)
    plt.plot(np.arange(len(similarities)) * window_sec + window_sec, similarities, marker='s', color='r')
    plt.axhline(y=0.95, color='g', linestyle='--', label='High Stability Threshold (0.95)')
    plt.title("Spectral Similarity between Adjacent Windows")
    plt.xlabel("Time (s)")
    plt.ylabel("Cosine Similarity")
    plt.ylim(0.8, 1.05)
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

    # 4. 给出最终结论
    avg_sim = np.mean(similarities[-5:]) # 取最后 5 秒的平均稳定性
    std_rms = np.std(rms_values) / np.mean(rms_values) # 能量波动率
    
    print(f"--- 系统稳态诊断报告 ---")
    print(f"总时长: {duration:.2f} 秒")
    print(f"末期平均频谱相似度: {avg_sim:.42f}")
    print(f"总体能量波动率 (CV): {std_rms:.2%}")
    
    if avg_sim > 0.95 and std_rms < 0.1:
        print("结论：系统已进入稳态，当前录制时间合适。")
    else:
        print("结论：信号仍在波动或噪声过大，建议增加录制时长或检查电机转速稳定性。")

# 使用示例
check_system_steady_state(r'D:\fdurop\machinelearning\machine-learning-4-metal\data_origin\Alball\L0_Alball_v=1.5_n=10_180355.wav')