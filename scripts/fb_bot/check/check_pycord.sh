#!/bin/bash

# py-cord 設置檢查腳本

echo "=== py-cord 設置檢查 ==="
echo ""

# 載入 Python 執行器
source "$(dirname "$0")/python_runner.sh"

# 獲取 Python 路徑
PYTHON_PATH=$(get_python_path)
if [ $? -ne 0 ]; then
    echo "❌ 無法找到 Python 解釋器"
    exit 1
fi

echo "使用 Python: ${PYTHON_PATH}"
check_venv_status

echo ""

# 檢查 py-cord 安裝
echo "1. 檢查 py-cord 安裝..."
if ${PYTHON_PATH} -c "import discord" 2>/dev/null; then
    VERSION=$(${PYTHON_PATH} -c "import discord; print(discord.__version__)" 2>/dev/null)
    echo "✅ py-cord 已安裝，版本: ${VERSION}"
else
    echo "❌ py-cord 未安裝"
    echo "請運行: pip install py-cord"
    exit 1
fi

# 檢查 py-cord 功能
echo ""
echo "2. 檢查 py-cord 功能..."

# 檢查 bridge 功能
if ${PYTHON_PATH} -c "from discord.ext import bridge" 2>/dev/null; then
    echo "✅ Bridge 功能可用"
else
    echo "❌ Bridge 功能不可用"
fi

# 檢查 commands 功能
if ${PYTHON_PATH} -c "from discord.ext import commands" 2>/dev/null; then
    echo "✅ Commands 功能可用"
else
    echo "❌ Commands 功能不可用"
fi

# 檢查 tasks 功能
if ${PYTHON_PATH} -c "from discord.ext import tasks" 2>/dev/null; then
    echo "✅ Tasks 功能可用"
else
    echo "❌ Tasks 功能不可用"
fi

# 檢查基本 Discord 功能
echo ""
echo "3. 檢查 Discord 基本功能..."
if ${PYTHON_PATH} -c "import discord; print('Discord Intents:', discord.Intents.all())" 2>/dev/null; then
    echo "✅ Discord Intents 功能正常"
else
    echo "❌ Discord Intents 功能異常"
fi

if ${PYTHON_PATH} -c "import discord; print('Discord Embed:', discord.Embed)" 2>/dev/null; then
    echo "✅ Discord Embed 功能正常"
else
    echo "❌ Discord Embed 功能異常"
fi

if ${PYTHON_PATH} -c "import discord; print('Discord File:', discord.File)" 2>/dev/null; then
    echo "✅ Discord File 功能正常"
else
    echo "❌ Discord File 功能異常"
fi

# 檢查 Bot 代碼兼容性
echo ""
echo "4. 檢查 Bot 代碼兼容性..."

# 檢查 bot.py 導入
if grep -q "import discord" bot.py && grep -q "from discord.ext import commands" bot.py; then
    echo "✅ bot.py 導入語句正確"
else
    echo "❌ bot.py 導入語句可能有問題"
fi

# 檢查 cog/fb.py 導入
if grep -q "import discord" cog/fb.py && grep -q "from discord.ext import commands, bridge, tasks" cog/fb.py; then
    echo "✅ cog/fb.py 導入語句正確"
else
    echo "❌ cog/fb.py 導入語句可能有問題"
fi

# 測試基本 Discord 功能
echo ""
echo "5. 測試基本 Discord 功能..."
${PYTHON_PATH} -c "
import discord
from discord.ext import commands

# 測試 Bot 創建
try:
    intents = discord.Intents.all()
    bot = commands.Bot(intents=intents)
    print('✅ Bot 創建成功')
except Exception as e:
    print(f'❌ Bot 創建失敗: {e}')

# 測試 Embed 創建
try:
    embed = discord.Embed(title='測試', description='測試描述')
    print('✅ Embed 創建成功')
except Exception as e:
    print(f'❌ Embed 創建失敗: {e}')

# 測試 Bridge Bot
try:
    from discord.ext import bridge
    bridge_bot = bridge.Bot(intents=intents)
    print('✅ Bridge Bot 創建成功')
except Exception as e:
    print(f'❌ Bridge Bot 創建失敗: {e}')
"

echo ""
echo "=== py-cord 檢查完成 ==="
echo ""
echo "如果所有檢查都通過，您的 py-cord 設置正確！"
echo ""
echo "py-cord 特色功能："
echo "- 斜線命令支持"
echo "- Bridge 命令系統"
echo "- 更好的錯誤處理"
echo "- 增強的調試功能"
echo "- 與 discord.py 完全兼容的 API" 