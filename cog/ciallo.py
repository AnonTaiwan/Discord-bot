import discord
from discord.ext import commands
import utils

class Ciallo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/ciallo.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

        if "掐" in message.content:
            await message.reply("掐囉～(∠·ω< )⌒★")

def setup(bot: commands.Bot):
    bot.add_cog(Ciallo(bot))