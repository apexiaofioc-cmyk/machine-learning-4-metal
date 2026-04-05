# Machine Learning for Metal
使用机器学习通过声音预测金属的杨氏模量
## 1. 核心功能
- [x] 数据获取
- [x] 训练模型
- [x] 盲测
## 2. 快速开始 
### 环境要求
- Python 3.11.x
### 安装步骤
```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/machine-learning-4-metal.git
# 2. 进入目录
cd machine-learning-4-metal
# 3. 安装依赖包
#建议先创建虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
#4.开始录制
请尽量录制时长相近的短片段以保证训练效果
#ui界面需要用到主题包

#启动虚拟环境
.venv\Scripts\Activate.ps1