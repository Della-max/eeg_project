# routes/auth.py
from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify, render_template_string
from utils.db import get_db_connection
import datetime

auth_bp = Blueprint('auth', __name__)

# 个人中心页面
@auth_bp.route('/login')
def user_info_page():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    username = session.get('username', '用户')
    real_name = session.get('real_name', '用户')
    role = session.get('role', 0)
    
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败！")
    
    try:
        cur = conn.cursor()
        # 查询用户信息
        cur.execute('''
            SELECT u.*, d.parent_relation
            FROM base_user u
            LEFT JOIN role_detail d ON u.user_id = d.user_id
            WHERE u.user_id = %s
        ''', (user_id,))
        user = cur.fetchone()
        
        if not user:
            return redirect(url_for('index'))
        
        # 解析用户数据
        user_id, uname, pwd, real_name, role, phone, status, parent_relation = user
        role_map = {1: "教育者", 2: "研究者", 3: "家长"}
        role_name = role_map.get(role, "未知角色")
        relation_info = f"亲子关系：{parent_relation if parent_relation else '未填写'}" if role == 3 else ""
        
        return render_template('user_info.html', 
                             real_name=real_name,
                             username=uname,
                             role_name=role_name,
                             phone=phone,
                             relation_info=relation_info,
                             user_id=user_id)
    except Exception as e:
        return render_template('error.html', error=f"系统错误：{str(e)}")
    finally:
        cur.close()
        conn.close()

# 登录验证
@auth_bp.route('/login', methods=['POST'])
def login_verify():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = get_db_connection()
    if not conn:
        return render_template('index.html', error="数据库连接失败！")
    
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
            return render_template('index.html', error="账号或密码错误！")
        
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
        
        return redirect(url_for('index'))
    except Exception as e:
        return render_template('index.html', error=f"系统错误：{str(e)}")
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

# 儿童管理页面
@auth_bp.route('/children')
def children_page():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    username = session.get('username', '用户')
    role = session.get('role', 0)
    
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败！")
    
    try:
        cur = conn.cursor()
        
        # 根据角色获取儿童列表
        if role == 3:  # 家长
            # 家长查看自己的孩子
            cur.execute('''
                SELECT child_id, child_name, id_card, gender, age, autism_level, create_time
                FROM autism_children
                WHERE parent_id = %s
                ORDER BY child_name
            ''', (user_id,))
        else:  # 教育者和研究者
            # 查看负责的孩子
            cur.execute('''
                SELECT c.child_id, c.child_name, c.id_card, c.gender, c.age, c.autism_level, c.create_time
                FROM autism_children c
                JOIN user_children uc ON c.child_id = uc.child_id
                WHERE uc.user_id = %s
                ORDER BY c.child_name
            ''', (user_id,))
        
        children = cur.fetchall()
        
        # 构造儿童列表
        children_list = []
        for child in children:
            # 确保 child 有足够的元素
            if len(child) >= 7:
                children_list.append({
                    'id': child[0],
                    'name': child[1],
                    'id_card': child[2],
                    'gender': '男' if child[3] == 1 else '女',
                    'age': child[4],
                    'autism_level': child[5],
                    'create_time': child[6].strftime('%Y-%m-%d %H:%M:%S') if child[6] else ''
                })
        
        return render_template('children.html', 
                             username=username,
                             role=role,
                             children=children_list)
    except Exception as e:
        return render_template('error.html', error=f"系统错误：{str(e)}")
    finally:
        cur.close()
        conn.close()

# 添加儿童页面
@auth_bp.route('/children/add')
def add_child_page():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    username = session.get('username', '用户')
    role = session.get('role', 0)
    
    return render_template('add_child.html', 
                         username=username,
                         role=role)

