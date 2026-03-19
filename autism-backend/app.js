const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { connectDB, sql } = require('./db.js');

const app = express();
const PORT = 3000;
let pool; // 数据库连接池

// 中间件
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));


// 允许所有域名跨域请求
app.use(cors({
  origin: 'http://localhost:52330', // 开发环境可用，上线后建议指定具体域名
  credentials: true,
  methods: ['GET', 'POST', 'OPTIONS']
}));

// 其他中间件和接口
app.use(express.json());

// 初始化数据库连接
connectDB().then(p => {
    pool = p;
});

// 接口1：查询行为记录（支持筛选/全部查询）
app.get('/api/behavior/get', async (req, res) => {
    try {
        const { child_id } = req.query;
        let result;

        if (child_id) {
            // 按儿童ID筛选查询
            result = await pool.request()
                .input('child_id', sql.VarChar, child_id)
                .query('SELECT * FROM behavior_record WHERE child_id = @child_id');
        } else {
            // 无筛选时查询所有记录
            result = await pool.request()
                .query('SELECT * FROM behavior_record');
        }

        res.status(200).json({
            success: true,
            data: result.recordset
        });
    } catch (err) {
        res.status(500).json({ 
            success: false, 
            message: '服务器错误', 
            error: err.message 
        });
    }
});

