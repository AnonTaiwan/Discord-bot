#!/bin/bash

# Facebook Bot 完整環境檢查腳本
# 檢查所有必要的套件、系統依賴和環境設置

echo "=== Facebook Bot 完整環境檢查 ==="
echo ""

# 載入 Python 執行器
source "$(dirname "$0")/python_runner.sh"

# 獲取 Python 路徑
PYTHON_PATH=$(get_python_path)
if [ $? -ne 0 ]; then
    echo "❌ 無法找到 Python 解釋器"
    exit 1
fi

echo "使用 Python: $PYTHON_PATH"
check_venv_status

echo ""

# 1. 檢查 Python 版本
echo "1. 檢查 Python 版本..."
PYTHON_VERSION=$($PYTHON_PATH --version 2>&1)
echo "✅ $PYTHON_VERSION"

# 檢查 Python 版本是否足夠新
PYTHON_MAJOR=$($PYTHON_PATH -c "import sys; print(sys.version_info.major)" 2>/dev/null)
PYTHON_MINOR=$($PYTHON_PATH -c "import sys; print(sys.version_info.minor)" 2>/dev/null)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 7 ]; then
    echo "✅ Python 版本符合要求 (>= 3.7)"
else
    echo "⚠️  Python 版本可能過舊，建議使用 Python 3.7+"
fi

# 2. 檢查系統依賴
echo ""
echo "2. 檢查系統依賴..."

# 檢查 curl
if command -v curl &> /dev/null; then
    echo "✅ curl 已安裝"
else
    echo "❌ curl 未安裝"
    echo "   Ubuntu/Debian: sudo apt-get install curl"
    echo "   CentOS/RHEL: sudo yum install curl"
fi

# 檢查 wget
if command -v wget &> /dev/null; then
    echo "✅ wget 已安裝"
else
    echo "⚠️  wget 未安裝（可選）"
fi

# 檢查 git
if command -v git &> /dev/null; then
    echo "✅ git 已安裝"
else
    echo "⚠️  git 未安裝（可選，用於版本控制）"
fi

# 檢查 screen（可選）
if command -v screen &> /dev/null; then
    echo "✅ screen 已安裝"
else
    echo "⚠️  screen 未安裝（可選，用於會話管理）"
fi

# 3. 檢查 Python 套件
echo ""
echo "3. 檢查 Python 套件..."

# 核心套件列表（根據實際代碼分析）
CORE_PACKAGES=(
    "pycord:discord"
    "requests:requests"
    "beautifulsoup4:bs4"
)

# 可選套件列表
OPTIONAL_PACKAGES=(
    "lxml:lxml"
    "html5lib:html5lib"
)

MISSING_CORE=()
MISSING_OPTIONAL=()

# 檢查核心套件
echo "核心套件："
for package in "${CORE_PACKAGES[@]}"; do
    IFS=':' read -r pip_name import_name <<< "$package"
    if $PYTHON_PATH -c "import $import_name" 2>/dev/null; then
        VERSION=$($PYTHON_PATH -c "import $import_name; print(getattr($import_name, '__version__', 'unknown'))" 2>/dev/null)
        echo "✅ $pip_name ($VERSION)"
    else
        echo "❌ $pip_name 未安裝"
        MISSING_CORE+=($pip_name)
    fi
done

# 檢查可選套件
echo ""
echo "可選套件："
for package in "${OPTIONAL_PACKAGES[@]}"; do
    IFS=':' read -r pip_name import_name <<< "$package"
    if $PYTHON_PATH -c "import $import_name" 2>/dev/null; then
        VERSION=$($PYTHON_PATH -c "import $import_name; print(getattr($import_name, '__version__', 'unknown'))" 2>/dev/null)
        echo "✅ $pip_name ($VERSION)"
    else
        echo "⚠️  $pip_name 未安裝（可選）"
        MISSING_OPTIONAL+=($pip_name)
    fi
done

# 4. 檢查網路連接
echo ""
echo "4. 檢查網路連接..."

# 檢查基本網路
if ping -c 1 8.8.8.8 &> /dev/null; then
    echo "✅ 基本網路連接正常"
else
    echo "❌ 基本網路連接失敗"
fi

# 檢查 Discord
if curl -s --connect-timeout 5 https://discord.com &> /dev/null; then
    echo "✅ Discord 連接正常"
else
    echo "❌ Discord 連接失敗"
fi

# 檢查 Facebook
if curl -s --connect-timeout 5 https://facebook.com &> /dev/null; then
    echo "✅ Facebook 連接正常"
else
    echo "❌ Facebook 連接失敗"
fi

# 5. 檢查文件權限
echo ""
echo "5. 檢查文件權限..."

# 檢查當前目錄權限
if [ -w . ]; then
    echo "✅ 當前目錄可寫"
else
    echo "❌ 當前目錄不可寫"
fi

# 檢查 logs 目錄
if [ -d "logs" ]; then
    if [ -w "logs" ]; then
        echo "✅ logs 目錄可寫"
    else
        echo "❌ logs 目錄不可寫"
    fi
else
    echo "⚠️  logs 目錄不存在（會在運行時創建）"
fi

# 6. 檢查 Discord Token
echo ""
echo "6. 檢查 Discord Token..."
if grep -q "bot.run('')" bot.py; then
    echo "❌ Discord Token 未設置"
    echo "   請在 bot.py 中設置您的 Discord Token"
    echo "   例如：bot.run('your_token_here')"
else
    echo "✅ Discord Token 已設置"
fi

# 7. 檢查必要文件
echo ""
echo "7. 檢查必要文件..."
REQUIRED_FILES=("bot.py" "cog/fb.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 不存在"
    fi
done

# 8. 檢查腳本權限
echo ""
echo "8. 檢查腳本權限..."
SCRIPTS=("start_bot.sh" "stop_bot.sh" "status_bot.sh" "restart_bot.sh" "python_runner.sh" "check_setup.sh" "setup_env.sh")
for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo "✅ $script 可執行"
        else
            echo "⚠️  $script 需要執行權限"
            chmod +x "$script"
            echo "✅ 已添加執行權限"
        fi
    else
        echo "❌ $script 不存在"
    fi
done

# 9. 檢查系統資源
echo ""
echo "9. 檢查系統資源..."

# 檢查磁盤空間
DISK_USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    echo "✅ 磁盤空間充足 ($DISK_USAGE% 使用)"
else
    echo "⚠️  磁盤空間不足 ($DISK_USAGE% 使用)"
fi

# 檢查記憶體
if command -v free &> /dev/null; then
    MEMORY_AVAILABLE=$(free -m | awk 'NR==2{printf "%.0f", $7*100/$2}')
    if [ "$MEMORY_AVAILABLE" -gt 20 ]; then
        echo "✅ 記憶體充足 ($MEMORY_AVAILABLE% 可用)"
    else
        echo "⚠️  記憶體不足 ($MEMORY_AVAILABLE% 可用)"
    fi
fi

# 10. 測試基本功能
echo ""
echo "10. 測試基本功能..."

# 測試 Discord 功能
echo "測試 Discord 功能..."
$PYTHON_PATH -c "
import discord
from discord.ext import commands

try:
    intents = discord.Intents.all()
    bot = commands.Bot(intents=intents)
    print('✅ Discord Bot 創建成功')
except Exception as e:
    print(f'❌ Discord Bot 創建失敗: {e}')

try:
    embed = discord.Embed(title='測試', description='測試描述')
    print('✅ Discord Embed 創建成功')
except Exception as e:
    print(f'❌ Discord Embed 創建失敗: {e}')
"

# 測試 requests 功能
echo "測試 requests 功能..."
$PYTHON_PATH -c "
import requests

try:
    response = requests.get('https://httpbin.org/get', timeout=5)
    if response.status_code == 200:
        print('✅ requests 功能正常')
    else:
        print(f'⚠️  requests 狀態碼異常: {response.status_code}')
except Exception as e:
    print(f'❌ requests 功能異常: {e}')
"

# 測試 BeautifulSoup 功能
echo "測試 BeautifulSoup 功能..."
$PYTHON_PATH -c "
from bs4 import BeautifulSoup

try:
    html = '<html><body><h1>測試</h1></body></html>'
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('h1').text
    if title == '測試':
        print('✅ BeautifulSoup 功能正常')
    else:
        print('⚠️  BeautifulSoup 解析異常')
except Exception as e:
    print(f'❌ BeautifulSoup 功能異常: {e}')
"

# 總結
echo ""
echo "=== 檢查完成 ==="
echo ""

if [ ${#MISSING_CORE[@]} -gt 0 ]; then
    echo "❌ 缺少核心套件："
    echo "   pip install ${MISSING_CORE[*]}"
    echo ""
    echo "或運行環境設置腳本："
    echo "   ./setup_env.sh"
    echo ""
fi

if [ ${#MISSING_OPTIONAL[@]} -gt 0 ]; then
    echo "⚠️  缺少可選套件（可提升性能）："
    echo "   pip install ${MISSING_OPTIONAL[*]}"
    echo ""
fi

echo "建議的安裝命令："
echo "pip install py-cord requests beautifulsoup4 lxml"
echo ""
echo "如果所有檢查都通過，您可以使用："
echo "  ./start_bot.sh    - 啟動 Bot"
echo "  ./status_bot.sh   - 檢查狀態"
echo "  ./stop_bot.sh     - 停止 Bot" 