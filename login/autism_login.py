# 导入需要的库
from flask import Flask, request, render_template_string
import pymysql

# 初始化Flask应用
app = Flask(__name__)

# -------------------------- 配置项（你需要改这里！） --------------------------
# 填写你的MySQL连接信息
MYSQL_CONFIG = {
    "host": "localhost",       # 固定值，不用改
    "user": "root",            # 你的MySQL用户名（一般是root）
    "password": "2006219wy", # 改成你装MySQL时设置的密码！！！
    "database": "autism_system",# 数据库名，和SQL里的一致，不用改
    "charset": "utf8mb4"       # 固定值，不用改
}
# -----------------------------------------------------------------------------

# 登录页面HTML（带样式，更美观） - 全局变量
login_html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>自闭症辅助教育系统 - 登录</title>
    <style>
        * {margin: 0; padding: 0; box-sizing: border-box;}
        body {background-color: #f5f5f5; font-family: Arial, sans-serif;}
        .login-box {width: 350px; margin: 100px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);}
        .login-box h2 {text-align: center; margin-bottom: 20px; color: #333;}
        .form-item {margin-bottom: 15px;}
        .form-item label {display: block; margin-bottom: 5px; color: #666;}
        .form-item input {width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;}
        .login-btn {width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer;}
        .login-btn:hover {background: #0056b3;}
        .error-msg {color: red; text-align: center; margin-top: 10px;}
        .register-link {text-align: center; margin-top: 15px;}
        .register-link a {color: #007bff; text-decoration: none;}
        .register-link a:hover {text-decoration: underline;}
    </style>
</head>
<body>
    <div class="login-box">
        <h2>用户登录</h2>
        <form action="/login" method="post">
            <div class="form-item">
                <label>登录账号</label>
                <input type="text" name="username" required placeholder="请输入账号">
            </div>
            <div class="form-item">
                <label>登录密码</label>
                <input type="password" name="password" required placeholder="请输入密码">
            </div>
            <button type="submit" class="login-btn">登录</button>
            {% if error %}
            <div class="error-msg">{{ error }}</div>
            {% endif %}
            <div class="register-link">还没有账号？<a href="/register">去注册</a></div>
        </form>
    </div>
</body>
</html>
'''

# 注册页面HTML（带样式） - 全局变量
register_html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>自闭症辅助教育系统 - 注册</title>
    <style>
        * {margin: 0; padding: 0; box-sizing: border-box;}
        body {background-color: #f5f5f5; font-family: Arial, sans-serif;}
        .register-box {width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);}
        .register-box h2 {text-align: center; margin-bottom: 20px; color: #333;}
        .form-item {margin-bottom: 15px;}
        .form-item label {display: block; margin-bottom: 5px; color: #666;}
        .form-item input, .form-item select {width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;}
        .register-btn {width: 100%; padding: 10px; background: #28a745; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer;}
        .register-btn:hover {background: #218838;}
        .error-msg {color: red; text-align: center; margin-top: 10px;}
        .login-link {text-align: center; margin-top: 15px;}
        .login-link a {color: #007bff; text-decoration: none;}
        .login-link a:hover {text-decoration: underline;}
    </style>
</head>
<body>
    <div class="register-box">
        <h2>用户注册</h2>
        <form action="/register" method="post">
            <div class="form-item">
                <label>登录账号</label>
                <input type="text" name="username" required placeholder="请输入账号">
            </div>
            <div class="form-item">
                <label>登录密码</label>
                <input type="password" name="password" required placeholder="请输入密码">
            </div>
            <div class="form-item">
                <label>真实姓名</label>
                <input type="text" name="real_name" required placeholder="请输入真实姓名">
            </div>
            <div class="form-item">
                <label>联系电话</label>
                <input type="text" name="phone" placeholder="请输入联系电话">
            </div>
            <div class="form-item">
                <label>用户角色</label>
                <select name="role" required>
                    <option value="1">教育者</option>
                    <option value="2">研究者</option>
                    <option value="3">家长</option>
                </select>
            </div>
            <div class="form-item" id="parent-relation">
                <label>亲子关系</label>
                <input type="text" name="parent_relation" placeholder="如：父亲、母亲">
            </div>
            <button type="submit" class="register-btn">注册</button>
            {% if error %}
            <div class="error-msg">{{ error }}</div>
            {% endif %}
            <div class="login-link">已有账号？<a href="/">去登录</a></div>
        </form>
    </div>
    <script>
        // 当角色选择为家长时显示亲子关系输入框，否则隐藏
        document.querySelector('select[name="role"]').addEventListener('change', function() {
            const parentRelation = document.getElementById('parent-relation');
            if (this.value == 3) {
                parentRelation.style.display = 'block';
            } else {
                parentRelation.style.display = 'none';
            }
        });
        // 初始加载时执行一次
        document.querySelector('select[name="role"]').dispatchEvent(new Event('change'));
    </script>
</body>
</html>
'''

# 连接MySQL数据库的函数（通用）
def get_db_connection():
    """创建并返回MySQL数据库连接"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    except Exception as e:
        print(f"数据库连接失败：{e}")
        return None

# 1. 登录页面（首页）
@app.route('/')
def login_page():
    """显示登录表单"""
    return render_template_string(login_html)

# 2. 登录验证接口
@app.route('/login', methods=['POST'])
def login_verify():
    """验证账号密码，跳转到用户信息页"""
    # 获取用户输入的账号和密码
    username = request.form.get('username')
    password = request.form.get('password')

    # 连接数据库验证
    conn = get_db_connection()
    if not conn:
        return render_template_string(login_html, error="数据库连接失败！")
    
    try:
        cur = conn.cursor()
        # 查询用户（联查基础表+角色详情表）
        cur.execute('''
            SELECT u.*, d.parent_relation
            FROM base_user u
            LEFT JOIN role_detail d ON u.user_id = d.user_id
            WHERE u.username=%s AND u.password=%s AND u.status=1
        ''', (username, password))
        user = cur.fetchone()

        if not user:
            # 登录失败，返回登录页并提示
            return render_template_string(login_html, error="账号或密码错误！")
        
        # 解析用户数据（按表字段顺序）
        user_id, uname, pwd, real_name, role, phone, status, parent_relation = user
        # 转换角色为文字
        role_map = {1: "教育者", 2: "研究者", 3: "家长"}
        role_name = role_map.get(role, "未知角色")
        # 仅家长显示亲子关系
        relation_info = f"亲子关系：{parent_relation if parent_relation else '未填写'}" if role == 3 else ""

        # 登录成功，显示用户信息页
        user_info_html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>用户信息 - {{role_name}}</title>
    <style>
        * {margin: 0; padding: 0; box-sizing: border-box;}
        body {background-color: #f5f5f5; font-family: Arial, sans-serif;}
        .info-box {width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);}
        .info-box h2 {text-align: center; margin-bottom: 20px; color: #333;}
        .info-item {margin-bottom: 10px; padding: 10px; background: #f9f9f9; border-radius: 4px;}
        .info-item label {font-weight: bold; color: #666;}
        .btn-group {margin-top: 20px; text-align: center;}
        .btn-group a {display: inline-block; padding: 8px 20px; margin: 0 5px; text-decoration: none; border-radius: 4px;}
        .edit-btn {background: #28a745; color: white;}
        .logout-btn {background: #dc3545; color: white;}
    </style>
</head>
<body>
    <div class="info-box">
        <h2>欢迎你，{{real_name}}！</h2>
        <div class="info-item"><label>账号：</label>{{username}}</div>
        <div class="info-item"><label>身份：</label>{{role_name}}</div>
        <div class="info-item"><label>电话：</label>{{phone if phone else '未填写'}}</div>
        {% if relation_info %}
        <div class="info-item"><label>{{relation_info}}</label></div>
        {% endif %}
        <div class="btn-group">
            <a href="/edit/{{user_id}}" class="edit-btn">修改我的信息</a>
            <a href="/" class="logout-btn">退出登录</a>
        </div>
    </div>
</body>
</html>
        '''
        return render_template_string(
            user_info_html,
            real_name=real_name,
            username=uname,
            role_name=role_name,
            phone=phone,
            relation_info=relation_info,
            user_id=user_id
        )
    except Exception as e:
        return render_template_string(login_html, error=f"系统错误：{str(e)}")
    finally:
        # 关闭数据库连接（必须！）
        cur.close()
        conn.close()

# 3. 注册页面
@app.route('/register')
def register_page():
    """显示注册表单"""
    return render_template_string(register_html)

# 4. 注册处理接口
@app.route('/register', methods=['POST'])
def register_verify():
    """处理用户注册"""
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
        return render_template_string(register_html, error="数据库连接失败！")
    
    try:
        cur = conn.cursor()
        
        # 检查用户名是否已存在
        cur.execute('SELECT user_id FROM base_user WHERE username=%s', (username,))
        if cur.fetchone():
            return render_template_string(register_html, error="用户名已存在！")
        
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
        return render_template_string(register_html, error=f"注册失败：{str(e)}")
    finally:
        # 关闭连接
        cur.close()
        conn.close()

# 5. 修改信息页面
@app.route('/edit/<int:user_id>')
def edit_info(user_id):
    """显示修改信息的表单"""
    conn = get_db_connection()
    if not conn:
        return render_template_string(login_html, error="数据库连接失败！") + "<a href='/'>返回登录</a>"
    
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
            return "用户不存在！<a href='/'>返回登录</a>"
        
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
    </style>
</head>
<body>
    <div class="edit-box">
        <h2>修改个人信息</h2>
        <form action="/update" method="post">
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
            {}
            <div class="form-item">
                <label>登录密码</label>
                <input type="password" name="password" value="{{pwd}}" required>
            </div>
            <button type="submit" class="save-btn">保存修改</button>
        </form>
        <a href="/login" class="back-btn">返回个人中心</a>
    </div>
</body>
</html>
        '''.format(relation_input)
        return render_template_string(
            edit_html,
            role_name=role_name,
            user_id=user_id,
            role=role,
            real_name=real_name,
            phone=phone,
            pwd=pwd
        )
    except Exception as e:
        return f"系统错误：{str(e)} <a href='/'>返回登录</a>"
    finally:
        cur.close()
        conn.close()

# 6. 保存修改的接口
@app.route('/update', methods=['POST'])
def update_info():
    """保存修改后的用户信息到数据库"""
    # 获取表单提交的数据
    user_id = request.form.get('user_id')
    role = int(request.form.get('role'))
    real_name = request.form.get('real_name')
    phone = request.form.get('phone')
    password = request.form.get('password')
    parent_relation = request.form.get('parent_relation', '')

    conn = get_db_connection()
    if not conn:
        return render_template_string(login_html, error="数据库连接失败！") + "<a href='/edit/{}'>返回修改</a>".format(user_id)
    
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
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>修改成功</title>
            <style>
                .success-box {width: 300px; margin: 100px auto; text-align: center;}
                .success-box h2 {color: #28a745; margin-bottom: 20px;}
                .success-box a {display: inline-block; margin-top: 10px; padding: 8px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;}
            </style>
        </head>
        <body>
            <div class="success-box">
                <h2>信息修改成功！</h2>
                <a href="/login">返回个人中心</a>
            </div>
        </body>
        </html>
        '''
    except Exception as e:
        # 出错则回滚
        conn.rollback()
        return f"修改失败：{str(e)} <a href='/edit/{user_id}'>返回修改</a>"
    finally:
        cur.close()
        conn.close()

# 启动服务（核心！）
if __name__ == '__main__':
    # host=0.0.0.0 允许局域网访问，port=5000 是访问端口
    app.run(host='0.0.0.0', port=5000, debug=True)