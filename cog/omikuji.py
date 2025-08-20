import discord
from discord.ext import commands, tasks
from curl_cffi import requests
import logging
from datetime import datetime, timedelta, time
import os
import random
import pytz
import json

#"大吉" Daikichi
#"吉"   Kichi
#"中吉" Chukichi
#"小吉" Shokichi
#"末吉" Suekichi
#"凶"," Kyo
#"大凶" Daikyo
omikuji_results = ["Daikichi",
                   "Kichi", 
                   "Chukichi", 
                   "Shokichi", 
                   "Suekichi", 
                   "Kyo",
                   "Daikyo"]


timezone = pytz.timezone('Asia/Taipei')  # 設定時區為台北時間
daily_reset = time(hour=0, minute=30, second=0, tzinfo=timezone)  # 每日訊息時間設定

record_file = 'JSON/omikuji.json'

class Omikuji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_logging()

    def _check_config_exist(self):
        if not os.path.exists(record_file):
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump({ "omikuji": [] }, f, ensure_ascii=False, indent=4)
            self.logger.info(f"{record_file} 不存在，已創建一個空的 {record_file}")
        else:
            self.logger.info(f"{record_file} 已存在")

    def setup_logging(self):
        """設置日誌系統"""
        # 創建 logs 目錄（如果不存在）
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # 設置日誌文件名（包含日期）
        log_filename = f'logs/fb_bot_{datetime.now().strftime("%Y%m%d")}.log'
        
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
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("cog/omikuji.py: 日誌系統初始化完成")

    def save_omikuji(self):
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump({"omikuji": self.omikuji}, f, ensure_ascii=False, indent=4)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("Omikuji cog is ready.")
        with open(record_file, 'r', encoding='utf-8') as f:
            omikuji_data = json.load(f)
        self.omikuji = omikuji_data.get("omikuji", [])
        self.daily_message.start()

    @discord.slash_command(name="omikuji", description="抽籤(此功能由)")
    async def draw_omikuji(self, ctx: discord.ApplicationContext):
        if ctx.author.id in self.omikuji:
            await ctx.respond("你今天已經抽過籤了！請明天再來。")
            return
        weights = [0.05,0.1,0.2,0.3,0.2,0.1,0.05]  
        result = random.choices(omikuji_results, weights=weights)[0]
        emoji = discord.utils.get(self.bot.emojis, name=result)

        try:
            if emoji:
                await ctx.respond(f"{emoji}")
            else:
                await ctx.respond(f"抽到的籤是：{result}")
            self.omikuji.append(ctx.author.id)
            self.save_omikuji()
        except Exception as e:
            self.logger.error(f"Error responding to omikuji command: {e}")
            await ctx.respond("抽籤失敗，請稍後再試。")

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