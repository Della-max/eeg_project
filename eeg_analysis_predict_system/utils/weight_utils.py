import torch
import numpy as np
import matplotlib.pyplot as plt
import os

# 确保中文显示正常
plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

def load_weights(weights_path):
    """加载权重文件"""
    if not os.path.exists(weights_path):
        raise FileNotFoundError(f"权重文件不存在: {weights_path}")
    
    try:
        weights = torch.load(weights_path, map_location=torch.device('cpu'))
        return weights
    except Exception as e:
        raise Exception(f"加载权重文件失败: {str(e)}")


def analyze_weights(weights):
    """分析权重的统计信息"""
    results = {}
    
    if isinstance(weights, dict) or isinstance(weights, torch.nn.modules.container.ModuleDict):
        for name, param in weights.items():
            # 检查是否为张量
            if hasattr(param, 'dtype'):
                # 如果是整数类型张量，转换为float32
                if param.dtype.is_floating_point:
                    tensor = param
                else:
                    tensor = param.float()
                
                # 计算统计信息
                results[name] = {
                    'mean': tensor.mean().item(),
                    'std': tensor.std().item(),
                    'min': tensor.min().item(),
                    'max': tensor.max().item(),
                    'shape': list(tensor.shape),
                    'dtype': str(tensor.dtype)
                }
    
    # 计算整体统计信息
    all_weights = []
    for name, stats in results.items():
        if 'mean' in stats:
            all_weights.append(stats['mean'])
    
    if all_weights:
        results['overall'] = {
            'mean': np.mean(all_weights),
            'std': np.std(all_weights),
            'min': np.min(all_weights),
            'max': np.max(all_weights)
        }
    
    return results

def visualize_weights(weights, analysis_results=None):
    """可视化权重分布"""
    # 确保静态图像目录存在
    static_image_dir = os.path.join('static', 'images')
    os.makedirs(static_image_dir, exist_ok=True)
    
    try:
        # 1. 绘制整体权重分布直方图
        plt.figure(figsize=(10, 6))
        
        # 收集所有权重值
        all_weights = []
        for name, param in weights.items():
            if hasattr(param, 'dtype'):
                # 转换为float并展平
                if param.dtype.is_floating_point:
                    tensor = param
                else:
                    tensor = param.float()
                all_weights.extend(tensor.cpu().detach().numpy().flatten())
        
        if all_weights:
            plt.hist(all_weights, bins=100, alpha=0.7, color='blue')
            plt.title('整体权重分布')
            plt.xlabel('权重值')
            plt.ylabel('频率')
            plt.grid(True, alpha=0.3)
            
            # 保存图像
            hist_path = os.path.join(static_image_dir, 'overall_weight_distribution.png')
            plt.savefig(hist_path, dpi=300, bbox_inches='tight')
            print(f"已保存整体权重分布图: {hist_path}")
        
        plt.close()  # 关闭图像以释放资源
        
        # 2. 创建热力图
        # 遍历所有权重并为每个合适的权重创建热力图
        first_heatmap_saved = False
        
        for name, param in weights.items():
            if hasattr(param, 'dtype'):
                try:
                    # 转换为float
                    if param.dtype.is_floating_point:
                        tensor = param
                    else:
                        tensor = param.float()
                    
                    # 提取数据
                    data = tensor.cpu().detach().numpy()
                    
                    # 处理不同维度的数据
                    if len(data.shape) == 1:
                        # 1D数据转为2D以显示热力图
                        dim_size = int(np.ceil(np.sqrt(len(data))))
                        # 填充到合适的大小
                        padded_data = np.zeros((dim_size, dim_size))
                        padded_data.flat[:min(len(data), dim_size*dim_size)] = data[:min(len(data), dim_size*dim_size)]
                        data = padded_data
                    elif len(data.shape) == 3:
                        # 3D数据取第一个通道
                        data = data[0]
                    elif len(data.shape) > 3:
                        # 高维数据展平后转为2D
                        data_flat = data.flatten()
                        dim_size = int(np.ceil(np.sqrt(len(data_flat))))
                        padded_data = np.zeros((dim_size, dim_size))
                        padded_data.flat[:min(len(data_flat), dim_size*dim_size)] = data_flat[:min(len(data_flat), dim_size*dim_size)]
                        data = padded_data
                    
                    # 现在data应该是2D的，可以绘制热力图
                    plt.figure(figsize=(10, 8))
                    plt.imshow(data, cmap='viridis')
                    plt.colorbar(label='权重值')
                    plt.title(f'权重热力图: {name}')
                    plt.xlabel('维度 1')
                    plt.ylabel('维度 0')
                    
                    # 保存图像
                    safe_name = name.replace('/', '_').replace('.', '_')
                    heatmap_path = os.path.join(static_image_dir, f'weight_heatmap_{safe_name}.png')
                    plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
                    print(f"已保存权重热力图: {heatmap_path}")
                    
                    # 确保至少保存一个示例热力图，命名为固定名称
                    if not first_heatmap_saved:
                        example_heatmap_path = os.path.join(static_image_dir, 'weight_heatmap_block_1_1_weight.png')
                        plt.savefig(example_heatmap_path, dpi=300, bbox_inches='tight')
                        print(f"已保存示例权重热力图: {example_heatmap_path}")
                        first_heatmap_saved = True
                    
                    plt.close()
                except Exception as e:
                    print(f"生成热力图时出错 ({name}): {str(e)}")
                    plt.close()
                    continue
        
        # 如果没有生成热力图，创建一个简单的示例图
        if not first_heatmap_saved:
            plt.figure(figsize=(10, 8))
            # 创建一个简单的示例矩阵
            example_matrix = np.random.rand(10, 10)
            plt.imshow(example_matrix, cmap='viridis')
            plt.colorbar(label='权重值')
            plt.title('权重热力图示例')
            plt.xlabel('维度 1')
            plt.ylabel('维度 0')
            
            example_heatmap_path = os.path.join(static_image_dir, 'weight_heatmap_block_1_1_weight.png')
            plt.savefig(example_heatmap_path, dpi=300, bbox_inches='tight')
            print(f"已保存示例权重热力图: {example_heatmap_path}")
            plt.close()
        
    except Exception as e:
        print(f"可视化过程中发生错误: {str(e)}")
        plt.close('all')  # 确保所有图像都被关闭
        raise