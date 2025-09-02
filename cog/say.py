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
    async def non_mygo_members(self, ctx: discord.ApplicationContext,
                               channel: discord.Option(discord.TextChannel, description="選擇頻道", required=True), # type: ignore
                               message: discord.Option(str, description="輸入訊息", required=True)): # type: ignore
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return
        
        if channel.guild.id != utils.CRYCHIC_GUILD_ID:
            await ctx.respond("❌ 只能在 CRYCHIC 伺服器使用此指令。", ephemeral=True)
            return

        if len(message) > 2000:
            await ctx.respond("❌ 訊息長度不能超過 2000 個字元。", ephemeral=True)
            return

        try:
            await channel.send(message)
            await ctx.respond(f"✅ 已成功在 {channel.mention} 傳送訊息。", ephemeral=True)
        except Exception as e:
            self.logger.error(f"在頻道 {channel.id} 傳送訊息時發生錯誤：{e}")
            await ctx.respond("❌ 發生錯誤，無法傳送訊息。", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(Say(bot))