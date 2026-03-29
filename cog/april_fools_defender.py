import discord
from discord.ext import commands
from datetime import timedelta
import utils

ARONA_2_0_ID = 1486154454850863298
TIMEOUT_DURATION = timedelta(hours=1)

class AprilFoolsDefender(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger("AprilFoolsDefender")
        self.logger.info("cog/april_fools_defender.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message is from the specific bot
        if message.author.id == ARONA_2_0_ID:
            # Notify the developer role
            guild = message.guild
            developer_role = discord.utils.get(guild.roles, id=utils.DEVELOPER_ROLE_ID)
            if developer_role:
                dev_test_channel = self.bot.get_channel(utils.TEST_CHANNEL_ID)
                await dev_test_channel.send(f"{developer_role.mention}, 彩奈 2.0 傳送了訊息，已自動禁言 1 小時！")

            # Timeout the bot
            member = guild.get_member(ARONA_2_0_ID)
            if member:
                try:
                    await member.timeout_for(TIMEOUT_DURATION, reason="Token 被盜用，自動禁言")
                    self.logger.info(f"Successfully timed out {member.name} for 1 hour.")
                except discord.Forbidden:
                    self.logger.error("Failed to timeout the bot: Missing permissions.")

# Setup function to add the cog to the bot
def setup(bot):
    bot.add_cog(AprilFoolsDefender(bot))