import torch
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 设置非交互式后端，避免线程问题
import matplotlib.pyplot as plt
import os
from flask import Flask, render_template, send_from_directory, request, jsonify
from utils.weight_utils import load_weights, analyze_weights, visualize_weights
from utils.predict_utils import predict_eeg, get_model_info

# 配置中文字体
plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 初始化Flask应用
app = Flask(__name__)
app.static_folder = 'static'

# 确保静态图像目录存在
STATIC_IMAGE_DIR = os.path.join('static', 'images')
os.makedirs(STATIC_IMAGE_DIR, exist_ok=True)

# 全局变量存储分析结果
analysis_results = None
model_info = None

# Flask路由
@app.route('/')
def index():
    global analysis_results
    # 准备要传递给模板的数据
    template_data = {
        'analysis_available': analysis_results is not None,
        'results': analysis_results or {},
        'model_info_available': model_info is not None,
        'model_info': model_info or {}
    }
    return render_template('index.html', **template_data)

@app.route('/weights_image/<path:image_name>')
def serve_weights_image(image_name):
    """提供权重可视化图像的路由"""
    image_path = os.path.join(STATIC_IMAGE_DIR, image_name)
    if not os.path.exists(image_path):
        print(f"图像文件不存在: {image_path}")
        return "图像文件不存在", 404
    
    # 使用send_from_directory提供静态文件
    return send_from_directory(STATIC_IMAGE_DIR, image_name)

@app.route('/predict', methods=['POST'])
def api_predict():
    """提供预测功能的API接口"""
    try:
        # 获取JSON数据
        data = request.json
        
        # 检查是否提供了数据
        if 'eeg_data' not in data:
            return jsonify({'error': '未提供EEG数据'}), 400
        
        # 准备输入数据
        eeg_data = np.array(data['eeg_data'])
        
        # 执行预测
        predictions = predict_eeg(eeg_data)
        
        if predictions is not None:
            return jsonify({'predictions': predictions.tolist()})
        else:
            return jsonify({'error': '预测失败'}), 500
    except Exception as e:
        print(f"API预测过程中发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

def main():
    global analysis_results, model_info
    
    try:
        # 1. 加载权重文件
        weights_path = 'weights_challenge_1.pt'
        print(f"正在加载权重文件: {weights_path}")
        weights = load_weights(weights_path)
        
        # 2. 分析权重
        print("正在分析权重...")
        analysis_results = analyze_weights(weights)
        
        # 3. 获取模型信息
        print("正在获取模型信息...")
        model_info = get_model_info(weights_path)
        
        # 4. 可视化权重
        print("正在生成可视化图像...")
        visualize_weights(weights, analysis_results)
        
        print("权重分析和可视化完成！")
        print("请在浏览器中访问 http://localhost:5000 查看结果")
        print("使用/predict API接口进行预测")
        
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # 运行主函数生成分析结果和图像
    main()
    
    # 启动Flask Web服务器
    print("启动Flask服务器...")
    print("请在浏览器中访问 http://localhost:5000 查看结果")
    app.run(debug=True)