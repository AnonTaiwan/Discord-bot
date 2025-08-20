import discord
from discord.ext import commands, tasks
from curl_cffi import requests
import logging
from datetime import datetime, timedelta, time
from pathlib import Path
import random
import pytz
import json

#"大吉" Daikichi
#"吉"   Kichi
#"中吉" Chukichi
#"小吉" Shokichi
#"末吉" Suekichi
#"凶"   Kyo
#"大凶" Daikyo
omikuji_results = [
    "Daikichi",
    "Kichi", 
    "Chukichi", 
    "Shokichi", 
    "Suekichi", 
    "Kyo",
    "Daikyo"
]


timezone = pytz.timezone('Asia/Taipei')  # 設定時區為台北時間
daily_reset = time(hour=0, minute=6, second=0, tzinfo=timezone)  # 每日訊息時間設定

# 專案路徑
ROOT_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT_DIR / 'logs'
JSON_DIR = ROOT_DIR / 'JSON'
STATIC_DIR = ROOT_DIR / 'static'

record_file = JSON_DIR / 'omikuji.json'

class Omikuji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_logging()

        self._check_config_exist()

        with open(JSON_DIR / 'bot.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.DEVELOPER = config.get("DEVELOPER", [])

    def _check_config_exist(self):
        if not record_file.exists():
            record_file.parent.mkdir(parents=True, exist_ok=True)
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump({ "omikuji": [] }, f, ensure_ascii=False, indent=4)
            self.logger.info(f"{record_file} 不存在，已創建一個空的 {record_file}")
        else:
            self.logger.info(f"{record_file} 已存在")

    def setup_logging(self):
        """設置日誌系統"""
        # 創建 logs 目錄（如果不存在）
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
            
        # 設置日誌文件名（包含日期）
        log_filename = LOGS_DIR / f'fb_bot_{datetime.now().strftime("%Y%m%d")}.log'
        
        # 配置日誌格式
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # 配置日誌
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(str(log_filename), encoding='utf-8'),
                logging.StreamHandler()  # 同時輸出到控制台
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("cog/omikuji.py: 日誌系統初始化完成")

    def save_omikuji(self):
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump({"omikuji": self.omikuji}, f, ensure_ascii=False, indent=4)

    @commands.Cog.listener()
    async def on_ready(self):
        with open(record_file, 'r', encoding='utf-8') as f:
            omikuji_data = json.load(f)
        self.omikuji = omikuji_data.get("omikuji", [])
        self.daily_message.start()

    @discord.slash_command(name="omikuji", description="抽籤 (此功能由 Kevin 提供)")
    async def draw_omikuji(self, ctx: discord.ApplicationContext):
        if ctx.author.id in self.omikuji:
            await ctx.respond("你今天已經抽過籤了！請明天再來。")
            return
        weights = [0.05, 0.1, 0.2, 0.3, 0.2, 0.1, 0.05]  
        result = random.choices(omikuji_results, weights=weights)[0]

        try:
            pic_path = STATIC_DIR / 'omikuji' / f'{result}.jpg'
            if pic_path.exists():
                pic = discord.File(str(pic_path), filename=pic_path.name)
                await ctx.respond(file=pic,content = f"抽到的籤是：{result}")
            else:
                await ctx.respond(f"抽到的籤是：{result}")
            self.omikuji.append(ctx.author.id)
            self.save_omikuji()

        except Exception as e:
            self.logger.error(f"Error responding to omikuji command: {e}")
            await ctx.respond("抽籤失敗，請稍後再試。")

    @discord.slash_command(name="reset-omikuji", description="重置使用者抽籤")
    async def reset_omikuji(self, ctx: discord.ApplicationContext,
                            user: discord.Member = None):
        if ctx.author.id not in self.DEVELOPER:
            await ctx.respond("❌ 你沒有權限使用這個指令。", ephemeral=True)
            return
        
        if user is None:
            await ctx.respond("請指定一個使用者來重置抽籤名單。", ephemeral=True)
            return
        
        if user.id in self.omikuji:
            self.omikuji.remove(user.id)
            self.save_omikuji()
        
        await ctx.respond(f"<@{user.id}> 已被重置。")

    @tasks.loop(time=daily_reset)
    async def daily_message(self):
        self.omikuji = []
        channel = self.bot.get_channel(1405253533540024340) 
        if channel:
            await channel.send("每日運勢抽籤已重置！")
        else:
            self.logger.error("無法找到指定的頻道。")

def setup(bot: commands.Bot):
    bot.add_cog(Omikuji(bot))