app.post('/api/behavior/add', async (req, res) => {
    try {
        const { child_id, behavior_type, intensity, start_time, end_time, scene, observer_id } = req.body;

        // 1. 校验必填参数
        if (!child_id || !behavior_type || !intensity || !start_time || !end_time || !scene || !observer_id) {
            return res.status(400).json({
                success: false,
                message: '所有字段都不能为空！'
            });
        }

        // 2. 插入数据库（参数化查询防注入）
        const result = await pool.request()
            .input('child_id', sql.VarChar, child_id)
            .input('behavior_type', sql.VarChar, behavior_type)
            .input('intensity', sql.Int, intensity)
            .input('start_time', sql.BigInt, start_time)
            .input('end_time', sql.BigInt, end_time)
            .input('scene', sql.VarChar, scene)
            .input('observer_id', sql.VarChar, observer_id)
            .query(`
                INSERT INTO behavior_record 
                (child_id, behavior_type, intensity, start_time, end_time, scene, observer_id)
                VALUES (@child_id, @behavior_type, @intensity, @start_time, @end_time, @scene, @observer_id)
            `);

        // 3. 返回成功结果
        res.status(200).json({
            success: true,
            message: '行为记录录入成功！',
            insertId: result.rowsAffected[0] // 影响的行数
        });
    } catch (err) {
        res.status(500).json({
            success: false,
            message: '录入失败',
            error: err.message
        });
    }
});
// 接口3：上传EEG特征数据（研究者用）
app.post('/api/eeg/add', async (req, res) => {
    try {
        const { child_id, alpha_power, beta_power, theta_power, sample_time, scene, uploader_id } = req.body;

        // 1. 校验必填参数
        if (!child_id || !alpha_power || !beta_power || !theta_power || !sample_time || !scene || !uploader_id) {
            return res.status(400).json({
                success: false,
                message: '所有字段都不能为空！'
            });
        }

        // 2. 校验数值范围（波功率0-100）
        if (alpha_power < 0 || alpha_power > 100 || beta_power < 0 || beta_power > 100 || theta_power < 0 || theta_power > 100) {
            return res.status(400).json({
                success: false,
                message: '波功率值必须在0-100之间！'
            });
        }

        // 3. 插入数据库
        const result = await pool.request()
            .input('child_id', sql.VarChar, child_id)
            .input('alpha_power', sql.Float, alpha_power)
            .input('beta_power', sql.Float, beta_power)
            .input('theta_power', sql.Float, theta_power)
            .input('sample_time', sql.BigInt, sample_time)
            .input('scene', sql.VarChar, scene)
            .input('uploader_id', sql.VarChar, uploader_id)
            .query(`
                INSERT INTO eeg_feature_data 
                (child_id, alpha_power, beta_power, theta_power, sample_time, scene, uploader_id)
                VALUES (@child_id, @alpha_power, @beta_power, @theta_power, @sample_time, @scene, @uploader_id)
            `);

        res.status(200).json({
            success: true,
            message: 'EEG特征上传成功！',
            feature_id: result.rowsAffected[0]
        });
    } catch (err) {
        res.status(500).json({
            success: false,
            message: '上传失败',
            error: err.message
        });
    }
});
// 接口4：查询EEG特征数据（支持按儿童ID筛选）
app.get('/api/eeg/get', async (req, res) => {
    try {
        const { child_id } = req.query;
        let result;

        if (child_id) {
            // 按儿童ID筛选
            result = await pool.request()
                .input('child_id', sql.VarChar, child_id)
                .query('SELECT * FROM eeg_feature_data WHERE child_id = @child_id');
        } else {
            // 查询所有
            result = await pool.request()
                .query('SELECT * FROM eeg_feature_data');
        }

        res.status(200).json({
            success: true,
            data: result.recordset
        });
    } catch (err) {
        res.status(500).json({
            success: false,
            message: '服务器错误',
            error: err.message
        });
    }
});
// 接口5：行为-EEG时间对齐（核心算法）
app.post('/api/behavior-eeg/match', async (req, res) => {
    try {
        const { child_id } = req.body;
        if (!child_id) {
            return res.status(400).json({
                success: false,
                message: 'child_id不能为空！'
            });
        }

        // 步骤1：查询该儿童的所有行为记录
        const behaviorResult = await pool.request()
            .input('child_id', sql.VarChar, child_id)
            .query('SELECT * FROM behavior_record WHERE child_id = @child_id');
        const behaviors = behaviorResult.recordset;
        if (behaviors.length === 0) {
            return res.status(400).json({
                success: false,
                message: '该儿童暂无行为记录！'
            });
        }

        // 步骤2：查询该儿童的所有EEG特征数据
        const eegResult = await pool.request()
            .input('child_id', sql.VarChar, child_id)
            .query('SELECT * FROM eeg_feature_data WHERE child_id = @child_id');
        const eegFeatures = eegResult.recordset;
        if (eegFeatures.length === 0) {
            return res.status(400).json({
                success: false,
                message: '该儿童暂无EEG特征数据！'
            });
        }

        // 步骤3：时间对齐核心算法（时间区间重叠匹配）
        const matchResults = [];
        for (const behavior of behaviors) {
            const behaviorStart = Number(behavior.start_time);
            const behaviorEnd = Number(behavior.end_time);
            
            // 筛选出时间在行为区间内的EEG数据
            const matchedEeg = eegFeatures.filter(eeg => {
                const eegTime = Number(eeg.sample_time);
                return eegTime >= behaviorStart && eegTime <= behaviorEnd;
            });

            // 计算时间重叠率（EEG时间在行为区间内的占比，这里简化为1）
            const overlapRate = matchedEeg.length > 0 ? 1.0 : 0.0;

            // 存储匹配结果到数据库
            for (const eeg of matchedEeg) {
                await pool.request()
                    .input('record_id', sql.Int, behavior.record_id)
                    .input('feature_id', sql.Int, eeg.feature_id)
                    .input('overlap_rate', sql.Float, overlapRate)
                    .query(`
                        INSERT INTO behavior_eeg_mapping 
                        (record_id, feature_id, time_overlap_rate)
                        VALUES (@record_id, @feature_id, @overlap_rate)
                    `);

                matchResults.push({
                    behavior_record_id: behavior.record_id,
                    behavior_type: behavior.behavior_type,
                    eeg_feature_id: eeg.feature_id,
                    alpha_power: eeg.alpha_power,
                    beta_power: eeg.beta_power,
                    theta_power: eeg.theta_power,
                    overlap_rate: overlapRate
                });
            }
        }

        // 返回匹配结果
        res.status(200).json({
            success: true,
            message: `时间对齐完成！共匹配到 ${matchResults.length} 组行为-EEG数据`,
            data: matchResults
        });
    } catch (err) {
        res.status(500).json({
            success: false,
            message: '时间对齐失败',
            error: err.message
        });
    }
});
// 接口6：查询EEG校准规则
app.get('/api/calibration/rule/get', async (req, res) => {
    try {
        const result = await pool.request()
            .query('SELECT * FROM eeg_calibration_rule');
        
        res.status(200).json({
            success: true,
            data: result.recordset
        });
    } catch (err) {
        res.status(500).json({
            success: false,
            message: '查询规则失败',
            error: err.message
        });
    }
});
// 接口7：执行EEG校准行为标签（核心算法）
app.post('/api/calibration/execute', async (req, res) => {
    try {
        const { child_id } = req.body;
        if (!child_id) {
            return res.status(400).json({
                success: false,
                message: 'child_id不能为空！'
            });
        }

        // 步骤1：获取该儿童的 行为-EEG 关联数据
        const mappingResult = await pool.request()
            .input('child_id', sql.VarChar, child_id)
            .query(`
                SELECT br.record_id, br.behavior_type AS original_label,
                       efd.alpha_power, efd.beta_power, efd.theta_power, efd.feature_id
                FROM behavior_record br
                JOIN behavior_eeg_mapping bem ON br.record_id = bem.record_id
                JOIN eeg_feature_data efd ON bem.feature_id = efd.feature_id
                WHERE br.child_id = @child_id
            `);
        const mappingData = mappingResult.recordset;
        if (mappingData.length === 0) {
            return res.status(400).json({
                success: false,
                message: '该儿童暂无行为-EEG关联数据，请先执行时间对齐！'
            });
        }

        // 步骤2：获取所有校准规则
        const ruleResult = await pool.request()
            .query('SELECT * FROM eeg_calibration_rule');
        const rules = ruleResult.recordset;

        // 步骤3：执行校准逻辑
        const calibrationResults = [];
        for (const item of mappingData) {
            let correctedLabel = item.original_label;
            let reason = '无需校准（未触发任何规则）';

            // 匹配校准规则
            for (const rule of rules) {
                if (item.original_label !== rule.original_label) continue;

                // 根据规则判断是否触发校准
                let isTrigger = false;
                switch (rule.condition_operator) {
                    case '>':
                        isTrigger = item[`${rule.condition_type}_power`] > rule.condition_value;
                        break;
                    case '<':
                        isTrigger = item[`${rule.condition_type}_power`] < rule.condition_value;
                        break;
                    case '=':
                        isTrigger = item[`${rule.condition_type}_power`] === rule.condition_value;
                        break;
                }

                // 触发校准
                if (isTrigger) {
                    correctedLabel = rule.corrected_label;
                    reason = `${rule.condition_type}波功率${rule.condition_operator}${rule.condition_value} → 触发校准`;
                    break;
                }
            }

            // 步骤4：存储校准结果到数据库
            await pool.request()
                .input('record_id', sql.Int, item.record_id)
                .input('feature_id', sql.Int, item.feature_id)
                .input('original_label', sql.VarChar, item.original_label)
                .input('corrected_label', sql.VarChar, correctedLabel)
                .input('calibration_reason', sql.VarChar, reason)
                .query(`
                    INSERT INTO behavior_calibrated_result 
                    (record_id, feature_id, original_label, corrected_label, calibration_reason)
                    VALUES (@record_id, @feature_id, @original_label, @corrected_label, @calibration_reason)
                `);

            calibrationResults.push({
                record_id: item.record_id,
                original_label: item.original_label,
                corrected_label: correctedLabel,
                alpha_power: item.alpha_power,
                beta_power: item.beta_power,
                theta_power: item.theta_power,
                reason: reason
            });
        }

        // 返回校准结果
        res.status(200).json({
            success: true,
            message: `校准完成！共处理 ${calibrationResults.length} 条行为记录`,
            data: calibrationResults
        });
    } catch (err) {
        res.status(500).json({
            success: false,
            message: '校准执行失败',
            error: err.message
        });
    }
});
// 接口8：查询校准结果（教育者/研究者通用）
app.get('/api/calibration/result/get', async (req, res) => {
    try {
        const { child_id } = req.query;
        let result;

        if (child_id) {
            // 按儿童ID筛选
            result = await pool.request()
                .input('child_id', sql.VarChar, child_id)
                .query(`
                    SELECT bcr.*, br.scene, br.start_time, br.end_time, br.intensity
                    FROM behavior_calibrated_result bcr
                    JOIN behavior_record br ON bcr.record_id = br.record_id
                    WHERE br.child_id = @child_id
                `);
        } else {
            // 查询所有
            result = await pool.request()
                .query(`
                    SELECT bcr.*, br.scene, br.start_time, br.end_time, br.intensity
                    FROM behavior_calibrated_result bcr
                    JOIN behavior_record br ON bcr.record_id = br.record_id
                `);
        }

        res.status(200).json({
            success: true,
            data: result.recordset
        });
    } catch (err) {
        res.status(500).json({
            success: false,
            message: '查询校准结果失败',
            error: err.message
        });
    }
});
// 接口9：双模态数据导出（适配LSTM建模）
app.get('/api/model/export-data', async (req, res) => {
    try {
        const { child_id, start_time, end_time, format = 'json' } = req.query;
        
        // 1. 基础校验
        if (!child_id) {
            return res.status(400).json({
                success: false,
                message: 'child_id不能为空！'
            });
        }

        // 2. 构建查询条件（支持时间范围筛选）
        let timeWhere = '';
        if (start_time && end_time) {
            timeWhere = `AND br.start_time >= ${start_time} AND br.end_time <= ${end_time}`;
        }

        // 3. 查询双模态数据（校准后行为 + EEG特征）
        const result = await pool.request()
            .input('child_id', sql.VarChar, child_id)
            .query(`
                SELECT 
                    br.record_id,
                    br.child_id,
                    br.start_time,
                    br.end_time,
                    br.scene,
                    br.intensity,
                    bcr.original_label,
                    bcr.corrected_label,
                    efd.alpha_power,
                    efd.beta_power,
                    efd.theta_power,
                    efd.sample_time AS eeg_time
                FROM behavior_record br
                JOIN behavior_calibrated_result bcr ON br.record_id = bcr.record_id
                JOIN eeg_feature_data efd ON bcr.feature_id = efd.feature_id
                WHERE br.child_id = @child_id ${timeWhere}
                ORDER BY br.start_time ASC;
            `);

        const rawData = result.recordset;
        if (rawData.length === 0) {
            return res.status(400).json({
                success: false,
                message: '该儿童暂无校准后的双模态数据！'
            });
        }

        // 4. 数据格式化（适配LSTM建模）
        // 核心：将类别型行为标签转为数值编码，拼接时序特征
        const labelMap = {
            '专注': 0,
            '被动走神': 1,
            '主动发起': 2,
            '社交回避': 3,
            '平稳': 4,
            '烦躁': 5
        };

        const modelData = rawData.map(item => ({
            // 时间特征（毫秒级时间戳，LSTM的时序输入）
            timestamp: Number(item.start_time),
            eeg_timestamp: Number(item.eeg_time),
            // 行为特征（数值化）
            behavior_label_original: labelMap[item.original_label] || -1,
            behavior_label_corrected: labelMap[item.corrected_label] || -1,
            behavior_intensity: Number(item.intensity),
            // EEG生理特征（连续值，核心输入）
            eeg_alpha: Number(item.alpha_power),
            eeg_beta: Number(item.beta_power),
            eeg_theta: Number(item.theta_power),
            // 辅助信息
            scene: item.scene,
            time_diff: Number(item.end_time) - Number(item.start_time) // 行为持续时长
        }));

        // 5. 支持JSON/CSV两种导出格式
        if (format === 'csv') {
            // 生成CSV格式
            const headers = Object.keys(modelData[0]).join(',');
            const rows = modelData.map(row => Object.values(row).join(','));
            const csvContent = `${headers}\n${rows.join('\n')}`;
            
            // 设置响应头，触发文件下载
            res.setHeader('Content-Type', 'text/csv');
            res.setHeader('Content-Disposition', `attachment; filename=child_${child_id}_bimodal_data.csv`);
            res.status(200).send(csvContent);
        } else {
            // 默认返回JSON格式
            res.status(200).json({
                success: true,
                message: `导出成功！共${modelData.length}条双模态数据`,
                data: modelData,
                label_mapping: labelMap // 提供标签编码映射表
            });
        }

    } catch (err) {
        res.status(500).json({
            success: false,
            message: '数据导出失败',
            error: err.message
        });
    }
});

