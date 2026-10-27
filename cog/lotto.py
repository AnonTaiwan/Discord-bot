import random

import discord
from discord.ext import commands

from internal import utils
from internal.rate_limit import SlidingWindowRateLimiter
from model import lotto


class Lotto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/lotto.py: 日誌系統初始化完成")

        self.rate_limiter = SlidingWindowRateLimiter(limit=1, window_seconds=5)

    lotto_command_group = discord.SlashCommandGroup(name="lotto", description="樂透相關指令")

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @lotto_command_group.command(name="draw", description="隨機抽選成員")
    async def draw(self, ctx: discord.ApplicationContext):  # type: ignore
        try:
            if not utils.is_unlimited(ctx.author, ctx.channel):
                allowed, retry_after = self.rate_limiter.allow((ctx.author.id, "lotto:draw"))

                if not allowed:
                    await ctx.respond(f"❌ 操作過於頻繁，請在 {retry_after:.0f} 秒後再試。", ephemeral=True)
                    return

            pool = lotto.list_pool()
            if not pool:
                await ctx.respond("抽選池目前沒有成員")
                return
            user = random.choice(pool)

            embed = discord.Embed(title="🎉 抽選結果 🎉", description=f"抽到 <@{user}> 了！", color=discord.Color.gold())

            await ctx.respond(embed=embed)
        except Exception as e:
            self.logger.error(f"抽選成員時發生錯誤：{e}")
            await ctx.respond("❌ 發生錯誤，無法完成抽選", ephemeral=True)

    @lotto_command_group.command(name="add-user", description="新增成員至抽選池")
    async def add_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(discord.Member, description="欲加入抽選池的成員", required=True, default=None),
    ):  # type: ignore
        if user is None:
            await ctx.respond("❌ 請指定欲加入抽選池的成員")
            return

        if lotto.has_user(user.id):
            await ctx.respond(f"❌ <@{user.id}> 已在抽選池中")
            return

        lotto.add_user(user.id)

        try:
            await ctx.respond(f"✅ 已將 <@{user.id}> 新增至抽選池")
        except Exception as e:
            self.logger.error(f"Error responding to lotto add-user command: {e}")
            await ctx.respond("❌ 發生錯誤，請稍後再試", ephemeral=True)

    @lotto_command_group.command(name="remove-user", description="從抽選池移除成員")
    async def remove_user(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(discord.Member, description="欲從抽選池移除的成員", required=True, default=None),
    ):  # type: ignore
        if user is None:
            await ctx.respond("❌ 請指定欲從抽選池移除的成員")
            return

        if not lotto.has_user(user.id):
            await ctx.respond(f"❌ <@{user.id}> 不在抽選池中")
            return

        lotto.remove_user(user.id)

        try:
            await ctx.respond(f"✅ 已將 <@{user.id}> 從抽選池移除")
        except Exception as e:
            self.logger.error(f"Error responding to lotto remove-user command: {e}")
            await ctx.respond("❌ 發生錯誤，請稍後再試", ephemeral=True)

    @lotto_command_group.command(name="list-users", description="列出抽選池中的成員")
    async def list_users(self, ctx: discord.ApplicationContext):  # type: ignore
        pool = lotto.list_pool()
        if not pool:
            await ctx.respond("抽選池目前沒有成員")
            return

        embed = discord.Embed(title="抽選池成員列表", color=discord.Color.blue())

        embed.description = "\n".join(f"<@{user_id}>" for user_id in pool)

        try:
            await ctx.respond(embed=embed)
        except Exception as e:
            self.logger.error(f"Error responding to lotto list-users command: {e}")
            await ctx.respond("❌ 發生錯誤，請稍後再試", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(Lotto(bot))
