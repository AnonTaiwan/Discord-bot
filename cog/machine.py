import discord
from discord.ext import commands
import random
import utils

class Machine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/machine.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if "打機吧" in message.content:
            await message.reply("對了！說到機...")
            
def setup(bot: commands.Bot):
    bot.add_cog(Machine(bot))