// 新增儿童信息接口
app.post('/api/child/add', async (req, res) => {
    try {
        console.log('收到添加儿童信息请求:', req.body);
        
        const { child_id, child_name, gender, age, autism_type, intervention_background } = req.body;

        // 1. 校验必填参数
        if (!child_id || !child_name) {
            console.log('参数校验失败：儿童ID或姓名为空');
            return res.status(400).json({
                success: false,
                message: '儿童ID和姓名不能为空！'
            });
        }

        // 2. 处理可选参数
        const processedAge = age ? parseInt(age) : null;

        // 3. 构造SQL查询
        const sqlQuery = `
            INSERT INTO child_info (child_id, child_name, gender, age, autism_type, intervention_background)
            VALUES (@child_id, @child_name, @gender, @age, @autism_type, @intervention_background)
        `;

        console.log('执行SQL查询:', sqlQuery);
        console.log('参数:', { child_id, child_name, gender, age: processedAge, autism_type, intervention_background });
        // 4. 执行数据库操作
        const result = await pool.request()
            .input('child_id', sql.VarChar, child_id)
            .input('child_name', sql.NVarChar, child_name)
            .input('gender', sql.NVarChar, gender)
            .input('age', sql.Int, processedAge)
            .input('autism_type', sql.NVarChar, autism_type)
            .input('intervention_background', sql.NVarChar, intervention_background)
            .query(sqlQuery);

        console.log('数据库操作结果:', result);

        // 5. 返回成功响应
        res.status(200).json({
            success: true,
            message: '儿童信息添加成功！',
            rowsAffected: result.rowsAffected[0]
        });
    } catch (err) {
        console.error('添加儿童信息失败:', err);
        // 返回详细错误信息以便调试
        res.status(500).json({
            success: false,
            message: '添加失败',
            error: err.message,
            stack: err.stack
        });
    }
});

