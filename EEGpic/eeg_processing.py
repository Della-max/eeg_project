import numpy as np
import mne
from scipy import signal
from scipy.integrate import trapezoid as trapz
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from hmmlearn import hmm
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
import matplotlib

# 设置Matplotlib支持中文显示
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']  # 设置中文字体
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class EEGProcessor:
    def __init__(self, sampling_freq=250, filter_params=None):
        """初始化EEG处理器"""
        self.sampling_freq = sampling_freq
        self.filter_params = filter_params or {
            'lowcut': 0.5,
            'highcut': 30.0,
            'order': 4
        }
        self.band_params = {
            'delta': (0.5, 4),
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30)
        }
         # 添加神经状态语义标签
        self.state_labels = {
            0: "注意维持困难",
            1: "相对平稳",
            2: "高唤醒/紧张",
            3: "放松/感官负荷低"
        }
        
    def plot_state_dynamics(self, state_sequence, time_axis=None):
        """绘制状态动态变化图"""
        plt.figure(figsize=(12, 4))
        if time_axis is None:
            time_axis = np.arange(len(state_sequence))
        
        plt.plot(time_axis, state_sequence, 'o-', markersize=3)
        plt.xlabel('时间')
        plt.ylabel('神经状态')
        plt.title('神经状态动态变化')
        plt.yticks(np.unique(state_sequence))
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('neural_state_dynamics.png')
        plt.show()
    
    def animate_state_dynamics(self, state_sequence, time_per_window=2.0, fps=1):
        """
        动态绘制状态动态变化图，时间轴逐渐增加，按q键暂停
        :param state_sequence: 状态序列
        :param time_per_window: 每个时间窗口的时长（秒）
        :param fps: 动画帧率（帧/秒）
        """
        # 计算总时间
        total_time = len(state_sequence) * time_per_window
        time_axis = np.arange(0, total_time, time_per_window)
        
        # 创建图形和轴
        fig, ax = plt.subplots(figsize=(12, 4))
        line, = ax.plot([], [], 'o-', markersize=3)
        
        # 设置图形属性
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('神经状态')
        ax.set_title('神经状态动态变化 - 动态更新')
        ax.set_yticks(np.unique(state_sequence))
        ax.grid(True)
        
        # 获取y轴的最小值和最大值，设置固定的y轴范围
        y_min = np.min(state_sequence) - 0.5
        y_max = np.max(state_sequence) + 0.5
        ax.set_ylim(y_min, y_max)
        
        # 初始化函数
        def init():
            line.set_data([], [])
            return line,
        
        # 更新函数
        def update(frame):
            if frame >= len(state_sequence):
                frame = len(state_sequence) - 1
            
            # 更新数据
            current_time = time_axis[:frame+1]
            current_states = state_sequence[:frame+1]
            
            line.set_data(current_time, current_states)
            
            # 动态更新x轴范围
            if frame > 0:
                ax.set_xlim(0, current_time[-1] + 2 * time_per_window)
            
            return line,
        
        # 创建动画
        ani = animation.FuncAnimation(
            fig, update, frames=len(state_sequence), init_func=init,
            interval=1000/fps, blit=True, repeat=False
        )
        
        # 按键事件处理函数
        def on_key_press(event):
            if event.key == 'q':
                ani.event_source.stop()
                print("动画已暂停")
        
        # 绑定按键事件
        fig.canvas.mpl_connect('key_press_event', on_key_press)
        
        plt.tight_layout()
        plt.show()
    
    def plot_state_intervals(self, state_sequence, time_per_window=2.0, save_path='state_intervals.png'):
        """
        使用阶梯图/条带图可视化神经状态区间，并计算状态统计信息
        :param state_sequence: 状态序列
        :param time_per_window: 每个时间窗口的时长（秒）
        :param save_path: 保存路径
        """
        # 计算时间轴
        n_windows = len(state_sequence)
        total_time = n_windows * time_per_window
        time_axis = np.arange(0, total_time, time_per_window)
        
        # 生成阶梯图数据
        step_x = []
        step_y = []
        
        for i in range(n_windows):
            # 当前窗口的开始和结束时间
            start_time = time_axis[i]
            end_time = time_axis[i] + time_per_window
            
            step_x.extend([start_time, end_time])
            step_y.extend([state_sequence[i], state_sequence[i]])
        
        # 计算状态统计信息
        unique_states, counts = np.unique(state_sequence, return_counts=True)
        state_durations = counts * time_per_window  # 每个状态的总持续时间（秒）
        total_duration = np.sum(state_durations)
        
        # 计算状态占比
        state_percentages = (state_durations / total_duration) * 100
        
        # 计算平均持续时间
        state_avg_durations = {}
        for state in unique_states:
            # 找到所有连续的状态区间
            transitions = np.where(np.diff(np.concatenate(([-1], state_sequence, [-1]))) != 0)[0]
            state_intervals = np.diff(transitions)[np.where(state_sequence[transitions[:-1]] == state)]
            if len(state_intervals) > 0:
                state_avg_durations[state] = np.mean(state_intervals) * time_per_window
            else:
                state_avg_durations[state] = 0
        
        # 绘制阶梯图
        plt.figure(figsize=(15, 8))
        
        # 主阶梯图
        plt.subplot(2, 1, 1)
        plt.step(step_x, step_y, where='post', linewidth=3)
        
        # 设置Y轴标签为语义标签
        y_ticks = sorted(unique_states)
        y_labels = [self.state_labels[state] for state in y_ticks]
        plt.yticks(y_ticks, y_labels)
        
        plt.xlabel('时间 (秒)')
        plt.ylabel('神经状态')
        plt.title('神经状态区间动态变化')
        plt.grid(True, alpha=0.3)
        
        # 统计信息子图
        plt.subplot(2, 1, 2)
        bar_width = 0.35
        index = np.arange(len(unique_states))
        
        # 绘制状态占比
        bars1 = plt.bar(index, state_percentages, bar_width, label='状态占比 (%)')
        
        # 绘制平均持续时间
        bars2 = plt.bar(index + bar_width, [state_avg_durations[state] for state in unique_states], 
                       bar_width, label='平均持续时间 (秒)')
        
        # 设置X轴标签为语义标签
        plt.xticks(index + bar_width/2, y_labels, rotation=0)
        
        plt.ylabel('数值')
        plt.title('神经状态统计信息')
        plt.legend()
        
        # 在柱状图上添加数值标签
        for bar in bars1:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{height:.1f}%', ha='center', va='bottom')
        
        for bar in bars2:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.2f}s', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.show()
        
        # 打印详细统计信息
        print("\n=== 神经状态统计信息 ===")
        print(f"总时长: {total_duration:.1f} 秒")
        print(f"时间窗口时长: {time_per_window:.1f} 秒")
        print(f"总窗口数: {n_windows}")
        print("\n各状态统计:")
        print("状态编号 | 状态标签 | 持续时间(秒) | 占比(%) | 平均持续时间(秒)")
        print("-" * 65)
        for state in unique_states:
            duration = state_durations[list(unique_states).index(state)]
            percentage = state_percentages[list(unique_states).index(state)]
            avg_duration = state_avg_durations[state]
            print(f"   S{state}   | {self.state_labels[state]:10} | {duration:12.1f} | {percentage:6.1f} | {avg_duration:14.2f}")
        print("-" * 65)   
        
    def filter_signal(self, eeg_data):
        """对EEG信号进行带通滤波"""
        nyquist = 0.5 * self.sampling_freq
        low = self.filter_params['lowcut'] / nyquist
        high = self.filter_params['highcut'] / nyquist
        b, a = signal.butter(self.filter_params['order'], [low, high], btype='band')
        return signal.filtfilt(b, a, eeg_data, axis=1)
    
    def resample_signal(self, eeg_data, new_sfreq):
        """对EEG信号进行重采样"""
        n_samples_new = int(eeg_data.shape[1] * new_sfreq / self.sampling_freq)
        resampled_data = signal.resample(eeg_data, n_samples_new, axis=1)
        self.sampling_freq = new_sfreq
        return resampled_data
    
    def remove_artifacts(self, eeg_data, method='zscore', threshold=3):
        """去除EEG信号中的伪迹"""
        if method == 'zscore':
            z_scores = np.abs((eeg_data - np.mean(eeg_data, axis=1, keepdims=True)) / 
                             np.std(eeg_data, axis=1, keepdims=True))
            eeg_data[z_scores > threshold] = np.nan
            for ch in range(eeg_data.shape[0]):
                mask = np.isnan(eeg_data[ch])
                if np.any(mask):
                    x = np.arange(eeg_data.shape[1])
                    eeg_data[ch, mask] = np.interp(x[mask], x[~mask], eeg_data[ch, ~mask])
        return eeg_data
    
    def segment_data(self, eeg_data, window_length=2, overlap=0.5):
        """将EEG数据分成多个时间窗口"""
        window_samples = int(window_length * self.sampling_freq)
        step_samples = int(window_samples * (1 - overlap))
        n_windows = int((eeg_data.shape[1] - window_samples) / step_samples) + 1
        
        segmented_data = []
        for i in range(n_windows):
            start = i * step_samples
            end = start + window_samples
            if end <= eeg_data.shape[1]:
                segmented_data.append(eeg_data[:, start:end])
        
        return np.array(segmented_data)
    
    def extract_band_power(self, eeg_data):
        """提取EEG信号的各频段功率"""
        n_windows, n_channels, n_samples = eeg_data.shape
        freqs, psd = signal.welch(eeg_data, self.sampling_freq, nperseg=n_samples, axis=2)
        
        features = []
        for window in range(n_windows):
            window_features = []
            for ch in range(n_channels):
                for band, (low, high) in self.band_params.items():
                    idx_band = np.logical_and(freqs >= low, freqs <= high)
                    band_power = trapz(psd[window, ch, idx_band], freqs[idx_band])
                    window_features.append(band_power)
            features.append(window_features)
        
        return np.array(features)
    
    def extract_ratio_features(self, band_power_features):
        """提取频段功率比值特征（如θ/β）"""
        n_windows, n_features = band_power_features.shape
        n_channels = n_features // len(self.band_params)
        
        ratio_features = []
        for window in range(n_windows):
            window_ratios = []
            for ch in range(n_channels):
                delta = band_power_features[window, ch * 4]
                theta = band_power_features[window, ch * 4 + 1]
                alpha = band_power_features[window, ch * 4 + 2]
                beta = band_power_features[window, ch * 4 + 3]
                
                theta_beta = theta / beta if beta != 0 else 0
                theta_alpha = theta / alpha if alpha != 0 else 0
                alpha_beta = alpha / beta if beta != 0 else 0
                
                window_ratios.extend([theta_beta, theta_alpha, alpha_beta])
            
            ratio_features.append(window_ratios)
        
        return np.hstack([band_power_features, np.array(ratio_features)])
    
    def dimensionality_reduction(self, features, n_components=10):
        """使用PCA对特征进行降维"""
        pca = PCA(n_components=n_components)
        reduced_features = pca.fit_transform(features)
        return reduced_features, pca
    
    def cluster_states(self, features, n_clusters=4):
        """使用K-means进行无监督聚类"""
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(features)
        return clusters, kmeans
    
    def hmm_modeling(self, features, n_states=4):
        """使用隐马尔可夫模型对特征序列建模"""
        model = hmm.GaussianHMM(n_components=n_states, covariance_type="diag", n_iter=1000, random_state=42)
        model.fit(features)
        state_sequence = model.predict(features)
        return model, state_sequence
    
    
    def realtime_eeg_display(self, eeg_data, channel_names=None, window_size=2.0, fps=30):
        """
        实时显示EEG数据
        :param eeg_data: EEG数据，形状为(n_channels, n_samples)
        :param channel_names: 通道名称列表，如果为None则使用默认名称
        :param window_size: 显示窗口大小（秒）
        :param fps: 帧率（帧/秒）
        """
        n_channels, n_samples = eeg_data.shape
        
        # 如果没有提供通道名称，使用默认名称
        if channel_names is None:
            channel_names = [f'Channel {i+1}' for i in range(n_channels)]
        
        # 计算窗口大小对应的样本数
        window_samples = int(window_size * self.sampling_freq)
        
        # 创建图形和子图
        fig, axes = plt.subplots(n_channels, 1, figsize=(12, 2 * n_channels), sharex=True)
        if n_channels == 1:
            axes = [axes]  # 确保axes是列表
        
        # 初始化线条
        lines = []
        time_axis = np.arange(window_samples) / self.sampling_freq
        
        for i, ax in enumerate(axes):
            line, = ax.plot(time_axis, np.zeros(window_samples))
            lines.append(line)
            ax.set_ylabel(channel_names[i])
            ax.grid(True, alpha=0.3)
        
        axes[-1].set_xlabel('时间 (秒)')
        fig.suptitle('实时EEG数据显示', fontsize=12)
        fig.tight_layout()
        
        # 初始化函数
        def init():
            for line in lines:
                line.set_data([], [])
            return lines
        
        # 更新函数
        def update(frame):
            # 计算当前窗口的起始和结束位置
            start = frame * int(self.sampling_freq / fps)
            end = start + window_samples
            
            # 确保不超出数据范围
            if end > n_samples:
                end = n_samples
                start = max(0, end - window_samples)
            
            # 更新时间轴
            current_time = np.arange(start, end) / self.sampling_freq - start / self.sampling_freq
            
            # 更新每个通道的数据
            for i, line in enumerate(lines):
                if end > start:
                    line.set_data(current_time, eeg_data[i, start:end])
                    # 自动调整y轴范围
                    axes[i].set_ylim(eeg_data[i, start:end].min() - 0.1, eeg_data[i, start:end].max() + 0.1)
            
            return lines
        
        # 创建动画
        ani = animation.FuncAnimation(
            fig, update, frames=int(n_samples * fps / self.sampling_freq), 
            init_func=init, interval=1000/fps, blit=True
        )
        
        # 按键事件处理函数
        def on_key_press(event):
            if event.key == 'q':
                plt.close(fig)
                print("实时显示已关闭")
        
        # 绑定按键事件
        fig.canvas.mpl_connect('key_press_event', on_key_press)
        
        plt.show()

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
    
    print(f"模拟EEG数据已生成并保存到 {save_dir} 文件夹")
    print(f"数据形状: {eeg_data.shape}")
    print(f"采样频率: {sfreq} Hz")
    print(f"时长: {duration} 秒")
    print(f"通道数: {n_channels}")
    
    return eeg_data, params

