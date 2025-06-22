#!/bin/bash

# Facebook Bot Screen 啟動腳本
# 使用 screen 創建一個持久的會話

SCREEN_NAME="facebook_bot"

echo "正在啟動 Facebook Bot (Screen 模式)..."

# 檢查 screen 是否已安裝
if ! command -v screen &> /dev/null; then
    echo "❌ screen 未安裝，請先安裝："
    echo "Ubuntu/Debian: sudo apt-get install screen"
    echo "CentOS/RHEL: sudo yum install screen"
    exit 1
fi

# 檢查是否已經有同名的 screen 會話
if screen -list | grep -q "$SCREEN_NAME"; then
    echo "❌ Screen 會話 '$SCREEN_NAME' 已存在"
    echo "使用以下命令連接到會話："
    echo "screen -r $SCREEN_NAME"
    echo ""
    echo "或使用以下命令終止現有會話："
    echo "screen -S $SCREEN_NAME -X quit"
    exit 1
fi

# 創建 logs 目錄
mkdir -p logs

# 創建新的 screen 會話並運行 bot
echo "創建新的 screen 會話..."
screen -dmS $SCREEN_NAME bash -c "
    echo 'Bot 在 screen 會話中啟動...'
    python3 bot.py
    echo 'Bot 已停止，按任意鍵關閉會話...'
    read
"

# 等待一下確保會話創建成功
sleep 2

# 檢查會話是否創建成功
if screen -list | grep -q "$SCREEN_NAME"; then
    echo "✅ Bot 已在 screen 會話中啟動！"
    echo "會話名稱: $SCREEN_NAME"
    echo ""
    echo "管理命令："
    echo "  連接到會話: screen -r $SCREEN_NAME"
    echo "  查看會話列表: screen -list"
    echo "  終止會話: screen -S $SCREEN_NAME -X quit"
    echo "  分離會話: Ctrl+A, 然後按 D"
    echo ""
    echo "您現在可以安全地關閉 SSH 窗口"
    echo "Bot 會在背景持續運行"
else
    echo "❌ 無法創建 screen 會話"
    exit 1
fi 