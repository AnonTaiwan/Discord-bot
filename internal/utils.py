import discord
from datetime import time, timedelta, timezone
import json
import logging
from pathlib import Path
from internal import config

# 時區設定

TIME_ZONE = timezone(timedelta(hours=8))

# 常用排程時間設定

MIDNIGHT = [time(hour=0, minute=0, second=0, tzinfo=TIME_ZONE)]
MORNING = [time(hour=9, minute=0, second=0, tzinfo=TIME_ZONE)]

# 專案路徑

# When placed under internal/, ROOT_DIR should be repository root
ROOT_DIR = Path(__file__).resolve().parents[1]
LOGS_DIR = ROOT_DIR / "logs"
JSON_DIR = ROOT_DIR / "JSON"
STATIC_DIR = ROOT_DIR / "static"
TMP_DIR = ROOT_DIR / "tmp"

# Bot 相關配置


def load_config():
    global DEVELOPER, BOT_TOKEN
    global GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN

    cfg = config.CONFIG

    DEVELOPER = cfg.discord.developer_ids
    BOT_TOKEN = cfg.discord.token
    GOOGLE_CLIENT_ID = cfg.google.google_client_id
    GOOGLE_CLIENT_SECRET = cfg.google.google_client_secret
    GOOGLE_REFRESH_TOKEN = cfg.google.google_refresh_token


DEVELOPER = []
BOT_TOKEN = ""
GOOGLE_CLIENT_ID = ""
GOOGLE_CLIENT_SECRET = ""
GOOGLE_REFRESH_TOKEN = ""

load_config()

# Discord 相關配置

CRYCHIC_GUILD_ID = 1354510853524815993
ADMIN_CHANNEL_ID = 1357392625992466653
OFFTOPIC_CHANNEL_ID = 1354880766126985358
BOT_PLAYGROUND_CHANNEL_ID = 1407248459949543455
COSPLAY_CHANNEL_ID = 1393601688157421792
TEST_CHANNEL_ID = 1405253533540024340
TTS_CHANNEL_ID = 1365650391496134656
CHANNEL_LOG_CHANNEL_ID = 1452275801230671935
WORKER_CHANNEL_ID = 1447639940681830451

MYGO_ROLE_ID = 1357307636382699631
NOTIFY_ROLE_ID = 1359436045837406329
NO_MYGO_ROLE_ID = 1411978158240174160
MC_MANAGER_ROLE_ID = 1435187605229801572
SOCIAL_MEDIA_MANAGER_ROLE_ID = 1359938675768557719
BOT_ROLE_ID = 1354877034991456480
DEVELOPER_ROLE_ID = 1361994254536409088
WORKER_ROLE_ID = 1447639989126037534
ENRICH_CHANNEL_IDS = [OFFTOPIC_CHANNEL_ID, BOT_PLAYGROUND_CHANNEL_ID, COSPLAY_CHANNEL_ID]

# Google Drive 相關配置

CONFERENCE_FOLDER_ID = "11IjCJgEVHM7Uimzr8QrswknHbb1vBkzo"  # 會議錄音資料夾 ID

# 通用函數


def get_logger(name):
    """獲取 logger。設定集中在 bot.py 處理，此處僅回傳以避免重複配置引起的資源洩漏。"""
    return logging.getLogger(name)


def is_developer(user: discord.Member | discord.User) -> bool:
    """檢查使用者是否為開發者"""
    return user.id in DEVELOPER


def is_operator(user: discord.Member | discord.User) -> bool:
    """檢查使用者是否為開發者、管理員或小編"""
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


def is_unlimited(user: discord.Member | discord.User, channel: discord.TextChannel) -> bool:
    """檢查使用者是否為無限權限（開發者、管理員）"""
    return is_developer(user) or is_admin(user) or is_in_bot_playground(channel)


def check_exist_or_create_json(logger: logging.Logger, file: Path, default_content: dict = {}):
    if not file.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
        with open(file, "w", encoding="utf-8") as f:
            json.dump(default_content, f, ensure_ascii=False, indent=4)
        logger.info(f"{file} 不存在，已創建一個空的 {file}")
    else:
        logger.info(f"{file} 已存在")


def read_json(logger: logging.Logger, file: Path, default_content: dict = {}) -> dict:
    with open(file, "r", encoding="utf-8") as f:
        try:
            content = json.load(f)
            # logger.info(f"已成功讀取 {file}")
        except json.JSONDecodeError as e:
            logger.error(f"讀取 {file} 時發生錯誤：{e}")
            content = default_content
    return content


def write_json(logger: logging.Logger, file: Path, data: dict) -> bool:
    with open(file, "w", encoding="utf-8") as f:
        try:
            json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"已成功寫入 {file}")
            return True
        except Exception as e:
            logger.error(f"寫入 {file} 時發生錯誤：{e}")
            return False
