from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import numpy as np
from utils.predict_utils import predict_eeg, get_model_info
from utils.psychopathology_utils import analyze_psychopathology, visualize_psychopathology, get_available_models
# 在导入部分添加
from utils.ai_analysis_utils import analyze_eeg_with_ai
from utils.psychopathology_utils import update_model_config
import shutil
import uuid


app = Flask(__name__)

# 配置静态文件夹路径
app.static_folder = 'static'

# 确保模板文件夹配置正确
app.template_folder = 'templates'

# 确保静态图像目录存在
STATIC_IMAGE_DIR = os.path.join('static', 'images')
os.makedirs(STATIC_IMAGE_DIR, exist_ok=True)

# 获取可用模型信息
available_models = get_available_models()

WEIGHTS_DIR = 'weights'
os.makedirs(WEIGHTS_DIR, exist_ok=True)

# ... 添加文件上传路由 ...
@app.route('/upload_weights', methods=['POST'])
def upload_weights():
    """
    上传并更新模型权重文件的API接口
    """
    try:
        # 检查是否有文件部分
        if 'weights_file' not in request.files:
            return jsonify({'error': '未提供权重文件'}), 400
        
        # 获取文件和模型ID
        file = request.files['weights_file']
        model_id = request.form.get('model_id', 'basic')
        
        # 检查文件是否有效
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        # 检查文件扩展名
        if not file.filename.endswith('.pt'):
            return jsonify({'error': '请上传.pt格式的PyTorch权重文件'}), 400
        
        # 生成唯一文件名以避免覆盖
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(WEIGHTS_DIR, unique_filename)
        
        # 保存文件
        file.save(file_path)
        
        # 更新模型配置
        success = update_model_config(model_id, file_path)
        
        if success:
            # 更新可用模型列表
            global available_models
            available_models = get_available_models()
            
            return jsonify({
                'success': True,
                'message': f'模型 {model_id} 的权重文件已成功更新',
                'weights_path': file_path
            })
        else:
            # 如果更新失败，删除上传的文件
            os.remove(file_path)
            return jsonify({'error': f'模型ID {model_id} 不存在'}), 404
            
    except Exception as e:
        print(f"上传权重文件时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    # 检查图像是否存在
    images = {
        'overall_distribution': os.path.exists(os.path.join('static', 'images', 'overall_weight_distribution.png')),
        'heatmap_example': os.path.exists(os.path.join('static', 'images', 'weight_heatmap_block_1_1_weight.png'))
    }
    
    # 准备模型信息
    template_data = {
        'images': images,
        'available_models': available_models,
        'model_info_available': False,
        'model_info': {}
    }
    return render_template('index.html', **template_data)

@app.route('/weights_image/<path:image_name>')
def serve_weights_image(image_name):
    """提供权重可视化图像的路由"""
    image_path = os.path.join(STATIC_IMAGE_DIR, image_name)
    if not os.path.exists(image_path):
        print(f"图像文件不存在: {image_path}")
        # 如果文件不存在，尝试返回示例图像
        if 'heatmap' in image_name:
            example_heatmap = os.path.join(STATIC_IMAGE_DIR, 'weight_heatmap_block_1_1_weight.png')
            if os.path.exists(example_heatmap):
                return send_from_directory(STATIC_IMAGE_DIR, 'weight_heatmap_block_1_1_weight.png')
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
        
        # 获取模型ID，如果没有提供则使用默认值
        model_id = data.get('model_id', 'basic')
        
        # 准备输入数据
        eeg_data = np.array(data['eeg_data'])
        
        # 执行预测
        predictions = predict_eeg(eeg_data, model_id=model_id)
        
        if predictions is not None:
            return jsonify({
                'predictions': predictions.tolist(),
                'model_used': model_id
            })
        else:
            return jsonify({'error': '预测失败'}), 500
    except Exception as e:
        print(f"API预测过程中发生错误: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def api_analyze():
    """提供精神病理学分析功能的API接口"""
    try:
        # 获取JSON数据
        data = request.json
        
        # 检查必要参数
        if 'eeg_data' not in data:
            return jsonify({'error': '未提供EEG数据'}), 400
        
        # 获取模型ID，如果没有提供则使用默认值
        model_id = data.get('model_id', 'basic')
        
        # 准备输入数据
        eeg_data = np.array(data['eeg_data'])
        
        # 执行预测
        predictions = predict_eeg(eeg_data, model_id=model_id)
        
        if predictions is None:
            return jsonify({'error': '预测失败，无法进行分析'}), 500
        
        # 进行精神病理学分析
        analysis_report = analyze_psychopathology(predictions, model_id=model_id)
        
        # 生成可视化图像
        visualization_paths = visualize_psychopathology(analysis_report)
        
        # 添加可视化路径到报告
        analysis_report['visualizations'] = visualization_paths
        
        return jsonify(analysis_report)
    except Exception as e:
        print(f"API分析过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/models')
def get_models():
    """获取可用模型列表的API接口"""
    return jsonify(available_models)

@app.route('/ai_analyze', methods=['POST'])
def api_ai_analyze():
    """提供AI增强的EEG数据分析功能的API接口"""
    try:
        # 获取JSON数据
        data = request.json
        
        # 检查必要参数
        if 'eeg_data' not in data:
            return jsonify({'error': '未提供EEG数据'}), 400
        
        # 获取模型ID和分析选项
        model_id = data.get('model_id', 'basic')
        options = data.get('options', {})
        
        # 准备输入数据
        eeg_data = np.array(data['eeg_data'])
        
        # 执行AI分析
        ai_analysis_report = analyze_eeg_with_ai(eeg_data, options, model_id)
        
        if 'error' in ai_analysis_report:
            return jsonify(ai_analysis_report), 500
        
        return jsonify(ai_analysis_report)
    except Exception as e:
        print(f"AI分析API过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# 在主函数的打印信息中添加新API的说明
if __name__ == '__main__':
    print("启动Flask服务器...")
    print("请在浏览器中访问 http://localhost:5000 查看结果")
    print("使用/predict API接口进行预测")
    print("使用/analyze API接口进行精神病理学分析")
    print("使用/ai_analyze API接口进行AI增强的EEG数据分析")
    print("使用/upload_weights API接口上传并更新模型权重文件")  # 添加这一行
    # 生产环境应设置debug=False
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode)