import discord
from discord.ext import commands
import utils

class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/say.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @discord.slash_command(name="say", description="使用彩奈傳送訊息")
    async def say(self, ctx: discord.ApplicationContext,
                               message: discord.Option(str, description="輸入訊息", required=True), # type: ignore
                               reply: discord.Option(str, description="選擇要回覆的訊息 ID", required=False, default=None), # type: ignore
                               channel: discord.Option(discord.TextChannel, description="選擇頻道", required=False)): # type: ignore
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return
        
        if channel and channel.guild.id != utils.CRYCHIC_GUILD_ID:
            await ctx.respond("❌ 只能在 CRYCHIC 伺服器使用此指令。", ephemeral=True)
            return

        if len(message) > 2000:
            await ctx.respond("❌ 訊息長度不能超過 2000 個字元。", ephemeral=True)
            return
        
        try:
            if channel and reply:
                await ctx.respond("❌ 只能選擇頻道或回覆其中一個。", ephemeral=True)

            if reply is not None:
                msg = await ctx.channel.fetch_message(int(reply))
                await msg.reply(message)
                await ctx.respond(f"✅ 已成功回覆訊息。", ephemeral=True)
                return

            if channel is None:
                channel = ctx.channel

            await channel.send(message)
            await ctx.respond(f"✅ 已成功在 {channel.mention} 傳送訊息。", ephemeral=True)
        except Exception as e:
            self.logger.error(f"在頻道 {channel.id} 傳送訊息時發生錯誤：{e}")
            await ctx.respond("❌ 發生錯誤，無法傳送訊息。", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(Say(bot))