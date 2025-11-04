import discord
from discord.ext import commands
import utils
import asyncio
import random
class Love(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/love.py: 日誌系統初始化完成")
        self.operator = ["❤️",]
        self.non_operator = ["對不起，我比較喜歡立希同學","對不起，我比較喜歡鼓子", "對不起，我覺得我不需要你的信用", "你覺得如果是找我，我就會答應嗎？","你覺得如果是找我，我就會回答嗎？","我覺得你不會變的真材實料"]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if "夢以我愛" in message.content or "夢以我喜歡" in message.content:
            if utils.is_operator(message.author):
                print("Operator Detected")
                await message.reply(random.choice(self.operator))
            else:
                await message.reply(random.choice(self.non_operator))

def setup(bot):
    bot.add_cog(Love(bot))