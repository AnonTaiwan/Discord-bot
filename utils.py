from datetime import datetime
import discord
from datetime import timedelta, timezone
import json
import logging
import os
from pathlib import Path

# 時區設定

TIME_ZONE = timezone(timedelta(hours=8))

# 專案路徑

ROOT_DIR = Path(__file__).resolve().parent
LOGS_DIR = ROOT_DIR / 'logs'
JSON_DIR = ROOT_DIR / 'JSON'
STATIC_DIR = ROOT_DIR / 'static'
TMP_DIR = ROOT_DIR / 'tmp'

# Bot 相關配置

BOT_CONFIG_FILE = JSON_DIR / 'bot.json'
try:
    with open(JSON_DIR / 'bot.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    DEVELOPER = config.get("DEVELOPER", [])
    BOT_TOKEN = config.get("DISCORD_BOT_TOKEN", "")
    FACEBOOK_TOKEN = config.get("FACEBOOK_TOKEN", "")
except Exception as e:
    print(f"Error reading {BOT_CONFIG_FILE}: {e}")

# Facebook 相關配置

FB_PAGE_ID = '419295154604542'

# Discord 相關配置

CRYCHIC_GUILD_ID = 1354510853524815993

OFFTOPIC_CHANNEL_ID = 1354880766126985358
BOT_PLAYGROUND_CHANNEL_ID = 1407248459949543455
FB_NOTIFICATION_CHANNEL_ID = 1357294484903297127
TEST_FB_NOTIFICATION_CHANNEL_ID = 1404889560068001864
TEST_CHANNEL_ID = 1405253533540024340

ANON_TAIWAN_SUBSCRIBER_ROLE_ID = 1357315095235137636
MYGO_ROLE_ID = 1357307636382699631
NOTIFY_ROLE_ID = 1359436045837406329
NO_MYGO_ROLE_ID = 1411978158240174160
SOCIAL_MEDIA_MANAGER_ROLE_ID = 1359938675768557719
BOT_ROLE_ID = 1354877034991456480
DEVELOPER_ROLE_ID = 1361994254536409088

# 通用函數

def get_logger(name):
    """設置日誌系統"""
    # 創建 logs 目錄（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # 設置日誌文件名（包含日期）
    log_filename = LOGS_DIR / f'bot_{datetime.now().strftime("%Y%m%d")}.log'
    
    # 配置日誌格式
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # 同時輸出到控制台
        ]
    )
    
    return logging.getLogger(name)

def is_developer(user: discord.User) -> bool:
    """檢查使用者是否為開發者"""
    return user.id in DEVELOPER

def is_operator(user: discord.User) -> bool:
    """檢查使用者是否為開發者或管理員"""
    if user.id in DEVELOPER:
        return True
    if any(role.id == DEVELOPER_ROLE_ID for role in user.roles):
        return True
    if any(role.id == SOCIAL_MEDIA_MANAGER_ROLE_ID for role in user.roles):
        return True
    return False

def is_in_bot_playground(channel: discord.TextChannel) -> bool:
    """檢查使用者是否在 Bot Playground 頻道"""
    return channel.id == BOT_PLAYGROUND_CHANNEL_ID

def check_exist_or_create_json(logger: logging.Logger, file: Path, default_content: dict = {}):
    if not file.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(default_content, f, ensure_ascii=False, indent=4)
        logger.info(f"{file} 不存在，已創建一個空的 {file}")
    else:
        logger.info(f"{file} 已存在")

def read_json(logger: logging.Logger, file: Path, default_content: dict = {}) -> dict:
    with open(file, 'r', encoding='utf-8') as f:
        try:
            content = json.load(f)
            logger.info(f"已成功讀取 {file}")
        except json.JSONDecodeError as e:
            logger.error(f"讀取 {file} 時發生錯誤：{e}")
            content = default_content
    return content

def write_json(logger: logging.Logger, file: Path, data: dict) -> bool:
    with open(file, 'w', encoding='utf-8') as f:
        try:
            json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"已成功寫入 {file}")
            return True
        except Exception as e:
            logger.error(f"寫入 {file} 時發生錯誤：{e}")
            return False
        
def get_tmp_file(filename: str) -> str:
    return str(TMP_DIR / filename)