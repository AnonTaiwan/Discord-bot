#!/bin/bash

# Facebook Bot Python 執行器
# 自動檢測和使用虛擬環境

# 載入環境配置
load_env_config() {
    if [ -f ".env_config" ]; then
        source .env_config
    fi
}

# 獲取 Python 解釋器路徑
get_python_path() {
    # 如果已經在虛擬環境中
    if [ -n "${VIRTUAL_ENV}" ]; then
        echo "python"
        return 0
    fi
    
    # 檢查本地虛擬環境
    if [ -f "venv/bin/python" ]; then
        echo "./venv/bin/python"
        return 0
    elif [ -f "venv/Scripts/python.exe" ]; then
        echo "./venv/Scripts/python.exe"
        return 0
    elif [ -f "venv/Scripts/python" ]; then
        echo "./venv/Scripts/python"
        return 0
    elif [ -f ".venv/bin/python" ]; then
        echo ./.venv/bin/python
        return 0
    elif [ -f ".venv/Scripts/python.exe" ]; then
        echo "./.venv/Scripts/python.exe"
        return 0
    elif [ -f ".venv/Scripts/python" ]; then
        echo "./.venv/Scripts/python"
        return 0
    elif [ -f "env/bin/python" ]; then
        echo "./env/bin/python"
        return 0
    elif [ -f "env/Scripts/python.exe" ]; then
        echo "./env/Scripts/python.exe"
        return 0
    elif [ -f "env/Scripts/python" ]; then
        echo "./env/Scripts/python"
        return 0
    fi
    
    # 檢查系統 Python
    if command -v python3 &> /dev/null; then
        echo "python3"
        return 0
    elif command -v python &> /dev/null; then
        echo "python"
        return 0
    fi
    
    echo "python3"  # 預設值
    return 1
}

# 執行 Python 腳本
run_python() {
    local python_path
    python_path=$(get_python_path)
    
    if [ $? -eq 0 ]; then
        echo "使用 Python: ${python_path}"
        ${python_path} "$@"
    else
        echo "❌ 無法找到 Python 解釋器"
        exit 1
    fi
}

# 檢查虛擬環境狀態
check_venv_status() {
    if [ -n "${VIRTUAL_ENV}" ]; then
        echo "✅ 當前在虛擬環境中: ${VIRTUAL_ENV}"
    elif [ -f "venv/bin/activate" ] || [ -f ".venv/bin/activate" ] || [ -f "env/bin/activate" ] || \
         [ -f "venv/Scripts/activate" ] || [ -f ".venv/Scripts/activate" ] || [ -f "env/Scripts/activate" ]; then
        echo "✅ 檢測到本地虛擬環境"
    else
        echo "⚠️  未檢測到虛擬環境，使用系統 Python"
    fi
}

# 如果直接執行此腳本
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    load_env_config
    check_venv_status
    run_python "$@"
fi 