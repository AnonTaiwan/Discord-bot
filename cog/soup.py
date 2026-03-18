import discord
from discord.ext import commands
import utils

class Soup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/soup.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @discord.command(name="soup", description="換算新台幣價格單位為濃湯")
    async def soup(self, ctx: discord.ApplicationContext,
                   price: discord.Option(int, description="欲換算的價格 (單位：新台幣)", required=True)): # type: ignore
        try:
            await ctx.respond(f"💰 {price} 新台幣約等於 {price / 150:.2f} 碗濃湯")
        except Exception as e:
            self.logger.error(f"換算新台幣價格單位為濃湯時發生錯誤：{e}")
            await ctx.respond("❌ 發生錯誤", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(Soup(bot))