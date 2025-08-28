import discord
from discord.ext import commands, tasks
from typing import List
from datetime import datetime, timedelta, timezone, time
import utils

daily_ask = [
    time(hour=10, minute=0, second=0, tzinfo=utils.TIME_ZONE),
    time(hour=15, minute=0, second=0, tzinfo=utils.TIME_ZONE),
    time(hour=22, minute=0, second=0, tzinfo=utils.TIME_ZONE),
]  # 每日訊息時間設定

class Concert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/concert.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.daily_message.is_running():
            self.daily_message.start()
        pass

    @tasks.loop(time=daily_ask)
    async def daily_message(self):
        channel = self.bot.get_channel(1354880766126985358)
        await channel.send("店長：有人要去青木陽菜仙台場嗎？")

def setup(bot: commands.Bot):
    bot.add_cog(Concert(bot))