// 获取儿童列表接口
app.get('/api/child/list', async (req, res) => {
    try {
        const result = await pool.request()
            .query('SELECT * FROM child_info ORDER BY create_time DESC');

        res.status(200).json({
            success: true,
            data: result.recordset
        });
    } catch (err) {
        res.status(500).json({
            success: false,
            message: '查询失败',
            error: err.message
        });
    }
});



// 新增用户（记录人）信息接口
// 新增用户（记录人）信息接口 - 只保留这一个路由！
app.post('/api/user/add', async (req, res) => {
    try {
        console.log('收到添加记录人信息请求:', req.body);
        
        const { user_id, username, role, responsible_child, email, password } = req.body;

        // 校验必填参数
        if (!user_id || !username || !role) {
            console.log('参数校验失败：用户ID、姓名或角色为空');
            return res.status(400).json({
                success: false,
                message: '用户ID、姓名和角色不能为空！'
            });
        }

        // 校验角色合法性
        if (!['researcher', 'educator'].includes(role)) {
            return res.status(400).json({
                success: false,
                message: '角色只能是 researcher（研究者）或 educator（教育者）！'
            });
        }

        // 校验ID是否已存在
        const existResult = await pool.request()
            .input('user_id', sql.VarChar, user_id)
            .query('SELECT * FROM user_table WHERE user_id = @user_id');
        
        if (existResult.recordset.length > 0) {
            return res.status(400).json({
                success: false,
                message: `用户ID ${user_id} 已存在！`
            });
        }

        // 加密密码
        const bcrypt = require('bcryptjs');
        const hashedPassword = bcrypt.hashSync(password || '123456', 10);

        // 执行数据库操作
        await pool.request()
            .input('user_id', sql.VarChar, user_id)
            .input('username', sql.NVarChar, username)
            .input('password', sql.VarChar, hashedPassword)
            .input('role', sql.VarChar, role)
            .input('responsible_child', sql.VarChar, responsible_child || '')
            .input('email', sql.VarChar, email || '')
            .query(`
                INSERT INTO user_table (user_id, username, password, role, responsible_child, email)
                VALUES (@user_id, @username, @password, @role, @responsible_child, @email)
            `);

        // 返回成功响应
        res.status(200).json({
            success: true,
            message: `记录人 ${username}（${user_id}）添加成功！初始密码：${password ? '自定义密码' : '123456'}`
        });
    } catch (err) {
        console.error('添加记录人信息失败:', err);
        res.status(500).json({
            success: false,
            message: '添加失败',
            error: err.message
        });
    }
});

