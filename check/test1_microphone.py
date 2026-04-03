import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt

def record_and_verify(duration=10, sr=44100, filename="mic_test.wav"):
    """
    录制原始音频并分析降噪特征
    """
    print(f"--- 实验开始：请保持前3秒安静，第4秒制造一个短促响声 ---")
    
    # 1. 录音 (使用 float32 保证动态范围不被压缩)
    # sd.rec 是非阻塞的，我们用 sd.wait() 等待结束
    recording = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='float32')
    sd.wait() 
    print("--- 录音结束，正在生成物理诊断报告 ---")

    # 2. 保存为原始 WAV 文件 (无损)
    wavfile.write(filename, sr, recording)

    # 3. 数据提取与分析
    audio_data = recording.flatten()
    time_axis = np.linspace(0, duration, len(audio_data))

    # 创建诊断图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # --- 诊断 A: 时域对数包络 (检查 Noise Gate/静音切断) ---
    # 对数坐标能放大微弱底噪，如果底噪是一条完美的水平线，说明有硬件降噪
    eps = 1e-10 # 防止 log(0)
    ax1.plot(time_axis, 20 * np.log10(np.abs(audio_data) + eps))
    ax1.set_title("Time Domain: Logarithmic Amplitude (dB FS)")
    ax1.set_ylabel("Amplitude (dB)")
    ax1.set_xlabel("Time (s)")
    ax1.grid(True, which='both', alpha=0.3)
    ax1.set_ylim([-100, 0]) # 观察 -100dB 到 0dB 的范围

    # --- 诊断 B: 能量分布密度 (检查 频率空洞/滤波) ---
    ax2.specgram(audio_data, Fs=sr, NFFT=1024, noverlap=512, cmap='magma')
    ax2.set_title("Frequency Domain: Spectrogram (Power Density)")
    ax2.set_ylabel("Frequency (Hz)")
    ax2.set_xlabel("Time (s)")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # 运行实验
    record_and_verify()