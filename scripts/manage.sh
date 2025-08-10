#!/bin/bash

# Facebook Bot 管理腳本
# 提供便捷的方式來調用各種工具

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FB_BOT_SCRIPT_DIR="${SCRIPT_DIR}/fb_bot"

show_help() {
    echo "Facebook Bot 管理工具"
    echo ""
    echo "常用命令："
    echo "  start     - 啟動 Bot"
    echo "  stop      - 停止 Bot"
    echo "  restart   - 重啟 Bot"
    echo "  status    - 檢查 Bot 狀態"
    echo ""
    echo "環境檢查："
    echo "  check     - 完整環境檢查"
    echo "  check-env - 基本設置檢查"
    echo "  check-py  - py-cord 專用檢查"
    echo ""
    echo "設置工具："
    echo "  setup     - 環境設置"
    echo "  screen    - 使用 screen 啟動"
    echo "  systemd   - 顯示 systemd 設置說明"
    echo ""
    echo "維護工具："
    echo "  logs      - 查看日誌"
    echo "  cleanup   - 清理專案"
    echo "  python    - 運行 Python 腳本"
    echo ""
    echo "幫助："
    echo "  help      - 顯示此幫助"
    echo ""
    echo "使用範例："
    echo "  ./manage.sh start"
    echo "  ./manage.sh check"
    echo "  ./manage.sh logs --follow"
}

# 檢查腳本是否存在
check_script() {
    local script_path="$1"
    if [ ! -f "${script_path}" ]; then
        echo "❌ 腳本不存在: ${script_path}"
        return 1
    fi
    return 0
}

# 執行腳本
run_script() {
    local script_path="$1"
    shift
    if check_script "${script_path}"; then
        "${script_path}" "$@"
    else
        exit 1
    fi
}

# 主邏輯
case "${1:-help}" in
    # 常用命令
    start)
        run_script "${SCRIPT_DIR}/start_bot.sh"
        ;;
    stop)
        run_script "${SCRIPT_DIR}/stop_bot.sh"
        ;;
    restart)
        run_script "${SCRIPT_DIR}/restart_bot.sh"
        ;;
    status)
        run_script "${SCRIPT_DIR}/status_bot.sh"
        ;;
    
    # 環境檢查
    check)
        run_script "${FB_BOT_SCRIPT_DIR}/check/check_environment.sh"
        ;;
    check-env)
        run_script "${FB_BOT_SCRIPT_DIR}/check/check_setup.sh"
        ;;
    check-py)
        run_script "${FB_BOT_SCRIPT_DIR}/check/check_pycord.sh"
        ;;
    
    # 設置工具
    setup)
        run_script "${FB_BOT_SCRIPT_DIR}/setup/setup_env.sh"
        ;;
    screen)
        run_script "${FB_BOT_SCRIPT_DIR}/setup/start_bot_screen.sh"
        ;;
    systemd)
        echo "=== Systemd 設置說明 ==="
        echo ""
        echo "1. 複製服務文件："
        echo "   sudo cp ${FB_BOT_SCRIPT_DIR}/setup/facebook-bot.service /etc/systemd/system/"
        echo ""
        echo "2. 修改服務文件中的路徑："
        echo "   sudo nano /etc/systemd/system/facebook-bot.service"
        echo ""
        echo "3. 重新載入 systemd："
        echo "   sudo systemctl daemon-reload"
        echo ""
        echo "4. 啟用服務："
        echo "   sudo systemctl enable facebook-bot.service"
        echo ""
        echo "5. 啟動服務："
        echo "   sudo systemctl start facebook-bot"
        echo ""
        echo "6. 檢查狀態："
        echo "   sudo systemctl status facebook-bot"
        ;;
    
    # 維護工具
    logs)
        shift
        run_script "${FB_BOT_SCRIPT_DIR}/tools/view_logs.py" "$@"
        ;;
    cleanup)
        run_script "${FB_BOT_SCRIPT_DIR}/tools/cleanup_project.sh"
        ;;
    python)
        shift
        run_script "${FB_BOT_SCRIPT_DIR}/tools/python_runner.sh" "$@"
        ;;
    
    # 幫助
    help|--help|-h)
        show_help
        ;;
    
    # 未知命令
    *)
        echo "❌ 未知命令: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 