// 添加在用户添加接口之后
app.get('/api/user/list', async (req, res) => {
    try {
        const result = await pool.request()
            .query('SELECT user_id, username, role FROM user_table');
        
        res.status(200).json({
            success: true,
            data: result.recordset
        });
    } catch (err) {
        console.error('获取记录人列表失败:', err);
        res.status(500).json({
            success: false,
            message: '获取记录人列表失败',
            error: err.message
        });
    }
});
// 行为记录录入接口（完全适配你的前端字段）
app.post('/api/behavior/add', async (req, res) => {
    try {
        // 1. 获取前端提交的所有数据（注意字段名和前端保持一致）
        const { 
            child_id, behavior_type, intensity, 
            start_time, end_time, scene, observer_id 
        } = req.body;

        // 2. 基础必填项校验
        if (!child_id || !observer_id || !behavior_type || !start_time || !end_time) {
            return res.status(400).json({
                success: false,
                message: '儿童ID、记录人ID、行为类型、开始/结束时间戳不能为空！'
            });
        }

        // 3. 校验儿童ID是否存在（适配你的child_info表）
        const childExist = await pool.request()
            .input('child_id', sql.VarChar, child_id)
            .query('SELECT * FROM child_info WHERE child_id = @child_id');
        if (childExist.recordset.length === 0) {
            return res.status(400).json({
                success: false,
                message: `儿童ID ${child_id} 不存在！请先添加该儿童信息。`
            });
        }

        // 4. 校验记录人ID是否存在（适配你的user_table表，字段名改为observer_id）
        const userExist = await pool.request()
            .input('user_id', sql.VarChar, observer_id) // 注意这里是observer_id，不是recorder_id
            .query('SELECT * FROM user_table WHERE user_id = @user_id');
        if (userExist.recordset.length === 0) {
            return res.status(400).json({
                success: false,
                message: `记录人ID ${observer_id} 不存在！请先添加该记录人信息。`
            });
        }

        // 5. 插入行为记录到数据库（适配你的behavior_record表）
        await pool.request()
            .input('child_id', sql.VarChar, child_id)
            .input('behavior_type', sql.VarChar, behavior_type)
            .input('intensity', sql.Int, intensity)
            .input('start_time', sql.BigInt, start_time) // 时间戳用BigInt防止溢出
            .input('end_time', sql.BigInt, end_time)
            .input('scene', sql.VarChar, scene)
            .input('observer_id', sql.VarChar, observer_id) // 记录人ID字段名
            .input('is_eeg_exist', sql.TinyInt, 0) // 默认无EEG数据
            .query(`
                INSERT INTO behavior_record (
                    child_id, behavior_type, intensity, start_time, 
                    end_time, scene, observer_id, is_eeg_exist
                )
                VALUES (
                    @child_id, @behavior_type, @intensity, @start_time, 
                    @end_time, @scene, @observer_id, @is_eeg_exist
                )
            `);

        // 6. 返回成功响应
        res.status(200).json({
            success: true,
            message: `行为记录录入成功！儿童ID：${child_id}，行为类型：${behavior_type}`
        });

    } catch (err) {
        // 7. 错误处理
        console.error('行为录入失败：', err); // 终端打印错误，方便排查
        res.status(500).json({
            success: false,
            message: '行为记录录入失败！',
            error: err.message // 可选：返回错误详情，调试用
        });
    }
});

app.get('/', (req, res) => {
    res.send('掬星平台后端服务器运行正常 ✅');
});
// 启动服务器
app.listen(PORT, () => {
    console.log(`后端服务器运行在 http://localhost:${PORT}`);
});