from datetime import datetime

import discord
from discord.ext import commands, tasks

from internal import utils

COUNTDOWN_CONFIGS = [
    {
        "channel_id": 1449977990778720286,  # 後援會第一語音頻道
        "target_date": datetime(year=2027, month=2, day=28, tzinfo=utils.TIME_ZONE),
        "template": "距離{year_prefix} 2 月 28 日還有 {days} 天",
    },
    {
        "channel_id": 1487506150831427604,  # 後援會第二語音頻道
        "target_date": datetime(year=2027, month=7, day=13, tzinfo=utils.TIME_ZONE),
        "template": "距離{year_prefix} 7 月 13 日還有 {days} 天",
    },
]


class RoutineManage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/routine_manage.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.channel_countdown_update.is_running():
            self.channel_countdown_update.start()
            try:
                await self.__apply_countdown_channel_update()
            except Exception as e:
                self.logger.error(f"Error executing initial countdown channel update: {e}")

    def __get_countdown_channel_name(self, target_date, template):
        now = datetime.now(utils.TIME_ZONE)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        target = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        days = (target - today).days

        if days < 0:
            return None

        year_diff = target.year - now.year
        if year_diff == 1:
            year_prefix = "明年"
        elif year_diff == 0:
            year_prefix = ""
        else:
            return None

        return template.format(year_prefix=year_prefix, year=target.year, month=target.month, day=target.day, days=days)

    async def __update_channel_name(self, channel_id, new_name):
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                self.logger.error(f"Failed to fetch channel {channel_id}: {e}")
                return

        if channel.name == new_name:
            return

        try:
            await channel.edit(name=new_name)
            return
        except discord.Forbidden:
            self.logger.error(f"Permission denied to edit channel {channel.name} ({channel_id}) (requires 'Manage Channels' permission).")
        except discord.HTTPException as e:
            self.logger.error(f"Failed to edit channel {channel.name} ({channel_id}) name: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error while editing channel {channel.name} ({channel_id}) name: {e}")

    async def __apply_countdown_channel_update(self):
        for config in COUNTDOWN_CONFIGS:
            channel_id = config["channel_id"]
            target_date = config["target_date"]
            template = config["template"]

            new_name = self.__get_countdown_channel_name(target_date, template)
            if new_name is None:
                continue

            await self.__update_channel_name(channel_id, new_name)

    @tasks.loop(time=utils.MIDNIGHT)
    async def channel_countdown_update(self):
        await self.__apply_countdown_channel_update()

    @discord.slash_command(name="channel-countdown", description="啟用或停用倒數頻道更名排程")
    async def toggle_countdown_loop(
        self,
        ctx: discord.ApplicationContext,
        enable: discord.Option(
            bool,
            description="是否啟用",
            required=True,
            choices=[True, False],
        ),  # type: ignore
    ):
        if not (utils.is_developer(ctx.author) or utils.is_admin(ctx.author)):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return

        is_running = self.channel_countdown_update.is_running()

        if enable:
            if not is_running:
                self.channel_countdown_update.start()
                is_running = True
        else:
            if is_running:
                self.channel_countdown_update.cancel()
                is_running = False

        status_text = "🟢 已啟用" if is_running else "🔴 已停用"
        await ctx.respond(f"倒數頻道更名排程狀態：{status_text}")


def setup(bot: commands.Bot):
    bot.add_cog(RoutineManage(bot))
