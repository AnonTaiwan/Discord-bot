import discord
from discord.ext import commands, tasks
from internal import utils
from datetime import datetime
from model import say

# 預設訊息選項
QUICK_MESSAGE_OPTIONS = [
    "屌你老母",
    "# 羊 駝 病 毒",
    "對了！說到機...",
    "咪咪洛德 幹他",
    "掐囉～(∠·ω< )⌒★",
    "要支持阿農台灣一輩子喔 👊"
]

class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/say.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_scheduled_messages.is_running():
            self.check_scheduled_messages.start()
            self.logger.info("已啟動排程訊息檢查任務")

    @discord.slash_command(name="say", description="使用彩奈傳送訊息")
    async def say(self, ctx: discord.ApplicationContext,
                               message: discord.Option(str, description="輸入訊息", required=False), # type: ignore
                               reply: discord.Option(str, description="選擇要回覆的訊息 ID", required=False, default=None), # type: ignore
                               channel: discord.Option(discord.TextChannel, description="選擇頻道", required=False), # type: ignore
                               quick_message: discord.Option(str, description="選擇預設訊息", required=False, choices=QUICK_MESSAGE_OPTIONS)): # type: ignore
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return

        if channel and channel.guild.id != utils.CRYCHIC_GUILD_ID:
            await ctx.respond("❌ 只能在 CRYCHIC 伺服器使用此指令。", ephemeral=True)
            return

        if message and len(message) > 2000:
            await ctx.respond("❌ 訊息長度不能超過 2000 個字元。", ephemeral=True)
            return

        if not (quick_message or message):
            await ctx.respond("❌ 請至少選擇預設訊息或自訂訊息其中一個。", ephemeral=True)
            return

        try:
            if quick_message and message:
                await ctx.respond("❌ 只能選擇預設訊息或自訂訊息其中一個。", ephemeral=True)
                return

            if reply is not None:
                if channel:
                    msg = await channel.fetch_message(int(reply))
                else:
                    msg = await ctx.channel.fetch_message(int(reply))
                await msg.reply(message if message else quick_message)
                if msg.channel != ctx.channel:
                    await ctx.respond("✅ 已成功回覆訊息。", ephemeral=True)
                else:
                    await ctx.defer(ephemeral = True)
                    await ctx.delete()
                return

            if channel is None:
                channel = ctx.channel

            await channel.send(message if message else quick_message)
            if channel != ctx.channel:
                await ctx.respond(f"✅ 已成功在 {channel.mention} 傳送訊息。", ephemeral=True)
            else:
                await ctx.defer(ephemeral = True)
                await ctx.delete()
        except Exception as e:
            self.logger.error(f"在頻道 {channel.id} 傳送訊息時發生錯誤：{e}")
            await ctx.respond("❌ 發生錯誤，無法傳送訊息。", ephemeral=True)

    @discord.slash_command(name="schedule", description="使用彩奈排程傳送訊息")
    async def schedule(self, ctx: discord.ApplicationContext,
                                message: discord.Option(str, description="輸入訊息", required=True),
                                time: discord.Option(str, description="輸入時間（格式：YYYY-MM-DD HH:MM）",
                                required=True), channel: discord.Option(discord.TextChannel, description="選擇頻道", required=False)): # type: ignore
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return

        if channel and channel.guild.id != utils.CRYCHIC_GUILD_ID:
            await ctx.respond("❌ 只能在 CRYCHIC 伺服器使用此指令。", ephemeral=True)
            return

        if message and len(message) > 2000:
            await ctx.respond("❌ 訊息長度不能超過 2000 個字元。", ephemeral=True)
            return

        scheduled_time = datetime.strptime(time, "%Y-%m-%d %H:%M")
        if scheduled_time < datetime.now():
            await ctx.respond("❌ 輸入的時間必須在未來。", ephemeral=True)
            return

        if channel is None:
            channel = ctx.channel

        say.add_schedule(message=message, channel_id=channel.id, scheduled_at=scheduled_time)
        await ctx.respond(f"✅ 已成功排程訊息將於 {time} 在 {channel.mention} 傳送。", ephemeral=True)

    @tasks.loop(minutes=1)
    async def check_scheduled_messages(self):
        now = datetime.now()
        due = say.get_due_scheduled(now)

        if not due:
            return

        ids_to_remove = []
        for item in due:
            channel = self.bot.get_channel(item.channel_id)
            if channel:
                try:
                    await channel.send(item.message)
                    self.logger.info(f"已成功傳送排程訊息：{item.message}")
                except Exception as e:
                    self.logger.error(f"在頻道 {channel.id} 傳送排程訊息時發生錯誤：{e}")
            else:
                self.logger.error(f"無法找到頻道 ID {item.channel_id} 傳送排程訊息")

            ids_to_remove.append(item.id)

        say.remove_schedule_by_ids(ids_to_remove)

def setup(bot: commands.Bot):
    bot.add_cog(Say(bot))
