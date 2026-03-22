# utils/db.py
import pymysql

# 数据库配置
MYSQL_CONFIG = {
    "host": "192.168.56.1",
    "user": "root",
    "password": "2006219wy",
    "database": "autism_system",
    "charset": "utf8mb4"
}

def get_db_connection():
    """创建并返回MySQL数据库连接"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    except Exception as e:
        print(f"数据库连接失败：{e}")
        return None