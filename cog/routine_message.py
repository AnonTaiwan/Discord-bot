import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import utils

retouch_picture_remind_time = [
    time(hour=14, minute=0, second=0, tzinfo=utils.TIME_ZONE),
    time(hour=20, minute=0, second=0, tzinfo=utils.TIME_ZONE),
]

fall_remind_time = [
    time(hour=13, minute=0, second=0, tzinfo=utils.TIME_ZONE),
    time(hour=20, minute=0, second=0, tzinfo=utils.TIME_ZONE),
]

GSAT_AST_CAP_remind_time = [
    time(hour=8, minute=0, second=0, tzinfo=utils.TIME_ZONE)
]

anon_taiwan_anniversary_remind_time = [
    time(hour=0, minute=0, second=0, tzinfo=utils.TIME_ZONE)
]

GSAT_day = datetime(year=2026, month=1, day=17, hour=0, minute=0, second=0, microsecond=0, tzinfo=utils.TIME_ZONE)
AST_day = datetime(year=2026, month=7, day=11, hour=0, minute=0, second=0, microsecond=0, tzinfo=utils.TIME_ZONE)

GSAT_AST_candidates = [
    741308613993300058,
    838291392047743016
]

CAP_day = datetime(year=2026, month=5, day=16, hour=0, minute=0, second=0, microsecond=0, tzinfo=utils.TIME_ZONE)

CAP_candidates = [
    854559172522409994
]

anon_taiwan_creation_day = datetime(year=2025, month=1, day=3, hour=0, minute=0, second=0, microsecond=0, tzinfo=utils.TIME_ZONE)

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
        
        if not self.fall_remind.is_running():
            self.fall_remind.start()
            
        if not self.CAP_remind.is_running():
            self.CAP_remind.start()

        if not self.anon_taiwan_anniversary_remind.is_running():
            self.anon_taiwan_anniversary_remind.start()

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
        if now.hour == 13:
            message = "每日提醒琪涵雅女裝 (1/2)"
        elif now.hour == 20:
            message = "每日提醒琪涵雅女裝 (2/2)"
        
        try:
            await channel.send(message)
        except Exception as e:
            self.logger.error(f"Error sending fall remind message: {e}")

    @tasks.loop(time=GSAT_AST_CAP_remind_time)
    async def GSAT_AST_remind(self):
        channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)

        now = datetime.now(utils.TIME_ZONE)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        days = (GSAT_day - today).days

        message = ""
        if days > 0:
            message = f"距離 2026 大學學科能力測驗還有 {days} 天，考生加油！"
        elif -2 <= days <= 0:
            message = f"今天是 2026 大學學科能力測驗 Day {1 - days}，考生加油！"
        else:
            days = (AST_day - today).days
            message = f"距離 2026 大學入學分科測驗還有 {days} 天，考生加油！"

        try:
            candidates_mentions = "\n".join([f"<@{candidate_id}>" for candidate_id in GSAT_AST_candidates])

            await channel.send(f"{message}\n\n{candidates_mentions}")
        except Exception as e:
            self.logger.error(f"Error reminding GSAT_AST candidates: {e}")

    @tasks.loop(time=GSAT_AST_CAP_remind_time)
    async def CAP_remind(self):
        channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)

        now = datetime.now(utils.TIME_ZONE)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        days = (CAP_day - today).days

        try:
            candidates_mentions = "\n".join([f"<@{candidate_id}>" for candidate_id in CAP_candidates])

            await channel.send(f"距離 2026 國中教育會考還有 {days} 天，考生加油！\n\n{candidates_mentions}")
        except Exception as e:
            self.logger.error(f"Error reminding CAP candidates: {e}")

    @tasks.loop(time=anon_taiwan_anniversary_remind_time)
    async def anon_taiwan_anniversary_remind(self):
        channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)

        now = datetime.now(utils.TIME_ZONE)
        if now.month != anon_taiwan_creation_day.month or now.day != anon_taiwan_creation_day.day:
            return

        anni = now.year - anon_taiwan_creation_day.year

        try:
            await channel.send(f"今天是阿農台灣成立 {anni} 週年紀念日！🎉🎉🎉\n大家要支持阿農台灣一輩子喔！👊")
        except Exception as e:
            self.logger.error(f"Error sending anon taiwan anniversary message: {e}")

def setup(bot: commands.Bot):
    bot.add_cog(RoutineMessage(bot))
