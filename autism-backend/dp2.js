const sql = require('mssql');

// 适配花生壳内网穿透的数据库配置
const dbConfig = {
    user: 'sa', // 你的SQL Server用户名（保持不变）
    password: '2006219wy', // 你的SQL Server密码（保持不变）
    server: '119txyh989002.vicp.fun', // 花生壳提供的公网地址
    database: 'AutismPlatform', // 你的数据库名（保持不变）
    port: 1433, // 花生壳映射的端口（保持1433即可）
    options: {
        encrypt: false, // 本地数据库关闭加密（保持不变）
        trustServerCertificate: true // 忽略证书验证（保持不变）
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