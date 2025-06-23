# Facebook Bot 項目結構說明

## 📁 目錄結構

```
Anon-Taiwan/
├── 📄 核心文件
│   ├── bot.py                    # Discord Bot 主程式
│   ├── requirements.txt          # Python 依賴列表
│   └── .gitignore               # Git 忽略文件
│
├── 📁 cog/                      # Discord Bot 擴展模組
│   └── fb.py                    # Facebook 監控模組
│
├── 📁 logs/                     # 日誌文件目錄
│   └── fb_bot_YYYYMMDD.log      # 日誌文件（按日期）
│
├── 🛠️ 常用管理腳本（根目錄）
│   ├── manage.sh                # 🎯 統一管理工具（推薦使用）
│   ├── start_bot.sh             # 啟動 Bot
│   ├── stop_bot.sh              # 停止 Bot
│   ├── restart_bot.sh           # 重啟 Bot
│   └── status_bot.sh            # 檢查狀態
│
├── 📁 scripts/                  # 工具腳本目錄
│   ├── 📄 README.md             # 腳本使用說明
│   │
│   ├── 📁 tools/                # 維護工具
│   │   ├── python_runner.sh     # Python 腳本執行器
│   │   ├── view_logs.py         # 日誌查看工具
│   │   └── cleanup_project.sh   # 專案清理工具
│   │
│   ├── 📁 setup/                # 設置工具
│   │   ├── setup_env.sh         # 環境設置腳本
│   │   ├── start_bot_screen.sh  # Screen 啟動腳本
│   │   └── facebook-bot.service # Systemd 服務文件
│   │
│   └── 📁 check/                # 檢查工具
│       ├── check_environment.sh # 完整環境檢查
│       ├── check_setup.sh       # 基本設置檢查
│       └── check_pycord.sh      # py-cord 專用檢查
│
└── 📄 文檔
    ├── QUICK_START.md           # 快速開始指南
    ├── DEPLOYMENT_GUIDE.md      # 部署指南
    ├── README_LOGS.md           # 日誌系統說明
    └── PROJECT_STRUCTURE.md     # 本文件
```

## 🎯 推薦使用方式

### 統一管理工具（最簡單）
```bash
# 基本操作
./manage.sh start     # 啟動 Bot
./manage.sh stop      # 停止 Bot
./manage.sh restart   # 重啟 Bot
./manage.sh status    # 檢查狀態

# 環境管理
./manage.sh setup     # 環境設置
./manage.sh check     # 完整檢查
./manage.sh check-env # 基本檢查
./manage.sh check-py  # py-cord 檢查

# 日誌管理
./manage.sh logs list                    # 列出日誌
./manage.sh logs view --file xxx.log     # 查看日誌
./manage.sh logs view --file xxx.log --follow  # 實時跟蹤
./manage.sh logs search --file xxx.log --keyword 錯誤  # 搜索
./manage.sh logs clean                   # 清理舊日誌

# 維護工具
./manage.sh cleanup   # 清理專案
./manage.sh python    # 運行 Python 腳本

# 幫助
./manage.sh help      # 顯示幫助
```

### 直接使用腳本（進階）
```bash
# 常用腳本（根目錄）
./start_bot.sh
./stop_bot.sh
./restart_bot.sh
./status_bot.sh

# 工具腳本
./scripts/tools/view_logs.py --help
./scripts/setup/setup_env.sh
./scripts/check/check_environment.sh
```

## 🔧 腳本功能說明

### 根目錄腳本
- **`manage.sh`**: 統一管理工具，提供所有功能的便捷介面
- **`start_bot.sh`**: 啟動 Bot（支援虛擬環境）
- **`stop_bot.sh`**: 停止 Bot
- **`restart_bot.sh`**: 重啟 Bot
- **`status_bot.sh`**: 檢查 Bot 運行狀態

### 工具腳本 (`scripts/tools/`)
- **`python_runner.sh`**: 通用 Python 腳本執行器，自動檢測虛擬環境
- **`view_logs.py`**: 日誌查看和管理工具，支援查看、搜索、清理
- **`cleanup_project.sh`**: 專案清理工具，清理臨時文件和緩存

### 設置腳本 (`scripts/setup/`)
- **`setup_env.sh`**: 環境設置腳本，自動創建虛擬環境並安裝依賴
- **`start_bot_screen.sh`**: 使用 screen 會話啟動 Bot
- **`facebook-bot.service`**: systemd 服務文件，用於系統級管理

### 檢查腳本 (`scripts/check/`)
- **`check_environment.sh`**: 完整環境檢查，包括系統、Python、網路等
- **`check_setup.sh`**: 基本設置檢查，檢查 Python、套件、Token 等
- **`check_pycord.sh`**: py-cord 專用檢查，測試 Discord 功能

## 📝 使用建議

### 日常使用
1. **啟動 Bot**: `./manage.sh start`
2. **檢查狀態**: `./manage.sh status`
3. **查看日誌**: `./manage.sh logs view --file fb_bot_$(date +%Y%m%d).log --follow`
4. **停止 Bot**: `./manage.sh stop`

### 故障排除
1. **環境檢查**: `./manage.sh check`
2. **重新設置**: `./manage.sh setup`
3. **查看錯誤**: `./manage.sh logs search --keyword 錯誤`

### 維護工作
1. **清理日誌**: `./manage.sh logs clean`
2. **清理專案**: `./manage.sh cleanup`
3. **更新依賴**: `./manage.sh setup`

## 🚀 快速開始

1. **首次設置**:
   ```bash
   ./manage.sh setup
   ./manage.sh check
   ```

2. **設置 Token**:
   在 `bot.py` 中設置 Discord Token

3. **啟動 Bot**:
   ```bash
   ./manage.sh start
   ```

4. **監控運行**:
   ```bash
   ./manage.sh status
   ./manage.sh logs view --file fb_bot_$(date +%Y%m%d).log --follow
   ```

## 📚 相關文檔

- **`QUICK_START.md`**: 詳細的快速開始指南
- **`DEPLOYMENT_GUIDE.md`**: 部署到服務器的完整指南
- **`README_LOGS.md`**: 日誌系統的詳細說明
- **`scripts/README.md`**: 腳本工具的詳細說明 