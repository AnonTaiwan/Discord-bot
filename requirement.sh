#!/bin/bash

# 設定顏色輸出（增加可讀性）
GREEN='\033[0;32m'
NC='\033[0m' # 無顏色

echo -e "${GREEN}==> 開始初始化 Python 環境...${NC}"

# 1. 檢查是否存在 requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "錯誤: 找不到 requirements.txt，請確保它在專案根目錄。"
    exit 1
fi

# 2. 建立虛擬環境資料夾 (名為 .venv)
if [ ! -d ".venv" ]; then
    echo -e "${GREEN}==> 正在建立虛擬環境 (.venv)...${NC}"
    python3 -m venv .venv
else
    echo -e "${GREEN}==> 虛擬環境已存在，跳過建立步驟。${NC}"
fi

# 3. 啟動虛擬環境並安裝套件
echo -e "${GREEN}==> 正在升級 pip 並安裝 Library...${NC}"
source .venv/bin/activate

# 確保 pip 是最新的
pip install --upgrade pip

# 安裝 requirements.txt 中的套件
pip install -r requirements.txt

echo -e "${GREEN}==> 設定完成！${NC}"
echo -e "${GREEN}==> 使用 'source .venv/bin/activate' 來啟動環境。${NC}"