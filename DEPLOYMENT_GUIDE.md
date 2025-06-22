# Facebook Bot 部署指南

## 概述

本指南提供三種不同的部署方式，讓您可以優雅地管理 Facebook Bot 的運行：

1. **nohup 方式** - 簡單易用
2. **Screen 方式** - 靈活互動
3. **Systemd 方式** - 專業服務

## 重要說明：py-cord 支持

本 Bot 使用 **py-cord** 而不是官方的 discord.py。py-cord 提供了：
- ✅ 與 discord.py 完全兼容的 API
- ✅ 斜線命令支持
- ✅ Bridge 命令系統
- ✅ 更好的錯誤處理和調試功能

### py-cord 檢查
```bash
# 檢查 py-cord 設置
./check_pycord.sh

# 檢查 py-cord 版本
python -c "import discord; print(discord.__version__)"
```

## 方案一：nohup 方式（推薦新手）

### 優點
- 簡單易用
- 不需要額外軟體
- 適合快速部署

### 使用方法

```bash
# 啟動 Bot
./start_bot.sh

# 檢查狀態
./status_bot.sh

# 停止 Bot
./stop_bot.sh

# 重啟 Bot
./restart_bot.sh
```

### 特點
- 使用 `nohup` 在背景運行
- 自動檢查是否已運行
- 提供詳細的狀態信息
- 優雅地停止進程

## 方案二：Screen 方式（推薦進階用戶）

### 優點
- 可以隨時連接到會話
- 支持互動式操作
- 會話持久化

### 安裝 screen（如果需要）
```bash
# Ubuntu/Debian
sudo apt-get install screen

# CentOS/RHEL
sudo yum install screen
```

### 使用方法

```bash
# 啟動 Bot
./start_bot_screen.sh

# 連接到會話
screen -r facebook_bot

# 查看所有會話
screen -list

# 終止會話
screen -S facebook_bot -X quit
```

### Screen 快捷鍵
- `Ctrl+A, D` - 分離會話（保持運行）
- `Ctrl+A, K` - 終止會話
- `Ctrl+A, ?` - 顯示幫助

## 方案三：Systemd 方式（推薦生產環境）

### 優點
- 系統級服務管理
- 自動重啟
- 開機自啟動
- 專業的日誌管理

### 安裝步驟

1. **複製服務文件**
```bash
sudo cp facebook-bot.service /etc/systemd/system/
```

2. **修改服務文件**
編輯 `/etc/systemd/system/facebook-bot.service`，修改以下路徑：
```ini
User=your_username
WorkingDirectory=/path/to/your/bot
ExecStart=/usr/bin/python3 /path/to/your/bot/bot.py
```

3. **重新載入 systemd**
```bash
sudo systemctl daemon-reload
```

4. **啟用服務**
```bash
sudo systemctl enable facebook-bot.service
```

### 使用方法

```bash
# 啟動服務
sudo systemctl start facebook-bot

# 檢查狀態
sudo systemctl status facebook-bot

# 停止服務
sudo systemctl stop facebook-bot

# 重啟服務
sudo systemctl restart facebook-bot

# 查看日誌
sudo journalctl -u facebook-bot -f
```

## 日誌管理

### 查看日誌
```bash
# 查看今天的 Facebook 監控日誌
TODAY=$(date +%Y%m%d)
python view_logs.py view --file fb_bot_${TODAY}.log

# 實時跟蹤日誌
python view_logs.py view --file fb_bot_${TODAY}.log --follow

# 搜索錯誤
python view_logs.py search --file fb_bot_${TODAY}.log --keyword 錯誤
```

### 自動清理日誌
```bash
# 設置 cron 任務（每天凌晨2點清理7天前的日誌）
crontab -e

# 添加以下行
0 2 * * * cd /path/to/your/bot && python view_logs.py clean --days 7
```

## 故障排除

### 檢查 Bot 是否運行
```bash
# 方法1：使用狀態腳本
./status_bot.sh

# 方法2：檢查進程
ps aux | grep python | grep bot.py

# 方法3：檢查端口（如果使用）
netstat -tlnp | grep python
```

### 常見問題

1. **Bot 無法啟動**
   - 檢查 Python 版本：`python3 --version`
   - 檢查依賴：`pip3 list | grep discord`
   - 檢查權限：`ls -la bot.py`

2. **Bot 啟動後立即停止**
   - 檢查 Discord Token 是否設置
   - 檢查網路連接
   - 查看錯誤日誌

3. **日誌文件不更新**
   - 檢查 `logs/` 目錄權限
   - 檢查磁盤空間：`df -h`
   - 檢查 Python 進程是否運行

### 緊急停止
```bash
# 強制終止所有 Python bot 進程
pkill -f "python.*bot.py"

# 或使用更強制的方式
pkill -9 -f "python.*bot.py"
```

## 安全建議

1. **防火牆設置**
   - 只開放必要的 SSH 端口
   - 限制訪問來源 IP

2. **用戶權限**
   - 使用專用用戶運行 Bot
   - 限制文件系統權限

3. **定期備份**
   - 備份配置文件和日誌
   - 設置自動備份腳本

4. **監控設置**
   - 設置磁盤空間監控
   - 設置進程監控
   - 設置網路連接監控

## 推薦部署流程

1. **選擇部署方式**
   - 新手：使用 nohup 方式
   - 進階用戶：使用 screen 方式
   - 生產環境：使用 systemd 方式

2. **測試部署**
   - 在測試環境先試運行
   - 確認所有功能正常

3. **監控設置**
   - 設置日誌監控
   - 設置自動清理
   - 設置備份策略

4. **正式部署**
   - 按照選擇的方式部署
   - 確認服務正常運行
   - 設置監控告警

## 聯繫支持

如果遇到問題，請：
1. 檢查日誌文件
2. 查看錯誤信息
3. 確認系統環境
4. 提供詳細的錯誤描述 