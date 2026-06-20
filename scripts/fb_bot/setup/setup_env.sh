#!/bin/bash

# Facebook Bot 環境設置腳本
# 自動檢測和配置 Python 虛擬環境

echo "=== Facebook Bot 環境設置 ==="
echo ""

# 檢查是否存在虛擬環境
check_venv() {
    if [ -n "${VIRTUAL_ENV}" ]; then
        echo "✅ 檢測到虛擬環境: ${VIRTUAL_ENV}"
        return 0
    elif [ -f "venv/bin/activate" ]; then
        echo "✅ 檢測到本地虛擬環境: ./venv"
        return 0
    elif [ -f ".venv/bin/activate" ]; then
        echo "✅ 檢測到本地虛擬環境: ./.venv"
        return 0
    elif [ -f "env/bin/activate" ]; then
        echo "✅ 檢測到本地虛擬環境: ./env"
        return 0
    else
        echo "❌ 未檢測到虛擬環境"
        return 1
    fi
}

# 創建虛擬環境
create_venv() {
    echo "正在創建虛擬環境..."
    
    # 檢查 Python 版本
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "❌ 未找到 Python"
        exit 1
    fi
    
    # 創建虛擬環境
    ${PYTHON_CMD} -m venv venv
    
    if [ $? -eq 0 ]; then
        echo "✅ 虛擬環境創建成功"
        return 0
    else
        echo "❌ 虛擬環境創建失敗"
        return 1
    fi
}

# 安裝依賴
install_dependencies() {
    echo "正在安裝依賴套件..."
    
    # 激活虛擬環境
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    elif [ -f "env/bin/activate" ]; then
        source env/bin/activate
    else
        echo "❌ 無法找到虛擬環境"
        return 1
    fi
    
    # 安裝核心依賴
    echo "安裝核心依賴..."
    pip install py-cord requests beautifulsoup4
    
    if [ $? -ne 0 ]; then
        echo "❌ 核心依賴安裝失敗"
        return 1
    fi
    
    # 安裝可選依賴（提升性能）
    echo "安裝可選依賴（提升性能）..."
    pip install lxml html5lib
    
    if [ $? -eq 0 ]; then
        echo "✅ 所有依賴安裝成功"
    else
        echo "⚠️  可選依賴安裝失敗，但不影響基本功能"
    fi
    
    return 0
}

# 生成環境配置文件
generate_env_config() {
    echo "正在生成環境配置文件..."
    
    # 檢測 Python 路徑
    if [ -f "venv/bin/python" ]; then
        PYTHON_PATH="./venv/bin/python"
    elif [ -f ".venv/bin/python" ]; then
        PYTHON_PATH="./.venv/bin/python"
    elif [ -f "env/bin/python" ]; then
        PYTHON_PATH="./env/bin/python"
    else
        PYTHON_PATH="python3"
    fi
    
    # 創建環境配置文件
    cat > .env_config << EOF
# Facebook Bot 環境配置
# 自動生成，請勿手動修改

# Python 解釋器路徑
PYTHON_PATH="${PYTHON_PATH}"

# 虛擬環境激活腳本
VENV_ACTIVATE=""
if [ -f "venv/bin/activate" ]; then
    VENV_ACTIVATE="venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    VENV_ACTIVATE=".venv/bin/activate"
elif [ -f "env/bin/activate" ]; then
    VENV_ACTIVATE="env/bin/activate"
fi

# 檢查是否在虛擬環境中
if [ -n "\${VIRTUAL_ENV}" ]; then
    echo "在虛擬環境中: \${VIRTUAL_ENV}"
elif [ -n "\$VENV_ACTIVATE" ]; then
    echo "使用本地虛擬環境: \$VENV_ACTIVATE"
else
    echo "使用系統 Python"
fi
EOF
    
    echo "✅ 環境配置文件已生成: .env_config"
}

# 主流程
main() {
    # 檢查是否已有虛擬環境
    if check_venv; then
        echo "虛擬環境已存在，跳過創建步驟"
    else
        echo "未檢測到虛擬環境，是否要創建？(y/n)"
        read -r response
        if [[ "${response}" =~ ^[Yy]$ ]]; then
            if create_venv; then
                if install_dependencies; then
                    echo "✅ 虛擬環境設置完成"
                else
                    echo "❌ 依賴安裝失敗"
                    exit 1
                fi
            else
                echo "❌ 虛擬環境創建失敗"
                exit 1
            fi
        else
            echo "跳過虛擬環境創建"
        fi
    fi
    
    # 生成環境配置
    generate_env_config
    
    echo ""
    echo "=== 環境設置完成 ==="
    echo ""
    echo "現在您可以使用以下命令："
    echo "  ./start_bot.sh    - 啟動 Bot"
    echo "  ./status_bot.sh   - 檢查狀態"
    echo "  ./stop_bot.sh     - 停止 Bot"
    echo ""
    echo "腳本會自動檢測並使用虛擬環境"
}

main 