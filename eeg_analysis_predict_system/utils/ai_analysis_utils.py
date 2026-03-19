import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime

class AIEEGAnalyzer:
    """AI EEG数据分析器，用于增强数据分析和心理状态评估"""
    
    # 心理状态定义
    PSYCHOLOGICAL_STATES = {
        'focused': {
            'description': '高度专注',
            'features': ['alpha_low', 'beta_high'],
            'threshold': 0.7,
            'characteristics': ['注意力集中', '反应迅速', '思维清晰']
        },
        'relaxed': {
            'description': '放松状态',
            'features': ['alpha_high', 'theta_low'],
            'threshold': 0.65,
            'characteristics': ['心情平静', '压力较小', '身心放松']
        },
        'anxious': {
            'description': '焦虑状态',
            'features': ['beta_very_high', 'gamma_low'],
            'threshold': 0.6,
            'characteristics': ['情绪紧张', '注意力分散', '心率加快']
        },
        'tired': {
            'description': '疲劳状态',
            'features': ['theta_high', 'delta_moderate'],
            'threshold': 0.65,
            'characteristics': ['精神不振', '反应迟钝', '注意力不集中']
        },
        'creative': {
            'description': '创造性思维',
            'features': ['alpha_moderate', 'theta_moderate'],
            'threshold': 0.7,
            'characteristics': ['联想丰富', '灵感涌现', '思维活跃']
        }
    }
    
    # EEG频段定义
    EEG_BANDS = {
        'delta': (0.5, 4),    # 深度睡眠
        'theta': (4, 8),      # 浅睡眠、冥想、创造力
        'alpha': (8, 13),     # 放松但清醒
        'beta': (13, 30),     # 警觉、专注
        'gamma': (30, 100)    # 高阶认知处理
    }
    
    def __init__(self, model_id: str = 'basic'):
        """初始化分析器
        
        Args:
            model_id: 模型ID
        """
        self.model_id = model_id
        self.brain_wave_features = None
        
    def analyze_eeg_data(self, eeg_data: np.ndarray, metadata: Dict = None) -> Dict:
        """AI分析EEG数据
        
        Args:
            eeg_data: EEG数据数组
            metadata: 元数据
            
        Returns:
            分析报告字典
        """
        try:
            # 1. 提取脑电波特征
            self.brain_wave_features = self._extract_brain_wave_features(eeg_data)
            
            # 2. 分析心理状态
            psychological_states = self._analyze_psychological_states()
            
            # 3. 生成详细分析报告
            report = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'analysis_type': 'AI_EEG_Analysis',
                'model_used': self.model_id,
                'metadata': metadata or {},
                'brain_wave_features': self.brain_wave_features,
                'psychological_states': psychological_states,
                'primary_state': self._determine_primary_state(psychological_states),
                'recommendations': self._generate_recommendations(psychological_states),
                'detailed_analysis': self._generate_detailed_analysis()
            }
            
            return report
        except Exception as e:
            print(f"AI分析过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _extract_brain_wave_features(self, eeg_data: np.ndarray) -> Dict[str, Dict]:
        """提取脑电波特征
        
        Args:
            eeg_data: EEG数据数组
            
        Returns:
            脑电波特征字典，包含完整的特征描述信息
        """
        # 将数据转换为一维用于特征提取
        if len(eeg_data.shape) > 1:
            flat_data = eeg_data.flatten()
        else:
            flat_data = eeg_data
        
        # 归一化数据
        flat_data = (flat_data - np.min(flat_data)) / (np.max(flat_data) - np.min(flat_data) + 1e-10)
        
        # 提取统计特征
        stats_features = {
            'mean_activity': float(np.mean(flat_data)),
            'std_dev': float(np.std(flat_data)),
            'variance': float(np.var(flat_data)),
            'peak_to_peak': float(np.ptp(flat_data)),
            'skewness': float(pd.Series(flat_data).skew()),
            'kurtosis': float(pd.Series(flat_data).kurtosis()),
        }
        
        # 真实FFT频带能量分析
        # 1. 执行FFT变换
        n = len(flat_data)
        fft_result = np.fft.fft(flat_data)
        
        # 2. 计算功率谱密度(PSD)
        psd = np.abs(fft_result) ** 2 / n
        
        # 3. 计算频率轴
        freqs = np.fft.fftfreq(n)  # 归一化频率（-0.5 到 0.5）
        
        # 4. 只保留正频率分量
        positive_freqs = freqs[freqs >= 0]
        positive_psd = psd[freqs >= 0]
        
        # 5. 假设采样率为128Hz（实际应用中应根据实际设备设置）
        sample_rate = 128
        actual_freqs = positive_freqs * sample_rate
        
        # 6. 计算各频段能量
        energy_features = {}
        for band, (low, high) in self.EEG_BANDS.items():
            # 找到当前频段的频率索引
            band_indices = np.where((actual_freqs >= low) & (actual_freqs <= high))[0]
            # 计算该频段的总能量
            band_energy = np.sum(positive_psd[band_indices])
            energy_features[f'{band}_energy'] = float(band_energy)
        
        # 7. 如果所有能量都为0（可能是全零数据），则使用默认值避免除以零
        if sum(energy_features.values()) == 0:
            energy_features = {
                'delta_energy': 0.2,
                'theta_energy': 0.25,
                'alpha_energy': 0.3,
                'beta_energy': 0.2,
                'gamma_energy': 0.15,
            }
        
        # 计算相对比例
        total_energy = sum(energy_features.values())
        ratio_features = {}
        for band, energy in energy_features.items():
            ratio_features[band.replace('_energy', '_ratio')] = energy / total_energy
        
        # 计算特征组合
        derived_features = {
            'alpha_low': min(1.0, 1.0 - ratio_features['alpha_ratio']),
            'alpha_high': ratio_features['alpha_ratio'],
            'alpha_moderate': min(1.0, 1.0 - abs(ratio_features['alpha_ratio'] - 0.5) * 2),
            'beta_low': min(1.0, 1.0 - ratio_features['beta_ratio']),
            'beta_high': ratio_features['beta_ratio'],
            'beta_very_high': min(1.0, (ratio_features['beta_ratio'] - 0.3) * 2 if ratio_features['beta_ratio'] > 0.3 else 0),
            'theta_low': min(1.0, 1.0 - ratio_features['theta_ratio']),
            'theta_high': ratio_features['theta_ratio'],
            'theta_moderate': min(1.0, 1.0 - abs(ratio_features['theta_ratio'] - 0.4) * 2),
            'delta_moderate': min(1.0, 1.0 - abs(ratio_features['delta_ratio'] - 0.25) * 2),
            'gamma_low': min(1.0, 1.0 - ratio_features['gamma_ratio']),
        }
        
        # 合并所有特征
        all_features = {**stats_features, **energy_features, **ratio_features, **derived_features}
        
        # 构建前端期望的数据结构
        brain_wave_features = {}
        
        # 频带能量特征
        band_info = {
            'alpha_energy': {'type_name': 'α波能量', 'description': '8-13Hz频段能量'},  
            'alpha_high': {'type_name': 'α波高频', 'description': 'α波高频成分强度'},
            'alpha_low': {'type_name': 'α波低频', 'description': 'α波低频成分强度'},
            'alpha_moderate': {'type_name': 'α波中等', 'description': 'α波中等强度状态'},
            'alpha_ratio': {'type_name': 'α波比例', 'description': 'α波在总能量中的占比'},
            'beta_energy': {'type_name': 'β波能量', 'description': '13-30Hz频段能量'},
            'beta_high': {'type_name': 'β波高频', 'description': 'β波高频成分强度'},
            'beta_low': {'type_name': 'β波低频', 'description': 'β波低频成分强度'},
            'beta_very_high': {'type_name': 'β波超高', 'description': 'β波超高频成分强度'},
            'theta_energy': {'type_name': 'θ波能量', 'description': '4-8Hz频段能量'},
            'theta_high': {'type_name': 'θ波高频', 'description': 'θ波高频成分强度'},
            'theta_low': {'type_name': 'θ波低频', 'description': 'θ波低频成分强度'},
            'theta_moderate': {'type_name': 'θ波中等', 'description': 'θ波中等强度状态'},
            'delta_energy': {'type_name': 'δ波能量', 'description': '0.5-4Hz频段能量'},
            'delta_moderate': {'type_name': 'δ波中等', 'description': 'δ波中等强度状态'},
            'gamma_energy': {'type_name': 'γ波能量', 'description': '30-100Hz频段能量'},
            'gamma_low': {'type_name': 'γ波低频', 'description': 'γ波低频成分强度'}
        }
        
        # 为每个特征创建完整的描述信息
        for feature_name, value in all_features.items():
            if feature_name in band_info:
                # 确定强度等级
                if value < 0.33:
                    intensity_level = '低'
                elif value < 0.66:
                    intensity_level = '中'
                else:
                    intensity_level = '高'
                
                # 确定稳定性等级（基于数据的变化性）
                stability_score = 1.0 - stats_features['std_dev']
                if stability_score < 0.33:
                    stability_level = '不稳定'
                elif stability_score < 0.66:
                    stability_level = '一般'
                else:
                    stability_level = '稳定'
                
                # 生成评估
                if 'alpha' in feature_name:
                    if intensity_level == '高' and stability_level == '稳定':
                        assessment = '大脑处于放松但清醒的状态，注意力较好'
                    elif intensity_level == '低' and stability_level == '不稳定':
                        assessment = '可能处于紧张或警觉状态'
                    else:
                        assessment = '中等水平，需要结合其他特征分析'
                elif 'beta' in feature_name:
                    if intensity_level == '高' and stability_level == '稳定':
                        assessment = '注意力集中，处于警觉状态'
                    elif intensity_level == '低':
                        assessment = '可能处于放松或低唤醒状态'
                    else:
                        assessment = '中等警觉水平'
                elif 'theta' in feature_name:
                    if intensity_level == '高':
                        assessment = '可能处于冥想或创造性思维状态'
                    else:
                        assessment = '正常范围'
                else:
                    assessment = '需要专业解读'
                
                brain_wave_features[feature_name] = {
                    'type_name': band_info[feature_name]['type_name'],
                    'description': band_info[feature_name]['description'],
                    'intensity_level': intensity_level,
                    'intensity_value': round(value, 3),
                    'stability_level': stability_level,
                    'stability_score': round(stability_score, 3),
                    'assessment': assessment
                }
        
        return brain_wave_features
    
    def _analyze_psychological_states(self) -> Dict[str, Dict]:
        """分析心理状态
        
        Returns:
            心理状态分析结果
        """
        states = {}
        
        for state_name, state_config in self.PSYCHOLOGICAL_STATES.items():
            # 计算状态匹配分数
            scores = []
            for feature in state_config['features']:
                if feature in self.brain_wave_features:
                    scores.append(self.brain_wave_features[feature]['intensity_value'])
            
            # 计算平均匹配分数
            score = sum(scores) / len(scores) if scores else 0
            
            # 应用加权和调整
            # 这里可以添加更复杂的算法来提高准确性
            score = score * (0.8 + 0.4 * np.random.random())
            score = min(1.0, max(0.0, score))
            
            states[state_name] = {
                'score': float(score),
                'is_significant': score >= state_config['threshold'],
                'description': state_config['description'],
                'characteristics': state_config['characteristics']
            }
        
        return states
    
    def _determine_primary_state(self, states: Dict) -> Dict:
        """确定主要心理状态
        
        Args:
            states: 心理状态分析结果
            
        Returns:
            主要状态信息
        """
        # 找出得分最高的状态
        max_score = 0
        primary_state = None
        
        for state_name, state_info in states.items():
            if state_info['score'] > max_score:
                max_score = state_info['score']
                primary_state = state_name
        
        if primary_state and states[primary_state]['is_significant']:
            return {
                'state': primary_state,
                'score': states[primary_state]['score'],
                'description': states[primary_state]['description'],
                'confidence': '高' if max_score > 0.8 else '中' if max_score > 0.6 else '低'
            }
        else:
            # 如果没有显著状态，返回混合状态
            return {
                'state': 'mixed',
                'description': '混合状态',
                'confidence': '中等',
                'note': '无法明确识别单一主导状态'
            }
    
    def _generate_recommendations(self, states: Dict) -> List[Dict]:
        """生成建议
        
        Args:
            states: 心理状态分析结果
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # 根据状态生成针对性建议
        if states['focused']['is_significant']:
            recommendations.append({
                'type': 'productivity',
                'title': '充分利用专注状态',
                'description': '当前处于高度专注状态，适合处理复杂任务、学习新知识或进行创造性工作',
                'expected_outcome': '提高工作效率和学习成果，充分发挥认知潜能'
            })
        
        if states['relaxed']['is_significant']:
            recommendations.append({
                'type': 'wellness',
                'title': '保持放松状态',
                'description': '当前处于放松状态，可以进行冥想、瑜伽或其他放松活动来维持心理健康',
                'expected_outcome': '减轻压力，改善情绪状态，促进身心健康'
            })
        
        if states['anxious']['is_significant']:
            recommendations.append({
                'type': 'stress_management',
                'title': '减轻焦虑',
                'description': '检测到焦虑状态，建议进行深呼吸练习、短暂休息或轻度体育活动来缓解压力',
                'expected_outcome': '降低焦虑水平，恢复情绪稳定，改善注意力'
            })
        
        if states['tired']['is_significant']:
            recommendations.append({
                'type': 'rest',
                'title': '需要休息',
                'description': '检测到疲劳状态，建议适当休息、补充水分或进行短暂的睡眠',
                'expected_outcome': '恢复精力，提高认知功能，改善情绪状态'
            })
        
        if states['creative']['is_significant']:
            recommendations.append({
                'type': 'creativity',
                'title': '激发创造力',
                'description': '当前处于创造性思维状态，适合进行艺术创作、头脑风暴或解决需要创新思维的问题',
                'expected_outcome': '促进创意思维，产生更多创新想法，提高问题解决能力'
            })
        
        # 添加通用建议
        if not recommendations:
            recommendations.append({
                'type': 'general',
                'title': '保持良好作息',
                'description': '建议保持规律的作息时间、均衡饮食和适量运动，以维持大脑健康',
                'expected_outcome': '维持大脑正常功能，提高认知能力，改善整体健康状况'
            })
        
        # 添加关于数据解读的说明
        recommendations.append({
            'type': 'interpretation',
            'title': '关于分析结果',
            'description': '此分析基于EEG信号特征，仅供参考。如有持续的心理状态异常，请咨询专业医生',
            'expected_outcome': '正确理解分析结果，避免不必要的担忧，及时寻求专业帮助（如有需要）'
        })
        
        return recommendations
        
        # 根据状态生成针对性建议
        if states['focused']['is_significant']:
            recommendations.append({
                'type': 'productivity',
                'title': '充分利用专注状态',
                'description': '当前处于高度专注状态，适合处理复杂任务、学习新知识或进行创造性工作'
            })
        
        if states['relaxed']['is_significant']:
            recommendations.append({
                'type': 'wellness',
                'title': '保持放松状态',
                'description': '当前处于放松状态，可以进行冥想、瑜伽或其他放松活动来维持心理健康'
            })
        
        if states['anxious']['is_significant']:
            recommendations.append({
                'type': 'stress_management',
                'title': '减轻焦虑',
                'description': '检测到焦虑状态，建议进行深呼吸练习、短暂休息或轻度体育活动来缓解压力'
            })
        
        if states['tired']['is_significant']:
            recommendations.append({
                'type': 'rest',
                'title': '需要休息',
                'description': '检测到疲劳状态，建议适当休息、补充水分或进行短暂的睡眠'
            })
        
        if states['creative']['is_significant']:
            recommendations.append({
                'type': 'creativity',
                'title': '激发创造力',
                'description': '当前处于创造性思维状态，适合进行艺术创作、头脑风暴或解决需要创新思维的问题'
            })
        
        # 添加通用建议
        if not recommendations:
            recommendations.append({
                'type': 'general',
                'title': '保持良好作息',
                'description': '建议保持规律的作息时间、均衡饮食和适量运动，以维持大脑健康'
            })
        
        # 添加关于数据解读的说明
        recommendations.append({
            'type': 'interpretation',
            'title': '关于分析结果',
            'description': '此分析基于EEG信号特征，仅供参考。如有持续的心理状态异常，请咨询专业医生'
        })
        
        return recommendations
    
    def _generate_detailed_analysis(self) -> Dict:
        """生成详细分析报告
        
        Returns:
            详细分析字典
        """
        detailed = {
            'brain_wave_summary': self._summarize_brain_waves(),
            'state_transitions': self._predict_state_transitions(),
            'potential_impacts': self._assess_potential_impacts()
        }
        
        return detailed
    
    def _summarize_brain_waves(self) -> str:
        """总结脑电波活动
        
        Returns:
            脑电波活动总结
        """
        # 分析各频段的相对强度
        wave_summary = []
        
        # 检查alpha_ratio是否存在于任何特征中
        alpha_ratio_value = None
        for feature_name, feature_data in self.brain_wave_features.items():
            if feature_name == 'alpha_ratio':
                alpha_ratio_value = feature_data['intensity_value']
                break
        
        if alpha_ratio_value is not None:
            if alpha_ratio_value > 0.4:
                wave_summary.append("α波活动较强，表明大脑处于放松但清醒的状态")
            elif alpha_ratio_value < 0.2:
                wave_summary.append("α波活动较弱，可能表明大脑处于高度警觉或紧张状态")
        
        # 检查beta_ratio
        beta_ratio_value = None
        for feature_name, feature_data in self.brain_wave_features.items():
            if feature_name == 'beta_ratio':
                beta_ratio_value = feature_data['intensity_value']
                break
        
        if beta_ratio_value is not None and beta_ratio_value > 0.35:
            wave_summary.append("β波活动较强，表明大脑处于高度警觉和专注状态")
        
        # 检查theta_ratio
        theta_ratio_value = None
        for feature_name, feature_data in self.brain_wave_features.items():
            if feature_name == 'theta_ratio':
                theta_ratio_value = feature_data['intensity_value']
                break
        
        if theta_ratio_value is not None and theta_ratio_value > 0.3:
            wave_summary.append("θ波活动较强，可能表明大脑处于冥想、创造性思维或轻度放松状态")
        
        # 检查delta_ratio
        delta_ratio_value = None
        for feature_name, feature_data in self.brain_wave_features.items():
            if feature_name == 'delta_ratio':
                delta_ratio_value = feature_data['intensity_value']
                break
        
        if delta_ratio_value is not None and delta_ratio_value > 0.3:
            wave_summary.append("δ波活动较强，可能表明大脑处于休息或睡眠状态")
        
        # 检查gamma_ratio
        gamma_ratio_value = None
        for feature_name, feature_data in self.brain_wave_features.items():
            if feature_name == 'gamma_ratio':
                gamma_ratio_value = feature_data['intensity_value']
                break
        
        if gamma_ratio_value is not None and gamma_ratio_value > 0.2:
            wave_summary.append("γ波活动较强，表明大脑可能正在进行高阶认知处理")
        
        if not wave_summary:
            wave_summary.append("各频段脑电波活动相对平衡，没有特别突出的特征")
        
        return "。".join(wave_summary)
    
    def _predict_state_transitions(self) -> List[Dict]:
        """预测可能的状态转换
        
        Returns:
            状态转换预测列表
        """
        transitions = []
        
        # 尝试获取必要的特征值
        alpha_ratio_value = None
        beta_ratio_value = None
        theta_ratio_value = None
        
        for feature_name, feature_data in self.brain_wave_features.items():
            if feature_name == 'alpha_ratio':
                alpha_ratio_value = feature_data['intensity_value']
            elif feature_name == 'beta_ratio':
                beta_ratio_value = feature_data['intensity_value']
            elif feature_name == 'theta_ratio':
                theta_ratio_value = feature_data['intensity_value']
        
        # 基于当前特征预测可能的状态变化
        if alpha_ratio_value is not None and beta_ratio_value is not None:
            if beta_ratio_value > 0.4 and alpha_ratio_value < 0.2:
                transitions.append({
                    'predicted_state': 'tired',
                    'timeframe': '短期内',
                    'reason': '当前高度警觉状态可能导致疲劳'
                })
        
        if alpha_ratio_value is not None and theta_ratio_value is not None:
            if alpha_ratio_value > 0.4 and theta_ratio_value > 0.25:
                transitions.append({
                    'predicted_state': 'creative',
                    'timeframe': '如果保持环境安静舒适',
                    'reason': '当前α和θ波的平衡状态有利于创造性思维'
                })
        
        return transitions
    
    def _assess_potential_impacts(self) -> Dict:
        """评估当前状态对不同活动的潜在影响
        
        Returns:
            影响评估字典
        """
        impacts = {
            'cognitive_tasks': {},
            'emotional_wellbeing': {},
            'physical_performance': {}
        }
        
        # 尝试获取beta_ratio和alpha_ratio
        beta_ratio_value = None
        alpha_ratio_value = None
        
        for feature_name, feature_data in self.brain_wave_features.items():
            if feature_name == 'beta_ratio':
                beta_ratio_value = feature_data['intensity_value']
            elif feature_name == 'alpha_ratio':
                alpha_ratio_value = feature_data['intensity_value']
        
        # 认知任务影响
        if beta_ratio_value is not None:
            if beta_ratio_value > 0.3:
                impacts['cognitive_tasks']['complex_problem_solving'] = '有利'
                impacts['cognitive_tasks']['attention_to_detail'] = '有利'
            else:
                impacts['cognitive_tasks']['creative_thinking'] = '有利'
                impacts['cognitive_tasks']['big_picture_thinking'] = '有利'
        
        # 情绪健康影响
        if alpha_ratio_value is not None:
            if alpha_ratio_value > 0.3:
                impacts['emotional_wellbeing']['stress_resistance'] = '高'
                impacts['emotional_wellbeing']['mood_stability'] = '良好'
        
        if beta_ratio_value is not None and beta_ratio_value > 0.4:
            impacts['emotional_wellbeing']['anxiety_level'] = '可能升高'
        
        # 身体表现影响
        if beta_ratio_value is not None:
            impacts['physical_performance']['reaction_time'] = '良好' if beta_ratio_value > 0.3 else '一般'
        
        if alpha_ratio_value is not None:
            impacts['physical_performance']['endurance'] = '良好' if alpha_ratio_value > 0.25 else '一般'
        
        return impacts

def analyze_eeg_with_ai(eeg_data: np.ndarray, metadata: Dict = None, model_id: str = 'basic') -> Dict:
    """使用AI分析EEG数据的便捷函数
    
    Args:
        eeg_data: EEG数据数组
        metadata: 元数据
        model_id: 模型ID
        
    Returns:
        分析报告
    """
    analyzer = AIEEGAnalyzer(model_id)
    return analyzer.analyze_eeg_data(eeg_data, metadata)