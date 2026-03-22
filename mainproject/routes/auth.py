# routes/auth.py
from flask import Blueprint, request, render_template, redirect, url_for, session
from utils.db import get_db_connection

auth_bp = Blueprint('auth', __name__)

# 登录页面
@auth_bp.route('/')
def login_page():
    return render_template('login.html')

# 登录验证
@auth_bp.route('/login', methods=['POST'])
def login_verify():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = get_db_connection()
    if not conn:
        return render_template('login.html', error="数据库连接失败！")
    
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT u.*, d.parent_relation
            FROM base_user u
            LEFT JOIN role_detail d ON u.user_id = d.user_id
            WHERE u.username=%s AND u.password=%s AND u.status=1
        ''', (username, password))
        user = cur.fetchone()
        
        if not user:
            return render_template('login.html', error="账号或密码错误！")
        
        # 解析用户数据
        user_id, uname, pwd, real_name, role, phone, status, parent_relation = user
        role_map = {1: "教育者", 2: "研究者", 3: "家长"}
        role_name = role_map.get(role, "未知角色")
        relation_info = f"亲子关系：{parent_relation if parent_relation else '未填写'}" if role == 3 else ""
        
        # 设置session
        session['user_id'] = user_id
        session['username'] = uname
        session['real_name'] = real_name
        session['role'] = role
        
        return render_template('user_info.html', 
                             real_name=real_name,
                             username=uname,
                             role_name=role_name,
                             phone=phone,
                             relation_info=relation_info,
                             user_id=user_id)
    except Exception as e:
        return render_template('login.html', error=f"系统错误：{str(e)}")
    finally:
        cur.close()
        conn.close()

# 注册页面
@auth_bp.route('/register')
def register_page():
    return render_template('register.html')

# 注册处理
@auth_bp.route('/register', methods=['POST'])
def register_verify():
        # 获取表单数据
    username = request.form.get('username')
    password = request.form.get('password')
    real_name = request.form.get('real_name')
    phone = request.form.get('phone')
    role = int(request.form.get('role'))
    parent_relation = request.form.get('parent_relation', '')
    
    # 连接数据库
    conn = get_db_connection()
    if not conn:
        return render_template('register.html', error="数据库连接失败！")
    
    try:
        cur = conn.cursor()
        
        # 检查用户名是否已存在
        cur.execute('SELECT user_id FROM base_user WHERE username=%s', (username,))
        if cur.fetchone():
            return render_template('register.html', error="用户名已存在！")
        
        # 插入基础用户信息
        cur.execute('''
            INSERT INTO base_user (username, password, real_name, role, phone, status)
            VALUES (%s, %s, %s, %s, %s, 1)
        ''', (username, password, real_name, role, phone))
        
        # 获取刚插入的用户ID
        user_id = cur.lastrowid
        
        # 如果是家长角色，插入亲子关系信息
        if role == 3 and parent_relation:
            cur.execute('''
                INSERT INTO role_detail (user_id, parent_relation)
                VALUES (%s, %s)
            ''', (user_id, parent_relation))
        
        # 提交事务
        conn.commit()
        
        # 注册成功，跳转到登录页面
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>注册成功</title>
            <style>
                .success-box {width: 300px; margin: 100px auto; text-align: center;}
                .success-box h2 {color: #28a745; margin-bottom: 20px;}
                .success-box a {display: inline-block; margin-top: 10px; padding: 8px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;}
            </style>
        </head>
        <body>
            <div class="success-box">
                <h2>注册成功！</h2>
                <p>您的账号已创建，请登录。</p>
                <a href="/">去登录</a>
            </div>
        </body>
        </html>
        '''
    except Exception as e:
        # 出错回滚
        conn.rollback()
        return render_template('register.html', error=f"注册失败：{str(e)}")
    finally:
        # 关闭连接
        cur.close()
        conn.close()