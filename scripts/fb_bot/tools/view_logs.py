#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日誌查看工具
用於查看和管理 Facebook Bot 的日誌文件
支持虛擬環境自動檢測
"""

import os
import sys
from datetime import datetime, timedelta
import argparse

# 虛擬環境檢測
def check_venv():
    """檢查是否在虛擬環境中"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"✅ 在虛擬環境中: {sys.prefix}")
        return True
    else:
        print("⚠️  未在虛擬環境中")
        return False

def list_log_files():
    """列出所有可用的日誌文件"""
    if not os.path.exists('logs'):
        print("logs 目錄不存在")
        return []

    log_files = []
    for file in os.listdir('logs'):
        if file.startswith('fb_bot_') and file.endswith('.log'):
            log_files.append(file)

    return sorted(log_files)

def view_log(log_file, lines=50, follow=False):
    """查看指定的日誌文件"""
    log_path = os.path.join('logs', log_file)

    if not os.path.exists(log_path):
        print(f"日誌文件 {log_file} 不存在")
        return

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            if follow:
                # 實時跟蹤日誌
                print(f"正在跟蹤日誌文件: {log_file}")
                print("按 Ctrl+C 停止跟蹤")
                print("-" * 50)

                # 先顯示最後幾行
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    print(line.rstrip())

                # 然後跟蹤新內容
                while True:
                    line = f.readline()
                    if line:
                        print(line.rstrip())
                    else:
                        import time
                        time.sleep(1)
            else:
                # 只顯示最後幾行
                all_lines = f.readlines()
                print(f"顯示 {log_file} 的最後 {lines} 行:")
                print("-" * 50)
                for line in all_lines[-lines:]:
                    print(line.rstrip())
    except KeyboardInterrupt:
        if follow:
            print("\n停止跟蹤日誌")
    except Exception as e:
        print(f"讀取日誌文件時發生錯誤: {e}")

def search_log(log_file, keyword):
    """在日誌文件中搜索關鍵字"""
    log_path = os.path.join('logs', log_file)

    if not os.path.exists(log_path):
        print(f"日誌文件 {log_file} 不存在")
        return

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            print(f"在 {log_file} 中搜索 '{keyword}':")
            print("-" * 50)
            found = False
            for line_num, line in enumerate(f, 1):
                if keyword.lower() in line.lower():
                    print(f"第 {line_num} 行: {line.rstrip()}")
                    found = True

            if not found:
                print(f"未找到包含 '{keyword}' 的行")
    except Exception as e:
        print(f"搜索日誌文件時發生錯誤: {e}")

def clean_old_logs(days=7):
    """清理舊的日誌文件"""
    if not os.path.exists('logs'):
        print("logs 目錄不存在")
        return

    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_count = 0

    for file in os.listdir('logs'):
        if file.startswith('fb_bot_') and file.endswith('.log'):
            file_path = os.path.join('logs', file)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

            if file_time < cutoff_date:
                try:
                    os.remove(file_path)
                    print(f"已刪除舊日誌文件: {file}")
                    deleted_count += 1
                except Exception as e:
                    print(f"刪除 {file} 時發生錯誤: {e}")

    print(f"清理完成，共刪除 {deleted_count} 個舊日誌文件")

def main():
    parser = argparse.ArgumentParser(description='Facebook Bot 日誌查看工具')
    parser.add_argument('action', choices=['list', 'view', 'search', 'clean'],
                       help='執行的操作')
    parser.add_argument('--file', '-f', help='日誌文件名')
    parser.add_argument('--lines', '-n', type=int, default=50,
                       help='顯示的行數 (預設: 50)')
    parser.add_argument('--follow', '-F', action='store_true',
                       help='實時跟蹤日誌文件')
    parser.add_argument('--keyword', '-k', help='搜索關鍵字')
    parser.add_argument('--days', '-d', type=int, default=7,
                       help='清理多少天前的日誌 (預設: 7)')
    parser.add_argument('--check-env', action='store_true',
                       help='檢查虛擬環境狀態')

    args = parser.parse_args()

    # 檢查虛擬環境
    if args.check_env:
        check_venv()
        return

    if args.action == 'list':
        log_files = list_log_files()
        if log_files:
            print("可用的日誌文件:")
            for file in log_files:
                file_path = os.path.join('logs', file)
                size = os.path.getsize(file_path)
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"  {file} ({size} bytes, 修改時間: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print("沒有找到日誌文件")

    elif args.action == 'view':
        if not args.file:
            print("請指定要查看的日誌文件 (使用 --file 參數)")
            return
        view_log(args.file, args.lines, args.follow)

    elif args.action == 'search':
        if not args.file:
            print("請指定要搜索的日誌文件 (使用 --file 參數)")
            return
        if not args.keyword:
            print("請指定搜索關鍵字 (使用 --keyword 參數)")
            return
        search_log(args.file, args.keyword)

    elif args.action == 'clean':
        clean_old_logs(args.days)

if __name__ == '__main__':
    main()
