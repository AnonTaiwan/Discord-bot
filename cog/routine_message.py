import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import utils

retouch_picture_remind_time = [
    time(hour=14, minute=0, second=0, tzinfo=utils.TIME_ZONE),
    time(hour=20, minute=0, second=0, tzinfo=utils.TIME_ZONE),
]

fall_remind_time = [
    time(hour=12, minute=40, second=0, tzinfo=utils.TIME_ZONE),
    time(hour=20, minute=0, second=0, tzinfo=utils.TIME_ZONE),
]

GSAT_remind_time = [
    time(hour=8, minute=0, second=0, tzinfo=utils.TIME_ZONE)
]

GSAT_day = datetime(year=2026, month=1, day=17, hour=0, minute=0, second=0, microsecond=0, tzinfo=utils.TIME_ZONE)

GSAT_candidates = [
    741308613993300058,
    838291392047743016
]

class RoutineMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/routine_message.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.retouch_picture_remind.is_running():
            self.retouch_picture_remind.start()

        if not self.GSAT_remind.is_running():
            self.GSAT_remind.start()

    @tasks.loop(time=retouch_picture_remind_time)
    async def retouch_picture_remind(self):
        channel = self.bot.get_channel(utils.COSPLAY_CHANNEL_ID)

        now = datetime.now(utils.TIME_ZONE)
        if now.hour == 14:
            message = "每日監督椰子修圖 (1/2)"
        elif now.hour == 20:
            message = "每日監督椰子修圖 (2/2)"
        
        try:
            await channel.send(message)
        except Exception as e:
            self.logger.error(f"Error sending retouch picture remind message: {e}")

        if now.hour == 14:
            message = "每日監督霧冥修圖 (1/2)"
        elif now.hour == 20:
            message = "每日監督霧冥修圖 (2/2)"
        
        try:
            await channel.send(message)
        except Exception as e:
            self.logger.error(f"Error sending retouch picture remind message: {e}")

    @tasks.loop(time=fall_remind_time)
    async def fall_remind(self):
        channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)

        now = datetime.now(utils.TIME_ZONE)
        if now.hour == 12:
            message = "每日提醒琪涵雅女裝 (1/2)"
        elif now.hour == 20:
            message = "每日提醒琪涵雅女裝 (2/2)"
        
        try:
            await channel.send(message)
        except Exception as e:
            self.logger.error(f"Error sending fall remind message: {e}")

    @tasks.loop(time=GSAT_remind_time)
    async def GSAT_remind(self):
        channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)

        now = datetime.now(utils.TIME_ZONE)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        days = (GSAT_day - today).days

        try:
            candidates_mentions = "\n".join([f"<@{candidate_id}>" for candidate_id in GSAT_candidates])

            await channel.send(f"距離 2026 大學學科能力測驗還有 {days} 天，考生加油！\n\n{candidates_mentions}")
        except Exception as e:
            self.logger.error(f"Error reminding GSAT candidates: {e}")

def setup(bot: commands.Bot):
    bot.add_cog(RoutineMessage(bot))
