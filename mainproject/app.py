# app.py
from flask import Flask, send_from_directory
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 注册蓝图
from routes.auth import auth_bp
from routes.recording import recording_bp

app.register_blueprint(auth_bp)
app.register_blueprint(recording_bp)

# 静态文件路由
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)