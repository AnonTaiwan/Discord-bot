#!/bin/bash

# Facebook Bot 重啟腳本

echo "正在重啟 Facebook Bot..."

# 檢查啟動和停止腳本是否存在
if [ ! -f "stop_bot.sh" ] || [ ! -f "start_bot.sh" ]; then
    echo "❌ 缺少必要的腳本文件"
    exit 1
fi

# 停止 bot
echo "步驟 1: 停止 Bot..."
./stop_bot.sh

# 等待一下確保完全停止
sleep 2

# 檢查是否真的停止了
if pgrep -f "python.*bot.py" > /dev/null; then
    echo "❌ Bot 未能完全停止，強制終止..."
    pkill -f "python.*bot.py"
    sleep 1
fi

# 啟動 bot
echo "步驟 2: 啟動 Bot..."
./start_bot.sh

# 檢查啟動結果
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Bot 重啟成功！"
    echo "使用 './status_bot.sh' 檢查運行狀況"
else
    echo "❌ Bot 重啟失敗！"
    exit 1
fi 