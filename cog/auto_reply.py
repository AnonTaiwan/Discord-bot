import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils
import random
from pypinyin import pinyin, lazy_pinyin, Style

class AutoReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/auto_reply.py: 日誌系統初始化完成")
        self.reply = {
            "mi1mi1luo4de2": ("咪咪洛德 幹他", 1),
            "mi1mi1luo4de5": ("咪咪洛德 幹他", 1),
            "掐": ("掐囉～(∠·ω< )⌒★", 1),
            "羊駝": ("# 羊 駝 病 毒", 0.25),
        }

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    def __ignore_message(self, message: discord.Message) -> bool:
        return message.author.id == self.bot.user.id or message.channel.id == utils.TTS_CHANNEL_ID

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.__ignore_message(message):
            return

        content_pinyin = "".join(lazy_pinyin(message.content, style=Style.TONE2, tone_sandhi=True, neutral_tone_with_five=True))
        
        for key, (reply_msg, probability) in self.reply.items():
            if (key in content_pinyin or key in message.content) and random.random() <= probability:
                await message.channel.send(reply_msg)
                
def setup(bot: commands.Bot):
    bot.add_cog(AutoReply(bot))