# Facebook Bot 快速開始指南

## 🚀 一鍵設置（推薦）

### 1. 環境設置
```bash
# 運行環境設置腳本（會自動檢測或創建虛擬環境）
./manage.sh setup
```

這個腳本會：
- ✅ 自動檢測現有虛擬環境
- ✅ 如果沒有，詢問是否創建新的虛擬環境
- ✅ 自動安裝所需套件（包括 py-cord）
- ✅ 生成環境配置文件

### 2. 完整環境檢查
```bash
# 運行完整環境檢查（推薦）
./manage.sh check
```

這個腳本會檢查：
- ✅ Python 版本和環境
- ✅ 系統依賴（curl, wget, git 等）
- ✅ Python 套件（py-cord, requests, beautifulsoup4 等）
- ✅ 網路連接（Discord, Facebook）
- ✅ 文件權限和系統資源
- ✅ 基本功能測試

### 3. 設置 Discord Token
在 `bot.py` 中設置您的 Discord Token：
```python
bot.run("your_discord_token_here")
```

### 4. 檢查設置
```bash
# 檢查基本設置
./manage.sh check-env

# 檢查 py-cord 設置
./manage.sh check-py
```

### 5. 啟動 Bot
```bash
# 啟動 Bot（會自動使用虛擬環境）
./manage.sh start
```

## 📋 管理命令

### 基本操作
```bash
./manage.sh start     # 啟動 Bot
./manage.sh status    # 檢查狀態
./manage.sh stop      # 停止 Bot
./manage.sh restart   # 重啟 Bot
```

### 環境檢查
```bash
./manage.sh check     # 完整環境檢查
./manage.sh check-env # 基本設置檢查
./manage.sh check-py  # py-cord 專用檢查
```

### 專案維護
```bash
./manage.sh cleanup   # 清理專案文件
./manage.sh setup     # 重新設置環境
```

### 日誌查看
```bash
# 列出所有日誌文件
./manage.sh logs list

# 查看今天的日誌
./manage.sh logs view --file fb_bot_$(date +%Y%m%d).log

# 實時跟蹤日誌
./manage.sh logs view --file fb_bot_$(date +%Y%m%d).log --follow

# 搜索日誌
./manage.sh logs search --file fb_bot_$(date +%Y%m%d).log --keyword 錯誤

# 清理舊日誌
./manage.sh logs clean
```

## 🔧 虛擬環境支持

### 自動檢測
腳本會自動檢測以下虛擬環境：
- ✅ 當前激活的虛擬環境
- ✅ `./venv/` 目錄
- ✅ `./.venv/` 目錄
- ✅ `./env/` 目錄
- ✅ 系統 Python（如果沒有虛擬環境）

### 手動創建虛擬環境
如果您想手動創建：
```bash
# 創建虛擬環境
python3 -m venv venv

# 激活虛擬環境
source venv/bin/activate

# 安裝依賴（使用 py-cord）
pip install py-cord requests beautifulsoup4 lxml html5lib
```

## 🐛 故障排除

### 常見問題

1. **找不到 Python**
   ```bash
   # 檢查 Python 版本
   python3 --version
   
   # 或運行環境設置
   ./manage.sh setup
   ```

2. **缺少套件**
   ```bash
   # 自動安裝
   ./manage.sh setup
   
   # 或手動安裝（注意使用 py-cord）
   pip install py-cord requests beautifulsoup4 lxml html5lib
   ```

3. **權限問題**
   ```bash
   # 添加執行權限
   chmod +x *.sh
   ```

4. **虛擬環境問題**
   ```bash
   # 檢查虛擬環境狀態
   ./manage.sh logs --check-env
   
   # 重新設置環境
   ./manage.sh setup
   ```

5. **py-cord 相關問題**
   ```bash
   # 檢查 py-cord 版本
   python3 -c "import discord; print(discord.__version__)"
   
   # 重新安裝 py-cord
   pip uninstall py-cord
   pip install py-cord
   ```

6. **網路連接問題**
   ```bash
   # 運行完整環境檢查
   ./manage.sh check
   
   # 檢查防火牆設置
   sudo ufw status
   ```

### 檢查 Bot 狀態
```bash
# 檢查是否運行
./manage.sh status

# 查看進程
ps aux | grep python | grep bot.py

# 查看日誌
./manage.sh logs view --file fb_bot_$(date +%Y%m%d).log --follow
```

## 📝 日誌說明

### 日誌文件位置
- `logs/bot_stdout.log` - Bot 標準輸出
- `logs/fb_bot_YYYYMMDD.log` - Facebook 監控日誌

### 日誌級別
- **INFO**: 一般信息
- **WARNING**: 警告信息
- **ERROR**: 錯誤信息

## 🔄 自動化建議

### 設置自動清理日誌
```bash
# 編輯 crontab
crontab -e

# 添加以下行（每天凌晨2點清理7天前的日誌）
0 2 * * * cd /path/to/your/bot && ./manage.sh logs clean --days 7
```

### 設置開機自啟動
如果您使用 systemd，可以參考 `DEPLOYMENT_GUIDE.md` 中的 systemd 方式。

## 💡 使用技巧

1. **安全關閉 SSH**
   - 啟動 Bot 後，可以安全地關閉 SSH 窗口
   - Bot 會在背景持續運行

2. **監控運行狀況**
   - 定期檢查 `./manage.sh status`
   - 查看日誌了解運行狀況

3. **備份重要文件**
   - 備份 `bot.py` 和 `cog/fb.py`
   - 定期備份日誌文件

4. **py-cord 特色功能**
   - 您的 Bot 使用了 py-cord 的 `bridge` 功能
   - 支持斜線命令和傳統命令
   - 更好的錯誤處理和調試信息

5. **定期維護**
   - 使用 `./manage.sh cleanup` 清理專案
   - 定期更新套件版本
   - 監控系統資源使用

## 🆘 緊急情況

### 強制停止
```bash
# 強制終止所有 Bot 進程
pkill -f "python.*bot.py"

# 或更強制的方式
pkill -9 -f "python.*bot.py"
```

### 重新部署
```bash
# 停止 Bot
./manage.sh stop

# 檢查設置
./manage.sh check

# 重新啟動
./manage.sh start
```

## 📞 需要幫助？

如果遇到問題：
1. 運行 `./manage.sh check` 進行完整檢查
2. 查看日誌文件了解錯誤
3. 檢查虛擬環境狀態
4. 確認 py-cord 版本和安裝
5. 參考 `DEPLOYMENT_GUIDE.md` 獲取詳細說明

## 🔍 py-cord 相關信息

### 版本檢查
```bash
python3 -c "import discord; print(f'py-cord 版本: {discord.__version__}')"
```

### 特色功能
- ✅ 斜線命令支持
- ✅ Bridge 命令系統
- ✅ 更好的錯誤處理
- ✅ 增強的調試功能
- ✅ 與 discord.py 完全兼容的 API

## 📦 套件說明

### 核心套件
- **py-cord**: Discord Bot 框架
- **requests**: HTTP 請求庫
- **beautifulsoup4**: HTML 解析庫

### 可選套件（提升性能）
- **lxml**: 更快的 XML/HTML 解析器
- **html5lib**: HTML5 解析器

### 安裝所有套件
```bash
pip install -r requirements.txt
``` 