import chat_exporter
import io
import asyncio

import discord
from discord.ext import commands

from internal import utils


class ManageCog(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/manage.py: 管理系統初始化完成")


    @commands.Cog.listener()
    async def on_ready(self):
        utils.get_logger(__name__).info("ManageCog 已準備就緒")
        pass

    command_group = discord.SlashCommandGroup("delete", "刪除相關指令")

    class CloseConfirmation(discord.ui.View):
        def __init__(self, channel: discord.TextChannel):
            super().__init__(timeout=None)
            self.value = None
            self.channel = channel

        async def record_channel_message(self, channel: discord.TextChannel):
            """在指定頻道記錄訊息"""
            transcript = await chat_exporter.export(channel, limit=None, tz_info="Asia/Taipei")
            channel_log_channel = self.bot.get_channel(utils.CHANNEL_LOG_CHANNEL_ID)

            if channel_log_channel is not None and transcript is not None:
                file = discord.File(io.BytesIO(transcript.encode()), filename=f"{channel.name}.html")
                await channel_log_channel.send(file=file)

        @discord.ui.button(label="確認刪除", style=discord.ButtonStyle.danger)
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            try:
                await interaction.response.send_message(f"頻道 {self.channel.mention} 將被刪除。", ephemeral=True)
                await self.record_channel_message(self.channel)
                await self.channel.delete(reason=f"Channel deleted by {interaction.user} via ManageCog.")

            except Exception as e:
                utils.get_logger(__name__).error(f"Error exporting channel messages: {e}")
                await interaction.response.send_message("無法導出工單紀錄。", ephemeral=True)

        @discord.ui.button(label="取消", style=discord.ButtonStyle.secondary)
        async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
            await interaction.response.send_message("已取消刪除頻道。", ephemeral=True)

    @command_group.command(name="channel", description="刪除指定頻道")
    async def delete_channel(
        self, ctx: discord.ApplicationContext, channel: discord.Option(discord.TextChannel, "選擇要刪除的頻道", default=None)
    ):  # type: ignore
        if not utils.is_operator(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name}嘗試使用刪除頻道指令，但沒有權限。")
            return
        else:
            """刪除指定頻道"""
            if channel is None:
                channel = ctx.channel  # 如果沒有指定頻道，則使用當前頻道

            embed = discord.Embed(
                title="確認刪除頻道", description=f"你確定要刪除頻道 {channel.mention} 嗎？此操作無法復原。", color=discord.Color.red()
            )
            view = self.CloseConfirmation(channel)

            await ctx.respond(embed=embed, view=view, ephemeral=True)
            self.logger.info(f"⚠️ {ctx.author.name} 嘗試刪除頻道 {channel.name}，等待確認中。")


def setup(bot):
    bot.add_cog(ManageCog(bot))
