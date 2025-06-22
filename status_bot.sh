#!/bin/bash

# Facebook Bot 狀態檢查腳本

echo "=== Facebook Bot 狀態檢查 ==="

# 查找 bot 進程
BOT_PID=$(pgrep -f "python.*bot.py")

if [ -z "$BOT_PID" ]; then
    echo "❌ Bot 未運行"
    exit 1
fi

echo "✅ Bot 正在運行"
echo "進程 ID: $BOT_PID"

# 檢查進程運行時間
if command -v ps > /dev/null; then
    UPTIME=$(ps -o etime= -p $BOT_PID 2>/dev/null)
    if [ ! -z "$UPTIME" ]; then
        echo "運行時間: $UPTIME"
    fi
fi

# 檢查記憶體使用
if command -v ps > /dev/null; then
    MEMORY=$(ps -o rss= -p $BOT_PID 2>/dev/null)
    if [ ! -z "$MEMORY" ]; then
        MEMORY_MB=$((MEMORY / 1024))
        echo "記憶體使用: ${MEMORY_MB}MB"
    fi
fi

# 檢查日誌文件
TODAY=$(date +%Y%m%d)
LOG_FILE="logs/fb_bot_${TODAY}.log"

if [ -f "$LOG_FILE" ]; then
    echo "今日日誌文件: $LOG_FILE"
    LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
    echo "日誌文件大小: $LOG_SIZE"
    
    # 顯示最後幾行日誌
    echo ""
    echo "=== 最近的日誌 ==="
    tail -5 "$LOG_FILE"
else
    echo "今日日誌文件不存在"
fi

# 檢查標準輸出日誌
STDOUT_LOG="logs/bot_stdout.log"
if [ -f "$STDOUT_LOG" ]; then
    echo ""
    echo "=== 標準輸出日誌 ==="
    tail -3 "$STDOUT_LOG"
fi

echo ""
echo "使用以下命令查看完整日誌："
echo "python view_logs.py view --file fb_bot_${TODAY}.log --follow" 