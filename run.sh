#!/bin/bash
# iyf.tv 爬虫启动脚本

echo "========================================="
echo "  iyf.tv 爬虫服务启动脚本"
echo "========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖包..."
pip install -r requirements.txt

# 启动服务
echo ""
echo "🚀 启动爬虫服务..."
echo "========================================="
python3 iyf_spider.py
