import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils

class AutoReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/auto_reply.py: 日誌系統初始化完成")
        self.reply = {
            "咪咪落德": "咪咪落德 幹他",
            "掐": "掐囉～(∠·ω< )⌒★",
            "羊駝": "# 羊 駝 病 毒",
        }

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    def __channel_check(self, message: discord.Message) -> bool:
        return message.author.id == self.bot.user.id or message.channel.id == utils.TTS_CHANNEL_ID

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.__channel_check(message):
            return

        for key, reply_msg in self.reply.items():
            if key in message.content:
                await message.channel.send(reply_msg)
                
def setup(bot: commands.Bot):
    bot.add_cog(AutoReply(bot))