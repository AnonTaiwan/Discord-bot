from datetime import timedelta
import logging
import discord
from discord.ext import commands
from internal import utils
from internal.rate_limit import SlidingWindowRateLimiter


TIMEOUT_DURATION_OPTIONS = [
    "60 秒",
    "5 分",
    "10 分",
    "1 小時",
    "1 天",
    "1 週",
]

TIMEOUT_DURATION_MAP = {
    "60 秒": timedelta(seconds=60),
    "5 分": timedelta(minutes=5),
    "10 分": timedelta(minutes=10),
    "1 小時": timedelta(hours=1),
    "1 天": timedelta(days=1),
    "1 週": timedelta(weeks=1),
}


class TimeoutRequestView(discord.ui.View):
    def __init__(self, logger: logging.Logger, requester: discord.Member | discord.User, target: discord.Member, duration_label: str):
        super().__init__(timeout=None)
        self.logger = logger
        self.requester = requester
        self.target = target
        self.duration_label = duration_label

    def build_request_embed(self) -> discord.Embed:
        embed = discord.Embed(
            description=f"{self.target.mention}，請問您是否同意被禁言 {self.duration_label}",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Requester", value=self.requester.mention, inline=False)
        return embed

    def build_result_embed(self, message: str, color: discord.Color) -> discord.Embed:
        embed = discord.Embed(description=message, color=color)
        return embed

    async def _finalize(self, interaction: discord.Interaction, embed: discord.Embed) -> None:
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="同意", style=discord.ButtonStyle.success)
    async def agree(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user is None or interaction.user.id != self.target.id:
            await interaction.response.send_message("❌ 只有被請求禁言的使用者才能操作這個按鈕。", ephemeral=True)
            return

        try:
            await self.target.timeout_for(
                self.__class__._duration_from_label(self.duration_label),
                reason=f"Timeout request approved by {interaction.user} for {self.requester}",
            )

            embed = self.build_result_embed(
                f"{self.target.mention} 已同意被 {self.requester.mention} 禁言 {self.duration_label}",
                discord.Color.green(),
            )
            await self._finalize(interaction, embed)
        except discord.Forbidden:
            embed = self.build_result_embed(
                f"❌ 我沒有權限禁言 {self.target.mention}",
                discord.Color.red(),
            )
            await self._finalize(interaction, embed)
        except Exception as e:
            self.logger.error(f"Timeout request approve failed: {e}")
            await interaction.response.send_message("❌ 執行禁言時發生錯誤。", ephemeral=True)

    @discord.ui.button(label="拒絕", style=discord.ButtonStyle.danger)
    async def reject(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user is None or interaction.user.id != self.target.id:
            await interaction.response.send_message("❌ 只有被請求禁言的使用者才能操作這個按鈕。", ephemeral=True)
            return

        embed = self.build_result_embed(
            f"{self.target.mention} 拒絕被 {self.requester.mention} 禁言 {self.duration_label}",
            discord.Color.red(),
        )
        await self._finalize(interaction, embed)

    @staticmethod
    def _duration_from_label(label: str) -> timedelta:
        return TIMEOUT_DURATION_MAP[label]


class FunPunish(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/fun_punish.py: 日誌系統初始化完成")

        self.rate_limiter = SlidingWindowRateLimiter(limit=3, window_seconds=60)

    @discord.slash_command(name="timeout-request", description="向指定成員發出禁言請求")
    async def timeout_request(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(discord.Member, description="要請求禁言的成員", required=True),  # type: ignore
        duration: discord.Option(str, description="禁言時間", required=True, choices=TIMEOUT_DURATION_OPTIONS),  # type: ignore
    ):
        if not utils.is_operator(ctx.author):
            allowed, retry_after = self.rate_limiter.allow((ctx.author.id, "timeout-request"))

            if not allowed:
                await ctx.respond(f"❌ 操作過於頻繁，請在 {retry_after:.0f} 秒後再試。", ephemeral=True)
                return

        view = TimeoutRequestView(self.logger, ctx.author, user, duration)
        await ctx.respond(embed=view.build_request_embed(), view=view)

    @discord.slash_command(name="self-timeout-request", description="發出禁言自己的請求")
    async def self_timeout_request(
        self,
        ctx: discord.ApplicationContext,
        duration: discord.Option(str, description="禁言時間", required=True, choices=TIMEOUT_DURATION_OPTIONS),  # type: ignore
    ):
        view = TimeoutRequestView(self.logger, ctx.author, ctx.author, duration)
        await ctx.respond(embed=view.build_request_embed(), view=view)


def setup(bot: commands.Bot):
    bot.add_cog(FunPunish(bot))
