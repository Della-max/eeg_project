from flask import Flask, send_from_directory, render_template, session, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

from routes.auth import auth_bp
from routes.recording import recording_bp

# 注册蓝图，明确指定 url_prefix 为空字符串
app.register_blueprint(auth_bp, url_prefix='')
app.register_blueprint(recording_bp, url_prefix='')

# 首页路由
@app.route('/')
def index():
    return render_template('index.html')

# 退出登录路由
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)