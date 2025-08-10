#!/bin/bash

# 載入 Python 執行器
source "$(dirname "$0")/../tools/python_runner.sh"

echo "=== Facebook Bot 設置檢查 ==="
echo ""

# 檢查虛擬環境狀態
echo "1. 檢查 Python 環境..."
check_venv_status

# 獲取 Python 路徑
PYTHON_PATH=$(get_python_path)
if [ $? -eq 0 ]; then
    PYTHON_VERSION=$(${PYTHON_PATH} --version 2>&1)
    echo "✅ ${PYTHON_VERSION}"
else
    echo "❌ 無法找到 Python 解釋器"
    exit 1
fi

# 檢查必要的 Python 套件
echo ""
echo "2. 檢查 Python 套件..."
REQUIRED_PACKAGES=("pycord" "requests" "bs4" "curl_cffi")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ${PYTHON_PATH} -c "import ${package}" 2>/dev/null; then
        echo "✅ ${package} 已安裝"
    else
        echo "❌ ${package} 未安裝"
        MISSING_PACKAGES+=(${package})
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo ""
    echo "請安裝缺少的套件："
    echo "pip install ${MISSING_PACKAGES[*]}"
    echo ""
    echo "或者運行環境設置腳本："
    echo "./scripts/setup/setup_env.sh"
    exit 1
fi

# 檢查 Discord Token
echo ""
echo "3. 檢查 Discord Token..."
if grep -q "bot.run('')" bot.py; then
    echo "❌ Discord Token 未設置"
    echo "請在 bot.py 中設置您的 Discord Token"
    echo "例如：bot.run('your_token_here')"
    exit 1
else
    echo "✅ Discord Token 已設置"
fi

# 檢查必要文件
echo ""
echo "4. 檢查必要文件..."
REQUIRED_FILES=("bot.py" "cog/fb.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "${file}" ]; then
        echo "✅ ${file} 存在"
    else
        echo "❌ ${file} 不存在"
        exit 1
    fi
done

# 檢查腳本權限
echo ""
echo "5. 檢查腳本權限..."
SCRIPTS=("start_bot.sh" "stop_bot.sh" "status_bot.sh" "restart_bot.sh" "manage.sh")
for script in "${SCRIPTS[@]}"; do
    if [ -f "${script}" ]; then
        if [ -x "${script}" ]; then
            echo "✅ ${script} 可執行"
        else
            echo "⚠️  ${script} 需要執行權限"
            chmod +x "${script}"
            echo "✅ 已添加執行權限"
        fi
    else
        echo "❌ ${script} 不存在"
    fi
done

# 檢查網路連接
echo ""
echo "6. 檢查網路連接..."
if ping -c 1 discord.com &> /dev/null; then
    echo "✅ Discord 連接正常"
else
    echo "⚠️  無法連接到 Discord，請檢查網路"
fi

if ping -c 1 facebook.com &> /dev/null; then
    echo "✅ Facebook 連接正常"
else
    echo "⚠️  無法連接到 Facebook，請檢查網路"
fi

echo ""
echo "=== 檢查完成 ==="
echo ""
echo "如果所有檢查都通過，您可以使用以下命令："
echo "  ./start_bot.sh    - 啟動 Bot"
echo "  ./status_bot.sh   - 檢查狀態"
echo "  ./stop_bot.sh     - 停止 Bot"
echo "  ./restart_bot.sh  - 重啟 Bot"
echo "  ./manage.sh       - 管理工具"
echo ""
echo "日誌查看："
echo "  ./manage.sh logs list                    - 列出日誌文件"
echo "  ./manage.sh logs view --file fb_bot_\$(date +%Y%m%d).log --follow  - 實時查看日誌" 