# Scripts 目錄

這個目錄包含了 Facebook Bot 專案的各種腳本工具，按功能分類組織。

## 目錄結構

### `/tools/` - 維護工具
- `python_runner.sh` - 通用 Python 腳本執行器
- `view_logs.py` - 日誌查看和管理工具
- `cleanup_project.sh` - 專案清理工具

### `/setup/` - 設置工具
- `setup_env.sh` - 環境設置腳本
- `start_bot_screen.sh` - 使用 screen 啟動 Bot
- `facebook-bot.service` - systemd 服務文件

### `/check/` - 檢查工具
- `check_environment.sh` - 完整環境檢查
- `check_setup.sh` - 基本設置檢查
- `check_pycord.sh` - py-cord 專用檢查

## 使用方式

### 推薦使用管理腳本
根目錄的 `manage.sh` 提供了便捷的統一介面：

```bash
# 常用命令
./manage.sh start
./manage.sh stop
./manage.sh restart
./manage.sh status

# 環境檢查
./manage.sh check
./manage.sh check-env
./manage.sh check-py

# 設置工具
./manage.sh setup
./manage.sh screen
./manage.sh systemd

# 維護工具
./manage.sh logs
./manage.sh cleanup
./manage.sh python
```

### 直接調用
也可以直接調用特定腳本：

```bash
# 工具
./scripts/tools/view_logs.py --help
./scripts/tools/cleanup_project.sh

# 設置
./scripts/setup/setup_env.sh

# 檢查
./scripts/check/check_environment.sh
```

## 注意事項

1. 所有腳本都支持虛擬環境自動檢測
2. 檢查腳本會提供詳細的診斷信息
3. 工具腳本包含錯誤處理和日誌記錄
4. 設置腳本會自動處理依賴安裝 