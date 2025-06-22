#!/bin/bash

# Facebook Bot 停止腳本

echo "正在停止 Facebook Bot..."

# 查找 bot 進程
BOT_PID=$(pgrep -f "python.*bot.py")

if [ -z "$BOT_PID" ]; then
    echo "❌ 沒有找到運行中的 Bot 進程"
    exit 1
fi

echo "找到 Bot 進程 ID: $BOT_PID"

# 優雅地停止進程
echo "正在發送停止信號..."
kill -TERM $BOT_PID

# 等待進程停止
echo "等待進程停止..."
for i in {1..10}; do
    if ! kill -0 $BOT_PID 2>/dev/null; then
        echo "✅ Bot 已成功停止"
        exit 0
    fi
    sleep 1
done

# 如果優雅停止失敗，強制終止
echo "優雅停止失敗，強制終止進程..."
kill -KILL $BOT_PID

if ! kill -0 $BOT_PID 2>/dev/null; then
    echo "✅ Bot 已強制停止"
else
    echo "❌ 無法停止 Bot"
    exit 1
fi 