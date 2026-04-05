import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

def plot_spectrograms(audio_path):
    # 1. 加载音频文件
    # sr=None 保持原始采样率
    y, sr = librosa.load(audio_path, sr=None)
    
    plt.figure(figsize=(12, 10))

    # --- 绘制普通频谱图 (STFT) ---
    # 使用短时傅里叶变换
    D = librosa.stft(y)
    # 将振幅转为分贝单位 (dB)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    
    plt.subplot(2, 1, 1)
    librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='hz')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Linear-frequency Power Spectrogram')

    # --- 绘制梅尔频谱图 (Mel Spectrogram) ---
    # n_mels 是梅尔滤波器的数量，通常设为 128
    S_mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    # 同样转为 dB 单位
    S_mel_db = librosa.power_to_db(S_mel, ref=np.max)
    
    plt.subplot(2, 1, 2)
    librosa.display.specshow(S_mel_db, sr=sr, x_axis='time', y_axis='mel')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Mel Spectrogram')

    plt.tight_layout()
    plt.show()

plot_spectrograms(r'D:\fdurop\machinelearning\machine-learning-4-metal\data_origin\Alball\L0_Alball_v=1.5_n=10_180355.wav')