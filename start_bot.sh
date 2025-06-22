#!/bin/bash

# Facebook Bot 啟動腳本
# 使用 nohup 在背景運行，即使 SSH 斷開也不會停止
# 自動檢測和使用虛擬環境

# 載入 Python 執行器
source "$(dirname "$0")/python_runner.sh"

echo "正在啟動 Facebook Bot..."

# 檢查是否已經在運行
if pgrep -f "python.*bot.py" > /dev/null; then
    echo "Bot 已經在運行中！"
    echo "進程 ID: $(pgrep -f 'python.*bot.py')"
    exit 1
fi

# 創建 logs 目錄
mkdir -p logs

# 獲取 Python 路徑
PYTHON_PATH=$(get_python_path)
if [ $? -ne 0 ]; then
    echo "❌ 無法找到 Python 解釋器"
    exit 1
fi

echo "使用 Python: $PYTHON_PATH"

# 檢查虛擬環境狀態
check_venv_status

# 使用 nohup 在背景運行
echo "正在啟動 Bot..."
nohup $PYTHON_PATH bot.py > logs/bot_stdout.log 2>&1 &

# 獲取進程 ID
BOT_PID=$!

# 等待一下確保程式啟動
sleep 3

# 檢查程式是否成功啟動
if kill -0 $BOT_PID 2>/dev/null; then
    echo "✅ Bot 已成功啟動！"
    echo "進程 ID: $BOT_PID"
    echo "日誌文件: logs/bot_stdout.log"
    echo "Facebook 監控日誌: logs/fb_bot_$(date +%Y%m%d).log"
    echo ""
    echo "您現在可以安全地關閉 SSH 窗口"
    echo "使用 'python view_logs.py view --file fb_bot_$(date +%Y%m%d).log --follow' 來監控運行狀況"
else
    echo "❌ Bot 啟動失敗！"
    echo "請檢查 logs/bot_stdout.log 中的錯誤信息"
    exit 1
fi 