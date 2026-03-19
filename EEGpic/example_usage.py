"""
EEG信号处理系统使用示例
"""
import numpy as np
from eeg_processing import EEGProcessor, generate_fake_eeg_data, load_fake_eeg_data, save_features_to_undo

def main():
    """主函数"""
    print("=== EEG信号处理系统示例 ===")
    
    # 1. 生成模拟数据
    print("\n1. 生成模拟EEG数据...")
    eeg_data, params = generate_fake_eeg_data(n_channels=8, duration=60, sfreq=250)
    
    # 2. 创建EEG处理器实例
    print("\n2. 创建EEG处理器实例...")
    processor = EEGProcessor(sampling_freq=params['sfreq'])
    
    # 3. 预处理数据
    print("\n3. 预处理数据...")
    filtered_data = processor.filter_signal(eeg_data)
    print("   - 滤波完成")
    
    cleaned_data = processor.remove_artifacts(filtered_data)
    print("   - 伪迹去除完成")
    
    segmented_data = processor.segment_data(cleaned_data, window_length=2, overlap=0.5)
    print("   - 时间分窗完成")
    print(f"   - 分窗后形状: {segmented_data.shape}")
    
    # 4. 特征提取
    print("\n4. 特征提取...")
    band_power = processor.extract_band_power(segmented_data)
    features = processor.extract_ratio_features(band_power)
    print(f"   - 提取特征数量: {features.shape[1]}")
    
    # 5. 降维
    print("\n5. 特征降维...")
    reduced_features, pca_model = processor.dimensionality_reduction(features, n_components=10)
    print(f"   - 降维后特征数量: {reduced_features.shape[1]}")
    
    # 6. 保存特征到undo_fakenum文件夹
    print("\n6. 保存特征数据到undo_fakenum文件夹...")
    save_features_to_undo(features, reduced_features, pca_model, save_dir='undo_fakenum')
    
    # 7. 无监督聚类
    print("\n7. 无监督聚类...")
    clusters, kmeans_model = processor.cluster_states(reduced_features, n_clusters=4)
    unique_clusters, cluster_counts = np.unique(clusters, return_counts=True)
    print(f"   - 聚类结果: {dict(zip(unique_clusters, cluster_counts))}")
    
    # 8. HMM建模
    print("\n8. HMM状态建模...")
    hmm_model, state_sequence = processor.hmm_modeling(reduced_features, n_states=4)
    unique_states, state_counts = np.unique(state_sequence, return_counts=True)
    print(f"   - 状态分布: {dict(zip(unique_states, state_counts))}")
    
    # 9. 可视化结果
    print("\n9. 可视化结果...")
    processor.plot_state_dynamics(state_sequence)
    print("   - 状态动态图已保存为 neural_state_dynamics.png")
    
    print("\n=== 处理完成 ===")

if __name__ == "__main__":
    main()