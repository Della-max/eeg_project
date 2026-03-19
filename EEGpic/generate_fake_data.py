import numpy as np
import matplotlib.pyplot as plt
import os
import matplotlib

matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

def generate_fake_eeg_data(n_channels=8, duration=60, sfreq=250, save_dir='fakenum'):
    """
    生成模拟EEG数据并保存到指定目录
    :param n_channels: 通道数
    :param duration: 时长（秒）
    :param sfreq: 采样频率
    :param save_dir: 保存目录
    :return: 生成的EEG数据和参数
    """
    # 创建保存目录（如果不存在）
    os.makedirs(save_dir, exist_ok=True)
    
    # 生成基础随机数据
    n_samples = int(duration * sfreq)
    eeg_data = np.random.randn(n_channels, n_samples)
    
    # 添加不同频段的活动
    time = np.arange(n_samples) / sfreq
    
    # 为每个通道添加不同的脑电活动模式
    for ch in range(n_channels):
        # Delta波（0.5-4Hz）- 深度睡眠
        delta_amp = 0.5 * (np.random.rand() + 0.5)
        delta_freq = 2 * np.random.rand() + 0.5
        eeg_data[ch] += delta_amp * np.sin(2 * np.pi * delta_freq * time)
        
        # Theta波（4-8Hz）- 困倦、冥想
        theta_amp = 0.3 * (np.random.rand() + 0.5)
        theta_freq = 3 * np.random.rand() + 5
        eeg_data[ch] += theta_amp * np.sin(2 * np.pi * theta_freq * time)
        
        # Alpha波（8-13Hz）- 放松但清醒
        alpha_amp = 0.4 * (np.random.rand() + 0.5)
        alpha_freq = 4 * np.random.rand() + 9
        eeg_data[ch] += alpha_amp * np.sin(2 * np.pi * alpha_freq * time)
        
        # Beta波（13-30Hz）- 清醒、专注
        beta_amp = 0.2 * (np.random.rand() + 0.5)
        beta_freq = 15 * np.random.rand() + 15
        eeg_data[ch] += beta_amp * np.sin(2 * np.pi * beta_freq * time)
    
    # 保存模拟数据
    data_path = os.path.join(save_dir, 'fake_eeg_data.npy')
    params_path = os.path.join(save_dir, 'fake_eeg_params.npy')
    
    params = {'sfreq': sfreq, 'n_channels': n_channels, 'duration': duration}
    np.save(data_path, eeg_data)
    np.save(params_path, params)
    
    # 绘制前两个通道的信号图
    plt.figure(figsize=(15, 6))
    plt.subplot(2, 1, 1)
    plt.plot(time, eeg_data[0])
    plt.title('通道 1 - 模拟EEG信号')
    plt.xlabel('时间 (秒)')
    plt.ylabel('振幅')
    
    plt.subplot(2, 1, 2)
    plt.plot(time, eeg_data[1])
    plt.title('通道 2 - 模拟EEG信号')
    plt.xlabel('时间 (秒)')
    plt.ylabel('振幅')
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'fake_eeg_plot.png'))
    plt.close()
    
    print(f"模拟EEG数据已成功生成并保存到 {save_dir} 文件夹")
    print(f"数据形状: {eeg_data.shape}")
    print(f"采样频率: {sfreq} Hz")
    print(f"时长: {duration} 秒")
    print(f"通道数: {n_channels}")
    
    return eeg_data, params

if __name__ == "__main__":
    generate_fake_eeg_data()