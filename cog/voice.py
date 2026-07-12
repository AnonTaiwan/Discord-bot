import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from internal import utils
from model.log import log_task
from model import voice


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/voice.py: 日誌系統初始化完成")

    voice_kick_command_group = discord.SlashCommandGroup(name="voice-kick", description="語音頻道踢出預約相關指令")

    def __is_valid_request(self, ctx: discord.ApplicationContext):
        return utils.is_developer(ctx.author) or utils.is_in_bot_playground(ctx.channel)

    async def __kick_from_voice_channel(self, user_id):
        user = await self.guild.fetch_member(user_id)
        if not user:
            self.logger.warning(f"無法找到使用者 ID {user_id}，無法將其踢出語音頻道")
            return

        if user.voice and user.voice.channel:
            voice_channel = user.voice.channel
            await user.move_to(None)
            self.logger.info(f"已將使用者 {user.name} 從語音頻道 {voice_channel} 中踢出")
            return

        self.logger.info(f"使用者 {user.name} 不在任何語音頻道中，無需踢出")

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.bot.get_guild(utils.CRYCHIC_GUILD_ID)

        if not self.check_kick_reservation.is_running():
            self.check_kick_reservation.start()

    @tasks.loop(minutes=1)
    @log_task("check_kick_reservation")
    async def check_kick_reservation(self):
        now = datetime.now(utils.TIME_ZONE)
        due = voice.get_due_kick_reservations(now)
        for r in due:
            try:
                await self.__kick_from_voice_channel(r.user_id)
            except Exception:
                self.logger.exception("Failed to kick user from voice channel")

            voice.remove_kick_reservation_by_id(r.id)

    @voice_kick_command_group.command(name="reserve", description="新增語音頻道踢出預約 (minutes 或 until 只能擇一)")
    async def add_reservation(
        self,
        ctx: discord.ApplicationContext,
        minutes: discord.Option(int, "多少分鐘後踢出 (< 1440)", min_value=1, max_value=1440, required=False),  # type: ignore
        until: discord.Option(str, "指定時間踢出，格式為 HH:MM (24 小時制)", required=False),
    ):  # type: ignore
        if not self.__is_valid_request(ctx):
            await ctx.respond("❌ 你沒有權限使用此指令", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 嘗試使用指令，但沒有權限")
            return

        if (not minutes and not until) or (minutes and until):
            await ctx.respond("❌ 請提供其中一個參數：minutes 或 until", ephemeral=True)
            return

        if minutes:
            try:
                if minutes <= 0 or minutes > 1440:
                    await ctx.respond("❌ 分鐘數必須在 1 到 1440 之間", ephemeral=True)
                    return
            except Exception as e:
                self.logger.error(f"Error in kick-from-voice-reservation command: {e}")
                return
            reservation_time = datetime.now(utils.TIME_ZONE) + timedelta(minutes=minutes)
        else:
            try:
                now = datetime.now(utils.TIME_ZONE)
                reservation_time = datetime.strptime(until, "%H:%M").replace(tzinfo=utils.TIME_ZONE)
                reservation_time = reservation_time.replace(year=now.year, month=now.month, day=now.day)
                if reservation_time < now:
                    reservation_time += timedelta(days=1)
                if reservation_time <= now:
                    await ctx.respond("❌ 指定的時間必須在未來", ephemeral=True)
                    return
                if reservation_time > now + timedelta(days=1):
                    await ctx.respond("❌ 指定的時間不能超過 24 小時", ephemeral=True)
                    return
            except ValueError:
                await ctx.respond("❌ 時間格式錯誤，請使用 HH:MM 格式 (24 小時制)", ephemeral=True)
                return

        voice.add_kick_reservation(ctx.author.id, reservation_time)

        try:
            await ctx.respond(f"✅ 已預約在 <t:{int(reservation_time.timestamp())}> 將你從語音頻道中踢出", ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error in kick-from-voice-reservation command: {e}")

    @voice_kick_command_group.command(name="list", description="列出我的語音頻道踢出預約")
    async def list_reservation(self, ctx: discord.ApplicationContext):
        if not self.__is_valid_request(ctx):
            await ctx.respond("❌ 你沒有權限使用此指令", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 嘗試使用指令，但沒有權限")
            return

        reservations = voice.list_kick_reservations_by_user(ctx.author.id)

        try:
            embed = discord.Embed(title="我的語音頻道踢出預約列表", color=discord.Color.blue())
            if not reservations:
                embed.description = "目前沒有任何預約"
                await ctx.respond(embed=embed, ephemeral=True)
                return
            for reservation in reservations:
                embed.add_field(name="時間", value=f"<t:{int(reservation.reservation_time.timestamp())}>", inline=False)

            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            ctx.respond("❌ 發生錯誤", ephemeral=True)
            self.logger.error(f"Error in list-kick-from-voice-reservation command: {e}")

    @voice_kick_command_group.command(name="remove-all", description="移除所有我的語音頻道踢出預約")
    async def remove_reservation(self, ctx: discord.ApplicationContext):
        if not self.__is_valid_request(ctx):
            await ctx.respond("❌ 你沒有權限使用此指令", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 嘗試使用指令，但沒有權限")
            return

        removed_count = voice.remove_kick_reservation_by_user(ctx.author.id)
        if removed_count == 0:
            await ctx.respond("❌ 你沒有任何預約可以移除", ephemeral=True)
            return

        try:
            await ctx.respond(f"✅ 已移除 {removed_count} 筆預約", ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error in remove-kick-from-voice-reservation command: {e}")


def setup(bot: commands.Bot):
    bot.add_cog(Voice(bot))
