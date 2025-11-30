import discord
from discord.ext import commands
import random
import utils

class Llama(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/llama.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id or message.channel.id == utils.TTS_CHANNEL_ID:
            return

        if "羊駝" in message.content:
            if random.randint(1, 100) <= 25:
                await message.reply("# 羊 駝 病 毒")

def setup(bot: commands.Bot):
    bot.add_cog(Llama(bot))