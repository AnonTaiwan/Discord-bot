#!/bin/bash

# Facebook Bot 專案清理腳本
# 刪除不需要的文件和目錄

echo "=== Facebook Bot 專案清理 ==="
echo ""

# 確認清理
echo "此腳本將清理以下項目："
echo "- macOS 系統文件 (.DS_Store)"
echo "- Python 緩存文件 (__pycache__, .pyc)"
echo "- 臨時圖片文件 (1.jpg)"
echo "- 舊的日誌文件（可選）"
echo ""

read -p "是否繼續？(y/n): " -r response
if [[ ! "${response}" =~ ^[Yy]$ ]]; then
    echo "清理已取消"
    exit 0
fi

echo "開始清理..."

# 1. 刪除 macOS 系統文件
echo "1. 清理 macOS 系統文件..."
find . -name ".DS_Store" -type f -delete
echo "✅ macOS 系統文件已清理"

# 2. 刪除 Python 緩存文件
echo "2. 清理 Python 緩存文件..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -type f -delete
find . -name "*.pyo" -type f -delete
echo "✅ Python 緩存文件已清理"

# 3. 刪除臨時圖片文件
echo "3. 清理臨時圖片文件..."
if [ -f "1.jpg" ]; then
    rm -f 1.jpg
    echo "✅ 臨時圖片文件已清理"
else
    echo "✅ 沒有臨時圖片文件需要清理"
fi

# 4. 清理舊日誌文件（可選）
echo ""
read -p "是否清理 7 天前的日誌文件？(y/n): " -r response
if [[ "${response}" =~ ^[Yy]$ ]]; then
    echo "4. 清理舊日誌文件..."
    if [ -d "logs" ]; then
        find logs -name "*.log" -mtime +7 -delete
        echo "✅ 舊日誌文件已清理"
    else
        echo "✅ logs 目錄不存在"
    fi
else
    echo "4. 跳過日誌文件清理"
fi

# 5. 清理空的日誌目錄
echo "5. 清理空目錄..."
find . -type d -empty -delete 2>/dev/null
echo "✅ 空目錄已清理"

# 6. 顯示清理結果
echo ""
echo "=== 清理完成 ==="
echo ""

# 顯示當前目錄大小
if command -v du &> /dev/null; then
    TOTAL_SIZE=$(du -sh . | cut -f1)
    echo "專案總大小: ${TOTAL_SIZE}"
fi

# 顯示剩餘文件
echo ""
echo "剩餘的主要文件："
ls -la | grep -E "\.(py|sh|md|txt|service)$|^(cog|logs)$"

echo ""
echo "清理完成！專案現在更加整潔了。" 