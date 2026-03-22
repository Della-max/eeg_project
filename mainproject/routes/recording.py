# routes/recording.py
from flask import Blueprint, request, render_template, session, jsonify, redirect, url_for  # 补全导入
import os
import uuid
import datetime
from utils.db import get_db_connection
from werkzeug.utils import secure_filename  # 安全文件名处理
import os.path  # 补全路径处理

recording_bp = Blueprint('recording', __name__)

# 配置项抽离（便于后续修改）
UPLOAD_FOLDER = os.path.abspath('uploads')  # 改为绝对路径
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'mp4', 'ogg'}  # 允许的音频格式
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 限制文件大小：10MB

# 创建上传目录（确保存在）
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 辅助函数：校验文件格式
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 录音管理页面
@recording_bp.route('/recordings')
def recordings_page():
    # 1. 登录校验
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    
    user_id = session['user_id']
    username = session.get('username', '用户')
    
    # 2. 数据库连接
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败！")  # 改用专用错误页
    
    cur = None
    try:
        cur = conn.cursor()
        # 3. 查询时过滤已删除的录音，字段名匹配表结构
        cur.execute('''
            SELECT recording_id, filename, file_path, record_time
            FROM user_recordings
            WHERE user_id = %s # 过滤软删除
            ORDER BY record_time DESC
        ''', (user_id,))
        recordings = cur.fetchall()
        
        # 4. 构造返回数据
        recording_list = []
        for recording in recordings:
            recording_list.append({
                'id': recording[0],
                'filename': recording[1],
                'file_path': recording[2],
                'record_time': recording[3].strftime('%Y-%m-%d %H:%M:%S') if recording[3] else ''
            })
        
        return render_template('recording.html', 
                             username=username,
                             recordings=recording_list)
    except Exception as e:
        # 错误日志建议：实际项目中添加 logger.error(e)
        return render_template('error.html', error=f"系统错误：{str(e)}")
    finally:
        # 安全关闭游标和连接（避免未定义报错）
        if cur:
            cur.close()
        if conn:
            conn.close()

# 保存录音API
@recording_bp.route('/api/recording/save', methods=['POST'])
def save_recording():
    # 1. 登录校验
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401  # 补充HTTP状态码
    
    user_id = session['user_id']
    cur = None
    conn = None
    
    try:
        # 2. 限制请求大小
        if request.content_length > MAX_CONTENT_LENGTH:
            return jsonify({'success': False, 'message': '文件大小不能超过10MB'}), 413
        
        # 3. 校验文件是否存在
        if 'audio' not in request.files:
            return jsonify({'success': False, 'message': '没有上传音频文件'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'success': False, 'message': '文件名不能为空'}), 400
        
        # 4. 校验文件格式
        if not allowed_file(audio_file.filename):
            return jsonify({'success': False, 'message': f'仅支持{ALLOWED_EXTENSIONS}格式'}), 400
        
        # 5. 生成安全的文件名和路径
        file_ext = audio_file.filename.rsplit('.', 1)[1].lower()
        unique_id = str(uuid.uuid4())
        filename = secure_filename(f"recording_{unique_id}.{file_ext}")  # 安全文件名
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # 6. 保存文件（确保目录可写）
        audio_file.save(file_path)
        
        # 7. 获取录音时长（前端传的参数，需前端配合）
        duration = request.form.get('duration', 0, float)
        
        # 8. 插入数据库（字段名匹配表结构）
        conn = get_db_connection()
        if not conn:
            # 回滚：删除已保存的文件
            os.remove(file_path)
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO user_recordings 
            (user_id, filename, file_path, record_time)
            VALUES (%s, %s, %s, %s)
        ''', (
            user_id, 
            filename, 
            filename,  # 只存储文件名
            datetime.datetime.now()
        ))
        conn.commit()
        
        return jsonify({'success': True, 'message': '录音保存成功'}), 200
    
    except Exception as e:
        # 异常回滚：删除已保存的文件，数据库回滚
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        if conn:
            conn.rollback()
        # 错误日志建议：logger.error(f"保存录音失败：{e}")
        return jsonify({'success': False, 'message': f'保存失败：{str(e)}'}), 500
    
    finally:
        # 安全关闭资源
        if cur:
            cur.close()
        if conn:
            conn.close()