def load_fake_eeg_data(save_dir='fakenum'):
    """
    加载保存的模拟EEG数据
    :param save_dir: 保存目录
    :return: EEG数据和参数
    """
    eeg_data = np.load(os.path.join(save_dir, 'fake_eeg_data.npy'))
    params = np.load(os.path.join(save_dir, 'fake_eeg_params.npy'), allow_pickle=True).item()
    return eeg_data, params

def save_features_to_undo(features, reduced_features, pca_model, save_dir='undo_fakenum'):
    """
    将特征值和降维后的数据保存到undo_fakenum文件夹
    :param features: 原始特征
    :param reduced_features: 降维后的数据
    :param pca_model: PCA模型
    :param save_dir: 保存目录
    """
    # 创建保存目录（如果不存在）
    os.makedirs(save_dir, exist_ok=True)
    
    # 保存特征数据
    np.save(os.path.join(save_dir, 'original_features.npy'), features)
    np.save(os.path.join(save_dir, 'reduced_features.npy'), reduced_features)
    
    # 保存PCA模型参数
    pca_params = {
        'components_': pca_model.components_,
        'explained_variance_': pca_model.explained_variance_,
        'explained_variance_ratio_': pca_model.explained_variance_ratio_,
        'mean_': pca_model.mean_,
        'n_components_': pca_model.n_components_
    }
    np.save(os.path.join(save_dir, 'pca_params.npy'), pca_params)
    
    print(f"\n特征数据已保存到 {save_dir} 文件夹")
    print(f"原始特征形状: {features.shape}")
    print(f"降维后特征形状: {reduced_features.shape}")
    print(f"PCA模型参数已保存")

