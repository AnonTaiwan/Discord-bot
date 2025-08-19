import discord
from discord.ext import commands, tasks
from curl_cffi import requests
import logging
from datetime import datetime
import os
import random

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

class Omikuji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_logging()

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

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(1354880766126985358) # 閒聊大廳
        self.logger.info(f'cog_name.cog: {self.bot.user} (ID: {self.bot.user.id}) Ready!')
        try:
            await self.channel.send("CogName 已啟動！")
        except Exception as e:
            self.logger.error(f"Error sending ready message: {e}")

    @discord.slash_command(name="omikuji", description="抽籤")
    async def draw_omikuji(self, ctx: discord.ApplicationContext):
        weights = [0.05,0.1,0.2,0.3,0.2,0.1,0.05]  
        result = random.choices(omikuji_results, weights=weights)[0]
        emoji = discord.utils.get(self.bot.emojis, name=result)

        try:
            if emoji:
                await ctx.respond(f"{emoji}")
            else:
                await ctx.respond(f"抽到的籤是：{result}")
        except Exception as e:
            self.logger.error(f"Error responding to omikuji command: {e}")
            await ctx.respond("抽籤失敗，請稍後再試。")

def setup(bot: commands.Bot):
    bot.add_cog(Omikuji(bot))