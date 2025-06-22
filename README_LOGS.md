# Facebook Bot 日誌系統使用說明

## 概述

Facebook Bot 現在配備了完整的日誌系統，可以記錄所有重要的運行信息，方便您通過 SSH 遠程監控程式運行狀況。

## 日誌文件位置

日誌文件保存在 `logs/` 目錄中，文件名格式為：
```
fb_bot_YYYYMMDD.log
```

例如：`fb_bot_20241201.log`

## 日誌內容

日誌會記錄以下信息：
- 程式啟動和初始化
- Facebook 數據獲取狀態
- 新貼文檢測
- Discord 消息發送
- Cookies 更新
- 錯誤和警告信息

## 日誌查看工具

我們提供了一個專門的日誌查看工具 `view_logs.py`，支持多種操作：

### 1. 列出所有日誌文件
```bash
python view_logs.py list
```

### 2. 查看日誌文件
```bash
# 查看最後 50 行
python view_logs.py view --file fb_bot_20241201.log

# 查看最後 100 行
python view_logs.py view --file fb_bot_20241201.log --lines 100

# 實時跟蹤日誌（類似 tail -f）
python view_logs.py view --file fb_bot_20241201.log --follow
```

### 3. 搜索日誌
```bash
# 搜索包含 "錯誤" 的行
python view_logs.py search --file fb_bot_20241201.log --keyword 錯誤

# 搜索包含 "新貼文" 的行
python view_logs.py search --file fb_bot_20241201.log --keyword 新貼文
```

### 4. 清理舊日誌
```bash
# 清理 7 天前的日誌（預設）
python view_logs.py clean

# 清理 30 天前的日誌
python view_logs.py clean --days 30
```

## 常用命令示例

### 查看今天的日誌
```bash
# 獲取今天的日期
TODAY=$(date +%Y%m%d)
python view_logs.py view --file fb_bot_${TODAY}.log
```

### 實時監控程式運行
```bash
# 實時跟蹤今天的日誌
TODAY=$(date +%Y%m%d)
python view_logs.py view --file fb_bot_${TODAY}.log --follow
```

### 搜索錯誤信息
```bash
# 搜索所有日誌文件中的錯誤
for log in logs/fb_bot_*.log; do
    echo "=== $log ==="
    python view_logs.py search --file $(basename $log) --keyword 錯誤
done
```

## 日誌級別

日誌包含以下級別：
- **INFO**: 一般信息（程式啟動、新貼文檢測等）
- **WARNING**: 警告信息（無法獲取數據、模式匹配失敗等）
- **ERROR**: 錯誤信息（網路錯誤、JSON 解析錯誤等）
- **DEBUG**: 調試信息（詳細的調試數據）

## 日誌格式

每行日誌的格式為：
```
2024-12-01 14:30:25 - INFO - 開始初始化 Facebook 監控...
```

包含：
- 時間戳
- 日誌級別
- 具體信息

## 故障排除

### 如果看不到日誌文件
1. 確保程式已經運行過
2. 檢查 `logs/` 目錄是否存在
3. 檢查程式是否有寫入權限

### 如果日誌文件太大
1. 使用 `clean` 命令清理舊日誌
2. 定期備份重要的日誌文件

### 如果日誌內容不完整
1. 檢查磁盤空間
2. 檢查程式是否正常運行
3. 查看是否有權限問題

## 自動化建議

您可以設置 cron 任務來自動清理舊日誌：

```bash
# 編輯 crontab
crontab -e

# 添加以下行（每天凌晨 2 點清理 7 天前的日誌）
0 2 * * * cd /path/to/your/bot && python view_logs.py clean --days 7
```

## 注意事項

1. 日誌文件會持續增長，建議定期清理
2. 日誌包含敏感信息，請妥善保管
3. 在生產環境中，建議設置日誌輪轉
4. 如果程式崩潰，日誌文件可能不會正確關閉

## 聯繫支持

如果您在使用日誌系統時遇到問題，請檢查：
1. Python 版本是否支持（建議 3.7+）
2. 是否有足夠的磁盤空間
3. 程式是否有適當的權限 