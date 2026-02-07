import discord
from discord.ext import commands
import utils

# 預設訊息選項
QUICK_MESSAGE_OPTIONS = ["# 羊 駝 病 毒", "對了！說到機...","咪咪洛德 幹他","掐囉～(∠·ω< )⌒★","要支持阿農台灣一輩子喔 👊"]

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
                    await ctx.respond(f"✅ 已成功回覆訊息。", ephemeral=True)
                else:
                    await ctx.defer()
                    await ctx.delete()
                return

            if channel is None:
                channel = ctx.channel

            await channel.send(message if message else quick_message)
            if channel != ctx.channel:
                await ctx.respond(f"✅ 已成功在 {channel.mention} 傳送訊息。", ephemeral=True)
            else:
                await ctx.defer()
                await ctx.delete()
        except Exception as e:
            self.logger.error(f"在頻道 {channel.id} 傳送訊息時發生錯誤：{e}")
            await ctx.respond("❌ 發生錯誤，無法傳送訊息。", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(Say(bot))