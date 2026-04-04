from datetime import datetime
import discord
from datetime import timedelta, timezone
import heapq
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
    GBC_TOKEN = config.get("GBC_TOKEN", "")
    THREADS_TOKEN = config.get("THREADS_TOKEN", "")
    GOOGLE_CLIENT_ID = config.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = config.get("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REFRESH_TOKEN = config.get("GOOGLE_REFRESH_TOKEN", "")
except Exception as e:
    print(f"Error reading {BOT_CONFIG_FILE}: {e}")

def update_bot_config():
    try:
        with open(BOT_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        global DEVELOPER, BOT_TOKEN, FACEBOOK_TOKEN, THREADS_TOKEN
        DEVELOPER = config.get("DEVELOPER", [])
        BOT_TOKEN = config.get("DISCORD_BOT_TOKEN", "")
        FACEBOOK_TOKEN = config.get("FACEBOOK_TOKEN", "")
        THREADS_TOKEN = config.get("THREADS_TOKEN", "")
    except Exception as e:
        print(f"Error updating {BOT_CONFIG_FILE}: {e}")

# Facebook 相關配置

FB_PAGE_ID = '465375250002911' #Anon Taiwan:465375250002911 女團哭:419295154604542
GBC_FB_PAGE_ID = '419295154604542' 

# Threads 相關配置
THREADS_ID = '24030978623271968'  # Anon Taiwan Threads ID

# X 相關配置
X_DETECT_LIST = [775280864674525184, 767910567071801344, 1476931325646884879, 1353543505432301569, 1394483928463941633, 1353541214709063680, 1359055471106134016, 707778526963830784, 1531145919722188803, 1253494572841201665, 2880189872]# , 3853228393
                # bang_dream_gbp     高尾奏音             羊宮妃那             立石凜                林鼓子                青木陽菜              小日向美香           佐々木李子           米澤 茜                渡瀬 結月           岡田夢以     反田葉月
X_ID_TO_NAME = {
    "775280864674525184": "bang_dream_gbp",
    "767910567071801344": "高尾奏音",
    "1476931325646884879": "羊宮妃那",
    "1353543505432301569": "立石凜",
    "1394483928463941633": "林鼓子",
    "1353541214709063680": "青木陽菜",
    "1359055471106134016": "小日向美香",
    "707778526963830784": "佐々木李子",
    "1531145919722188803": "米澤 茜",
    "1253494572841201665": "渡瀬 結月",
    "2880189872": "岡田夢以",
    # "3853228393": "反田葉月"
}
# Discord 相關配置

CRYCHIC_GUILD_ID = 1354510853524815993
ADMIN_CHANNEL_ID = 1357392625992466653
OFFTOPIC_CHANNEL_ID = 1354880766126985358
BOT_PLAYGROUND_CHANNEL_ID = 1407248459949543455
COSPLAY_CHANNEL_ID = 1393601688157421792
FB_NOTIFICATION_CHANNEL_ID = 1357294484903297127
TEST_FB_NOTIFICATION_CHANNEL_ID = 1404889560068001864
TEST_CHANNEL_ID = 1405253533540024340
TTS_CHANNEL_ID = 1365650391496134656
WORK_TTS_CHANNEL_ID = 1455615715339145279
FB_PAGE_DAILY_MESSAGE_CHANNEL_ID = 1412829967741485276
THREADS_CHANNEL_ID = 1429474139026231396
THREADS_MEDIA_CHANNEL_ID = 1430119766080880702
CHANNEL_LOG_CHANNEL_ID = 1452275801230671935
WORKER_CHANNEL_ID = 1447639940681830451
WORKER_VOICE_CHANNEL_ID = 1449977990778720286

MC_TICKET_ID = 1413938348141187142
MC_TICKET_HISTORY_CHANNEL_ID = 1435178992167551037

ANON_TAIWAN_SUBSCRIBER_ROLE_ID = 1357315095235137636
MYGO_ROLE_ID = 1357307636382699631
NOTIFY_ROLE_ID = 1359436045837406329
NO_MYGO_ROLE_ID = 1411978158240174160
MC_MANAGER_ROLE_ID = 1435187605229801572
SOCIAL_MEDIA_MANAGER_ROLE_ID = 1359938675768557719
BOT_ROLE_ID = 1354877034991456480
DEVELOPER_ROLE_ID = 1361994254536409088
MOM_ROLE_ID = 1444384762213961864
WORKER_ROLE_ID = 1447639989126037534
ENRICH_CHANNEL_IDS = [OFFTOPIC_CHANNEL_ID, BOT_PLAYGROUND_CHANNEL_ID, COSPLAY_CHANNEL_ID]

# Google Drive 相關配置
CONFERENCE_FOLDER_ID = '11IjCJgEVHM7Uimzr8QrswknHbb1vBkzo'  # 會議錄音資料夾 ID

# 通用函數

def get_logger(name):
    """獲取 logger。設定集中在 bot.py 處理，此處僅回傳以避免重複配置引起的資源洩漏。"""
    return logging.getLogger(name)

def is_developer(user: discord.Member | discord.User) -> bool:
    """檢查使用者是否為開發者"""
    return user.id in DEVELOPER

def is_operator(user: discord.Member | discord.User) -> bool:
    """檢查使用者是否為開發者或管理員"""
    if not isinstance(user, discord.Member):
        return False
    if user.id in DEVELOPER:
        return True
    if any(role.id == DEVELOPER_ROLE_ID for role in user.roles):
        return True
    if any(role.id == SOCIAL_MEDIA_MANAGER_ROLE_ID for role in user.roles):
        return True
    return False

def is_admin(user: discord.Member | discord.User) -> bool:
    """檢查使用者是否為管理員"""
    if not isinstance(user, discord.Member):
        return False
    return bool(user.guild_permissions and user.guild_permissions.administrator)

def is_worker(user: discord.Member | discord.User) -> bool:
    """檢查使用者是否為工作人員"""
    if not isinstance(user, discord.Member):
        return False
    if is_developer(user):
        return True
    return any(role.id == WORKER_ROLE_ID for role in user.roles)

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

class PriorityQueue():
    def __init__(self, save_callback):
        self.elements = []
        self.save_callback = save_callback

    def get_raw_elements(self):
        return [item for _, item in self.elements]

    def __save(self):
        if self.save_callback:
            self.save_callback()

    def empty(self):
        return not self.elements

    def push(self, priority, item):
        heapq.heappush(self.elements, (priority, item))
        self.__save()

    def top(self):
        return self.elements[0]
    
    def pop(self):
        heapq.heappop(self.elements)
        self.__save()