import discord
from discord.ext import commands
from internal import utils


class Halt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/halt.py: 日誌系統初始化完成")

    @discord.slash_command(name="halt", description="停止機器人")
    async def halt(self, ctx: discord.ApplicationContext):
        if not utils.is_worker(ctx.author) and not utils.is_developer(ctx.author):
            embed = discord.Embed(title="權限不足", description="只有後援會人員或工程部可以執行此命令", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        
        await ctx.defer(ephemeral=True)
        await ctx.delete()

        embed = discord.Embed(title="停止機器人", description=f"機器人將由 {ctx.author.mention} 停止", color=discord.Color.orange())
        await ctx.send(embed=embed)
        self.logger.info(f"機器人由 {ctx.author} (ID: {ctx.author.id}) 停止")
        await self.bot.close()


def setup(bot: commands.Bot):
    bot.add_cog(Halt(bot))