def main():
    """主函数示例"""
    # 1. 生成模拟数据
    eeg_data, params = generate_fake_eeg_data(n_channels=8, duration=60, sfreq=250)
    
    # 2. 创建EEG处理器实例
    processor = EEGProcessor(sampling_freq=params['sfreq'])
    
    # 3. 处理EEG数据
    filtered_data = processor.filter_signal(eeg_data)
    cleaned_data = processor.remove_artifacts(filtered_data)
    segmented_data = processor.segment_data(cleaned_data, window_length=2, overlap=0.5)
    
    # 4. 特征提取
    band_power = processor.extract_band_power(segmented_data)
    features = processor.extract_ratio_features(band_power)
    
    # 5. 降维
    reduced_features, pca_model = processor.dimensionality_reduction(features, n_components=10)
    
    # 6. 保存特征数据到undo_fakenum
    save_features_to_undo(features, reduced_features, pca_model, save_dir='undo_fakenum')
    
    # 7. 无监督聚类
    clusters, kmeans_model = processor.cluster_states(reduced_features, n_clusters=4)
    
    # 8. HMM建模
    hmm_model, state_sequence = processor.hmm_modeling(reduced_features, n_states=4)
    
    # 9. 动态可视化结果（删除了静态图）
    print("\n正在播放动态图表... 按q键暂停")
    processor.animate_state_dynamics(state_sequence, time_per_window=2.0, fps=1)
    
    # 10. 绘制状态区间图
    processor.plot_state_intervals(state_sequence, time_per_window=2.0)
    
    print("\n正在显示实时EEG数据... 按q键关闭")
    channel_names = [f'Channel {i+1}' for i in range(params['n_channels'])]
    processor.realtime_eeg_display(cleaned_data, channel_names=channel_names, window_size=2.0, fps=30)
    # 打印结果信息
    print(f"\n分窗后数据形状: {segmented_data.shape}")
    print(f"提取的特征数量: {features.shape[1]}")
    print(f"降维后的特征数量: {reduced_features.shape[1]}")
    print(f"检测到的神经状态数量: {len(np.unique(state_sequence))}")

if __name__ == "__main__":
    main()