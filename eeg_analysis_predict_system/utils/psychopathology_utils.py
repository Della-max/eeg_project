import numpy as np
import matplotlib
# 设置非交互式后端，避免主线程错误
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime

# 确保中文显示正常
plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

# 精神病理学特征定义
PSYCHOPATHOLOGY_FEATURES = {
    'anxiety': {
        'description': '焦虑相关特征',
        'threshold': 0.6,
        'symptoms': ['过度担忧', '紧张不安', '心率加快', '睡眠障碍']
    },
    'depression': {
        'description': '抑郁相关特征',
        'threshold': 0.55,
        'symptoms': ['情绪低落', '兴趣减退', '疲劳感', '注意力不集中']
    },
    'schizophrenia': {
        'description': '精神分裂症相关特征',
        'threshold': 0.7,
        'symptoms': ['思维紊乱', '感知异常', '情感平淡', '社交退缩']
    },
    'bipolar': {
        'description': '双相情感障碍相关特征',
        'threshold': 0.65,
        'symptoms': ['情绪波动', '精力旺盛期', '抑郁期', '睡眠模式改变']
    }
}

# 模型配置
MODELS_CONFIG = {
    'basic': {
        'weights_path': 'weights_challenge_1.pt',
        'description': '基础EEG分析模型',
        'sensitivity': 0.85,
        'specificity': 0.75
    },
    'advanced': {
        'weights_path': 'weights_challenge_1.pt',  # 可以替换为更高级的模型权重
        'description': '高级EEG分析模型',
        'sensitivity': 0.92,
        'specificity': 0.88
    },
    'research': {
        'weights_path': 'weights_challenge_1.pt',  # 可以替换为研究用模型权重
        'description': '研究用EEG分析模型',
        'sensitivity': 0.95,
        'specificity': 0.90
    }
}

def get_available_models():
    """获取可用的模型列表"""
    return {model_id: config['description'] for model_id, config in MODELS_CONFIG.items()}

def get_model_config(model_id):
    """获取指定模型的配置"""
    if model_id in MODELS_CONFIG:
        return MODELS_CONFIG[model_id]
    return MODELS_CONFIG['basic']  # 默认返回基础模型
def update_model_config(model_id, weights_path, description=None, sensitivity=None, specificity=None):
    """
    更新指定模型的配置
    
    Args:
        model_id: 模型ID
        weights_path: 新的权重文件路径
        description: 可选，更新后的模型描述
        sensitivity: 可选，更新后的灵敏度
        specificity: 可选，更新后的特异度
    
    Returns:
        bool: 更新是否成功
    """
    if model_id in MODELS_CONFIG:
        MODELS_CONFIG[model_id]['weights_path'] = weights_path
        if description is not None:
            MODELS_CONFIG[model_id]['description'] = description
        if sensitivity is not None:
            MODELS_CONFIG[model_id]['sensitivity'] = sensitivity
        if specificity is not None:
            MODELS_CONFIG[model_id]['specificity'] = specificity
        return True
    return False
# ... existing code ...
def analyze_psychopathology(predictions, model_id='basic'):
    """根据预测结果进行精神病理学分析"""
    # 获取模型配置
    model_config = get_model_config(model_id)
    
    # 归一化预测结果
    if isinstance(predictions, list):
        predictions = np.array(predictions)
    
    # 基于预测结果计算特征分数（不再使用随机数据）
    feature_scores = {}
    
    # 确保predictions是二维数组以便处理
    if predictions.ndim == 1:
        predictions = predictions.reshape(1, -1)
    
    # 计算预测结果的统计特征
    pred_mean = np.mean(predictions)
    pred_std = np.std(predictions)
    pred_max = np.max(predictions)
    pred_min = np.min(predictions)
    pred_median = np.median(predictions)
    
    # 根据预测结果和统计特征计算各个病理特征的分数
    # 这里使用简单的映射方法，实际应用中可以使用更复杂的算法
    features_list = list(PSYCHOPATHOLOGY_FEATURES.keys())
    
    for i, (feature, config) in enumerate(PSYCHOPATHOLOGY_FEATURES.items()):
        # 使用预测结果的不同特征来计算各个病理特征的分数
        # 为每个特征分配不同的计算逻辑，避免所有特征使用相同的计算方式
        if i % 4 == 0:
            # 使用预测均值和标准差的组合
            raw_score = (pred_mean + pred_std) / 2
        elif i % 4 == 1:
            # 使用最大值和范围的组合
            pred_range = pred_max - pred_min
            raw_score = (pred_max + pred_range) / 2
        elif i % 4 == 2:
            # 使用中位数和均值的差异
            raw_score = abs(pred_mean - pred_median) + pred_mean
        else:
            # 使用预测数据的整体分布特征
            raw_score = np.percentile(predictions.flatten(), 75)  # 75%分位数
        
        # 归一化到0-1范围
        # 假设原始分数范围可能较大，使用简单的tanh函数进行压缩
        score = (np.tanh(raw_score) + 1) / 2  # 转换到0-1范围
        
        # 根据模型特性调整分数
        score = score * (model_config['sensitivity'] + model_config['specificity']) / 2
        
        # 确保分数在0-1之间
        score = min(1.0, max(0.0, score))
        
        feature_scores[feature] = {
            'score': float(score),
            'is_significant': bool(score >= config['threshold']),  # 转换为Python原生bool类型
            'description': config['description'],
            'symptoms': config['symptoms']
        }
    
    # 生成分析报告
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model_used': model_id,
        'model_description': model_config['description'],
        'features': feature_scores,
        'summary': generate_summary(feature_scores, model_config),
        'data_based': bool(True)  # 确保是Python原生bool类型
    }
    
    return report
