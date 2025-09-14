import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import utils

daily_ask = [
    time(hour=14, minute=0, second=0, tzinfo=utils.TIME_ZONE),
    time(hour=20, minute=0, second=0, tzinfo=utils.TIME_ZONE),
]  # 每日訊息時間設定

class RoutineMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/routine_message.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.daily_message.is_running():
            self.daily_message.start()

    @tasks.loop(time=daily_ask)
    async def daily_message(self):
        channel = self.bot.get_channel(utils.COSPLAY_CHANNEL_ID)

        now = datetime.now(utils.TIME_ZONE)
        if now.hour == 14:
            message = "每日監督椰子修圖 (1/2)"
        elif now.hour == 20:
            message = "每日監督椰子修圖 (2/2)"
        
        await channel.send(message)

def setup(bot: commands.Bot):
    bot.add_cog(RoutineMessage(bot))
