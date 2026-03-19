import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import json
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import matplotlib

# 配置matplotlib支持中文显示
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体（Windows内置字体）
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# ===================== 基础配置 =====================
# 设置随机种子确保可复现
torch.manual_seed(42)
np.random.seed(42)

# 行为标签映射（和平台保持一致）
LABEL_MAP = {
    '专注': 0,
    '被动走神': 1,
    '主动发起': 2,
    '社交回避': 3,
    '平稳': 4,
    '烦躁': 5
}
# 特征列（和导出的JSON数据一致）
FEATURE_COLS = ['eeg_alpha', 'eeg_beta', 'eeg_theta', 'behavior_intensity', 'time_diff']

# ===================== 1. 数据加载与预处理（核心改造） =====================
def load_bimodal_data(file_path):
    """加载从平台导出的双模态JSON数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # 转为DataFrame，方便处理
    if isinstance(raw_data, dict) and 'data' in raw_data:
        df = pd.DataFrame(raw_data['data'])  # 兼容平台导出的JSON格式
    else:
        df = pd.DataFrame(raw_data)
    
    # 筛选核心特征和目标标签
    df = df[FEATURE_COLS + ['behavior_label_corrected']].dropna()
    return df

def create_sequences(df, sequence_length=3):
    """
    构建时序数据集（适配分类任务）
    输入：前sequence_length个时间步的特征
    输出：第sequence_length个时间步的行为标签
    """
    # 特征归一化（LSTM对数值敏感）
    scaler = MinMaxScaler(feature_range=(0, 1))
    features_scaled = scaler.fit_transform(df[FEATURE_COLS])
    
    X = []
    y = []
    # 按时间戳排序（关键！时序数据不能乱序）
    for i in range(sequence_length, len(features_scaled)):
        # 取前sequence_length个时间步的特征
        X.append(features_scaled[i-sequence_length:i])
        # 取当前时间步的行为标签（分类目标）
        y.append(df.iloc[i]['behavior_label_corrected'])
    
    return np.array(X), np.array(y), scaler

# 加载真实数据（替换为你的JSON文件路径）
df = load_bimodal_data('child_C001_bimodal_data.json')

# 构建时序序列（短窗口适配少数据场景）
sequence_length = 3
X, y, scaler = create_sequences(df, sequence_length)

# 划分训练集/测试集（时序数据必须shuffle=False）
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False, random_state=42
)

# 转换为PyTorch张量（适配分类任务）
# 特征张量：[样本数, 时序窗口, 特征数]
X_train_tensor = torch.FloatTensor(X_train)  # shape: (N, 3, 5)
X_test_tensor = torch.FloatTensor(X_test)

# 标签张量：分类任务需转为long类型
y_train_tensor = torch.LongTensor(y_train)   # shape: (N,)
y_test_tensor = torch.LongTensor(y_test)

# ===================== 2. 定义LSTM模型（适配分类任务） =====================
class BehaviorLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes):
        super(BehaviorLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM层（batch_first=True：输入格式为[batch, seq, feature]）
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2  # 防止过拟合（数据量少时关键）
        )
        
        # 分类输出层（6类行为标签）
        self.fc1 = nn.Linear(hidden_size, 32)  # 中间层
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, num_classes)  # 输出层
        self.softmax = nn.Softmax(dim=1)       # 输出概率
    
    def forward(self, x):
        # 初始化隐藏状态和细胞状态
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # LSTM前向传播：out shape [batch, seq_len, hidden_size]
        out, _ = self.lstm(x, (h0, c0))
        
        # 取最后一个时间步的输出（时序特征汇总）
        out = out[:, -1, :]
        
        # 分类头
        out = self.fc1(out)
        out = self.relu(out)
        out = self.fc2(out)
        out = self.softmax(out)
        
        return out

# 模型初始化
input_size = len(FEATURE_COLS)  # 5个特征（α/β/θ波+强度+时间差）
hidden_size = 64                # 隐藏层神经元（数据少可设为32）
num_layers = 2                  # LSTM层数
num_classes = len(LABEL_MAP)    # 6类行为标签

model = BehaviorLSTM(input_size, hidden_size, num_layers, num_classes)
print("模型结构：")
print(model)

# ===================== 3. 训练配置（适配分类任务） =====================
# 损失函数：分类任务用交叉熵损失
criterion = nn.CrossEntropyLoss()
# 优化器：Adam（学习率小一点，防止过拟合）
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)

# ===================== 4. 模型训练 =====================
def train_model(model, X_train, y_train, criterion, optimizer, num_epochs=50, batch_size=4):
    """训练分类型LSTM模型"""
    model.train()
    train_losses = []
    train_accs = []
    
    # 创建数据加载器（时序数据shuffle=False，但训练批次可shuffle）
    dataset = torch.utils.data.TensorDataset(X_train, y_train)
    dataloader = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=True
    )
    
    for epoch in range(num_epochs):
        epoch_loss = 0.0
        correct = 0
        total = 0
        
        for batch_X, batch_y in dataloader:
            # 前向传播
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            # 统计损失和准确率
            epoch_loss += loss.item() * batch_X.size(0)
            _, predicted = torch.max(outputs.data, 1)
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()
        
        # 计算本轮平均损失和准确率
        avg_loss = epoch_loss / len(dataset)
        avg_acc = correct / total
        train_losses.append(avg_loss)
        train_accs.append(avg_acc)
        
        # 每10轮打印一次
        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch+1}/{num_epochs}] | Loss: {avg_loss:.4f} | Acc: {avg_acc:.4f}')
    
    return train_losses, train_accs

# 开始训练（数据少则epoch设小一点）
num_epochs = 50
batch_size = 4  # 小批次适配少数据
train_losses, train_accs = train_model(
    model, X_train_tensor, y_train_tensor, criterion, optimizer, num_epochs, batch_size
)

# ===================== 5. 模型评估 =====================
def evaluate_model(model, X_test, y_test):
    """评估模型性能"""
    model.eval()  # 评估模式（关闭dropout）
    with torch.no_grad():
        outputs = model(X_test)
        _, predicted = torch.max(outputs.data, 1)
        total = y_test.size(0)
        correct = (predicted == y_test).sum().item()
        test_acc = correct / total
        
        # 计算测试集损失
        loss = criterion(outputs, y_test)
        
        print(f'\n测试集准确率: {test_acc:.4f}')
        print(f'测试集损失: {loss.item():.4f}')
        
        # 打印混淆矩阵（直观看分类效果）
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(y_test.numpy(), predicted.numpy())
        print("\n混淆矩阵：")
        print(cm)
    
    return test_acc, predicted

# 评估模型
test_acc, test_preds = evaluate_model(model, X_test_tensor, y_test_tensor)

# ===================== 6. 结果可视化 =====================
# 1. 训练损失/准确率曲线
plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
plt.plot(train_losses, label='Train Loss')
plt.title('训练损失变化')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(train_accs, label='Train Acc', color='orange')
plt.title('训练准确率变化')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

# 2. 真实标签vs预测标签对比
plt.figure(figsize=(10, 4))
plt.plot(y_test.numpy(), label='真实标签', marker='o', markersize=4)
plt.plot(test_preds.numpy(), label='预测标签', marker='x', markersize=4)
plt.title('行为标签预测结果对比')
plt.xlabel('测试样本索引')
plt.ylabel('行为标签编码')
plt.legend()
plt.grid(True)
plt.show()

# ===================== 7. 模型保存与加载 =====================
def save_model(model, filepath='behavior_lstm_pytorch.pth'):
    """保存PyTorch模型"""
    torch.save({
        'model_state_dict': model.state_dict(),
        'input_size': input_size,
        'hidden_size': hidden_size,
        'num_layers': num_layers,
        'num_classes': num_classes,
        'scaler': scaler  # 保存归一化器，预测时需要
    }, filepath)
    print(f"\n模型已保存到: {filepath}")

# 保存模型
save_model(model)

# 加载模型示例（后续预测用）
def load_model(filepath='behavior_lstm_pytorch.pth'):
    checkpoint = torch.load(filepath)
    model = BehaviorLSTM(
        input_size=checkpoint['input_size'],
        hidden_size=checkpoint['hidden_size'],
        num_layers=checkpoint['num_layers'],
        num_classes=checkpoint['num_classes']
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    scaler = checkpoint['scaler']
    return model, scaler

# 加载模型（示例）
# loaded_model, loaded_scaler = load_model()