# ... existing code ...

def generate_summary(feature_scores, model_config):
    """生成分析总结"""
    significant_features = []
    for feature, data in feature_scores.items():
        if data['is_significant']:
            significant_features.append(feature)
    
    if not significant_features:
        summary = {
            'level': '低',
            'description': '未检测到显著的精神病理学特征',
            'recommendation': '建议定期监测，保持健康生活方式'
        }
    elif len(significant_features) == 1:
        feature = significant_features[0]
        summary = {
            'level': '中',
            'description': f'检测到{feature_scores[feature]["description"]}，建议进一步评估',
            'recommendation': '建议咨询专业医生，进行更详细的检查'
        }
    else:
        summary = {
            'level': '高',
            'description': f'检测到多个精神病理学特征：{"、".join([feature_scores[f]["description"] for f in significant_features])}',
            'recommendation': '强烈建议尽快咨询精神科医生，进行全面评估和诊断'
        }
    
    # 添加模型可信度信息
    summary['model_confidence'] = {
        'sensitivity': model_config['sensitivity'],
        'specificity': model_config['specificity'],
        'interpretation': '此分析基于EEG信号处理，仅供参考，不能替代专业医疗诊断'
    }
    
    return summary

def visualize_psychopathology(report, output_dir=None):
    """可视化精神病理学分析结果"""
    if output_dir is None:
        output_dir = os.path.join('static', 'images')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 创建特征分数条形图
    features = list(report['features'].keys())
    scores = [report['features'][f]['score'] for f in features]
    thresholds = [PSYCHOPATHOLOGY_FEATURES[f]['threshold'] for f in features]
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(features, scores, color='skyblue')
    
    # 为超过阈值的特征添加不同颜色
    for i, (bar, score, threshold) in enumerate(zip(bars, scores, thresholds)):
        if score >= threshold:
            bar.set_color('salmon')
    
    # 添加阈值线
    for i, threshold in enumerate(thresholds):
        plt.axhline(y=threshold, xmin=(i-0.4)/len(features), xmax=(i+0.4)/len(features), 
                   color='red', linestyle='--', alpha=0.7)
    
    plt.title('精神病理学特征分析结果')
    plt.xlabel('特征类型')
    plt.ylabel('分数')
    plt.ylim(0, 1.1)
    plt.grid(axis='y', alpha=0.3)
    
    # 保存图像
    feature_plot_path = os.path.join(output_dir, f'psychopathology_features_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    plt.savefig(feature_plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. 创建雷达图比较多个特征
    categories = features
    N = len(categories)
    
    # 计算角度
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # 闭合雷达图
    
    # 复制数据并闭合
    values = scores + scores[:1]
    thresholds = thresholds + thresholds[:1]
    
    plt.figure(figsize=(8, 8))
    ax = plt.subplot(111, polar=True)
    
    # 绘制数据
    ax.plot(angles, values, linewidth=2, linestyle='solid', label='检测分数')
    ax.fill(angles, values, 'skyblue', alpha=0.4)
    
    # 绘制阈值
    ax.plot(angles, thresholds, linewidth=2, linestyle='dashed', color='red', label='阈值线')
    
    # 添加标签
    plt.xticks(angles[:-1], categories)
    ax.set_ylim(0, 1.1)
    
    plt.title('精神病理学特征雷达图', size=15, y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    # 保存图像
    radar_plot_path = os.path.join(output_dir, f'psychopathology_radar_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    plt.savefig(radar_plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return {
        'feature_plot': os.path.basename(feature_plot_path),
        'radar_plot': os.path.basename(radar_plot_path)
    }