# 添加儿童处理
@auth_bp.route('/children/add', methods=['POST'])
def add_child():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_id = session['user_id']
    role = session.get('role', 0)
    
    try:
        # 获取表单数据
        child_name = request.form.get('child_name')
        id_card = request.form.get('id_card')
        
        # 检查必填字段
        if not id_card or not child_name:
            return jsonify({'success': False, 'message': '身份证号和姓名不能为空'})
        
        # 连接数据库
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'})
        
        cur = conn.cursor()
        
        # 检查身份证号是否已存在
        cur.execute('SELECT child_id FROM autism_children WHERE id_card = %s', (id_card,))
        existing_child = cur.fetchone()
        
        if role == 3:  # 家长
            # 家长添加自己的孩子
            if existing_child:
                return jsonify({'success': False, 'message': '该身份证号的儿童已存在'})
            
            # 获取家长添加儿童所需的其他字段
            gender = request.form.get('gender')
            age = request.form.get('age')
            autism_level = request.form.get('autism_level')
            
            if not gender or not age or not autism_level:
                return jsonify({'success': False, 'message': '请填写完整的儿童信息'})
            
            # 插入儿童信息
            cur.execute('''
                INSERT INTO autism_children (child_name, id_card, gender, age, autism_level, parent_id, create_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (child_name, id_card, int(gender), int(age), autism_level, user_id, datetime.datetime.now()))
        else:  # 教育者和研究者
            # 教育者和研究者根据身份证号添加负责的儿童
            if not existing_child:
                return jsonify({'success': False, 'message': '该身份证号的儿童不存在，请先由家长添加'})
            
            child_id = existing_child[0]
            
            # 检查是否已经添加过
            cur.execute('SELECT id FROM user_children WHERE user_id = %s AND child_id = %s', (user_id, child_id))
            if cur.fetchone():
                return jsonify({'success': False, 'message': '您已经添加过该儿童'})
            
            # 关联用户和儿童
            cur.execute('''
                INSERT INTO user_children (user_id, child_id, create_time)
                VALUES (%s, %s, %s)
            ''', (user_id, child_id, datetime.datetime.now()))
        
        conn.commit()
        return jsonify({'success': True, 'message': '添加成功'})
    except Exception as e:
        # 确保在异常情况下也返回 JSON
        if 'conn' in locals() and conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        # 确保关闭连接
        if 'cur' in locals() and cur:
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()

# 修改信息页面
@auth_bp.route('/edit/<int:user_id>')
def edit_info_page(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if not conn:
        return render_template('error.html', error="数据库连接失败！")
    
    try:
        cur = conn.cursor()
        # 查询当前用户信息
        cur.execute('''
            SELECT u.*, d.parent_relation
            FROM base_user u
            LEFT JOIN role_detail d ON u.user_id = d.user_id
            WHERE u.user_id=%s
        ''', (user_id,))
        user = cur.fetchone()
        if not user:
            return render_template('error.html', error="用户不存在！")
        
        # 解析用户数据
        user_id, uname, pwd, real_name, role, phone, status, parent_relation = user
        role_name = {1: "教育者", 2: "研究者", 3: "家长"}.get(role, "未知")
        # 仅家长显示亲子关系输入框
        relation_input = '''
        <div class="form-item">
            <label>亲子关系</label>
            <input type="text" name="parent_relation" value="{}" placeholder="如：父亲、母亲">
        </div>
        '''.format(parent_relation if parent_relation else "") if role == 3 else ""

        # 修改信息页面HTML
        edit_html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>修改信息 - {{role_name}}</title>
    <style>
        * {margin: 0; padding: 0; box-sizing: border-box;}
        body {background-color: #f5f5f5; font-family: Arial, sans-serif;}
        .edit-box {width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);}
        .edit-box h2 {text-align: center; margin-bottom: 20px; color: #333;}
        .form-item {margin-bottom: 15px;}
        .form-item label {display: block; margin-bottom: 5px; color: #666;}
        .form-item input {width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;}
        .save-btn {width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer;}
        .save-btn:hover {background: #0056b3;}
        .back-btn {display: block; text-align: center; margin-top: 10px; color: #666; text-decoration: none;}
        #message {margin-top: 10px; padding: 10px; border-radius: 4px; text-align: center;}
        .success {background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;}
        .error {background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;}
    </style>
</head>
<body>
    <div class="edit-box">
        <h2>修改个人信息</h2>
        <form id="editForm">
            <input type="hidden" name="user_id" value="{{user_id}}">
            <input type="hidden" name="role" value="{{role}}">
            <div class="form-item">
                <label>真实姓名</label>
                <input type="text" name="real_name" value="{{real_name}}" required>
            </div>
            <div class="form-item">
                <label>联系电话</label>
                <input type="text" name="phone" value="{{phone if phone else ''}}" placeholder="如：13800138000">
            </div>
            {{relation_input|safe}}
            <div class="form-item">
                <label>登录密码</label>
                <input type="password" name="password" value="{{pwd}}" required>
            </div>
            <button type="submit" class="save-btn">保存修改</button>
        </form>
        <a href="/login" class="back-btn">返回个人中心</a>
        <div id="message"></div>
    </div>
    <script>
        document.getElementById('editForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const messageDiv = document.getElementById('message');
            
            try {
                const response = await fetch('/update', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (result.success) {
                    messageDiv.className = 'success';
                    messageDiv.textContent = result.message;
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 1000);
                } else {
                    messageDiv.className = 'error';
                    messageDiv.textContent = result.message;
                }
            } catch (error) {
                messageDiv.className = 'error';
                messageDiv.textContent = '修改失败：' + error.message;
            }
        });
    </script>
</body>
</html>
        '''
        return render_template_string(
            edit_html,
            role_name=role_name,
            user_id=user_id,
            role=role,
            real_name=real_name,
            phone=phone,
            pwd=pwd,
            relation_input=relation_input
        )
    except Exception as e:
        return render_template('error.html', error=f"系统错误：{str(e)}")
    finally:
        cur.close()
        conn.close()

# 保存修改的接口
@auth_bp.route('/update', methods=['POST'])
def update_info():
    """保存修改后的用户信息到数据库"""
    # 获取表单提交的数据
    user_id = request.form.get('user_id')
    role = int(request.form.get('role'))
    real_name = request.form.get('real_name')
    phone = request.form.get('phone')
    password = request.form.get('password')
    parent_relation = request.form.get('parent_relation', '')

    # 检查登录状态
    if 'user_id' not in session or session['user_id'] != int(user_id):
        return jsonify({'success': False, 'message': '请先登录'})

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': '数据库连接失败'})
    
    try:
        cur = conn.cursor()
        # 第一步：更新基础用户表
        cur.execute('''
            UPDATE base_user
            SET real_name=%s, phone=%s, password=%s
            WHERE user_id=%s
        ''', (real_name, phone, password, user_id))
        
        # 第二步：更新角色详情表（仅家长的亲子关系）
        if role == 3:
            # 先查是否有该用户的详情记录
            cur.execute('SELECT detail_id FROM role_detail WHERE user_id=%s', (user_id,))
            if cur.fetchone():
                # 有记录则更新
                cur.execute('''
                    UPDATE role_detail
                    SET parent_relation=%s
                    WHERE user_id=%s
                ''', (parent_relation, user_id))
            else:
                # 无记录则插入
                cur.execute('''
                    INSERT INTO role_detail (user_id, parent_relation)
                    VALUES (%s, %s)
                ''', (user_id, parent_relation))
        
        # 提交修改（必须！）
        conn.commit()
        return jsonify({'success': True, 'message': '信息修改成功！'})
    except Exception as e:
        # 出错则回滚
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cur.close()
        conn.close()