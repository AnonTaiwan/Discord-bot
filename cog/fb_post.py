from discord.ext import commands
from internal import utils

class FBPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/fb_post.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("cog/fb_post.py: 機器人已準備就緒")

def setup(bot: commands.Bot):
    bot.add_cog(FBPost(bot))
