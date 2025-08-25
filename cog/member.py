import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import random
import pytz
import utils

class Member(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/member.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @discord.slash_command(name="non-mygo-members", description="取得所有未領取「迷失之人」身分組的人")
    async def non_mygo_members(self, ctx: discord.ApplicationContext):
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return

        if ctx.guild is None:
            await ctx.respond("此指令只能在伺服器中使用。", ephemeral=True)
            return
        
        members = ctx.guild.members

        try:
            non_mygo_members = [member for member in members if
                                not any(role.id == utils.MYGO_ROLE_ID or role.id == utils.BOT_ROLE_ID
                                    for role in member.roles)]

            if not non_mygo_members:
                await ctx.respond("所有成員都已領取「迷失之人」身分組。")
                return
            
            embed = discord.Embed(title="未領取「迷失之人」身分組的成員", color=discord.Color.blue())
            for member in non_mygo_members:
                join_time = member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "未知"
                embed.add_field(name=member.mention, value=f"加入時間: {join_time}", inline=False)

            await ctx.respond(embed=embed)
        except Exception as e:
            self.logger.error(f"Error responding to non_mygo_members command: {e}")
            await ctx.respond("❌ 發生錯誤，無法取得成員列表。")

def setup(bot: commands.Bot):
    bot.add_cog(Member(bot))