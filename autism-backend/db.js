const sql = require('mssql');

// 替换为你的SQL Server配置
const dbConfig = {
    user: 'sa', // 你的SQL Server用户名
    password: '2006219wy', // 安装SQL Server时设置的密码
    server: 'localhost', // 本地数据库
    database: 'AutismPlatform', // 刚才创建的数据库
    options: {
        encrypt: false, // 本地数据库关闭加密
        trustServerCertificate: true
    }
};

// 连接数据库并导出连接池
const connectDB = async () => {
    try {
        const pool = await sql.connect(dbConfig);
        console.log('SQL Server连接成功！');
        return pool;
    } catch (err) {
        console.error('连接失败：', err);
        process.exit(1); // 连接失败退出程序
    }
};

module.exports = { connectDB, sql };