import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils

class Fabao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/fabao.py: 日誌系統初始化完成")

    fabao_command_group = discord.SlashCommandGroup(name="fabao", description="法堡相關指令")
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.bot.get_guild(utils.CRYCHIC_GUILD_ID)
    
    @fabao_command_group.command(name="get-branches", description="查詢法堡所有分店")
    async def get_branches(self, ctx: discord.ApplicationContext):
        members = self.guild.members
        
        branches = []
        fabao_keywords = ["法堡", "Fabao", "fabao", "FABAO"]
        for member in members:
            for keyword in fabao_keywords:
                if member.display_name and keyword in member.display_name:
                    branches.append(member)
                    break

        embed = discord.Embed(title="法堡分店列表", color=discord.Color.blue())
        if branches:
            description = "\n".join([f"{member.mention}" for member in branches])
            description += f"\n\n總共有 {len(branches)} 家法堡分店"
            embed.description = description
        else:
            embed.description = "目前沒有任何法堡分店"

        try:
            await ctx.respond(embed=embed)
        except Exception as e:
            self.logger.error(f"Error responding to fabao get-branches command: {e}")
            await ctx.respond("發生錯誤，請稍後再試。", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(Fabao(bot))