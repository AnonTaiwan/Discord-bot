import asyncio
import os
import sys
from datetime import datetime

import discord
from discord.ext import commands

from internal import utils
from model.log import CommandLog, record_log


class Log(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/log.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext):
        options = []
        if ctx.selected_options:
            for opt in ctx.selected_options:
                options.append(f"{opt['name']}={opt['value']}")
        opt_str = " ".join(options)
        command_content = f"/{ctx.command.qualified_name}"
        if opt_str:
            command_content += f" {opt_str}"

        record_log(
            user_name=ctx.author.name,
            command_content=command_content,
            user_id=ctx.author.id,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.content and message.content.startswith("!"):
            if message.author.id in utils.DEVELOPER:
                record_log(
                    user_name=message.author.name,
                    command_content=message.content,
                    user_id=message.author.id,
                )

    @discord.slash_command(name="record_channel", description="記錄指定頻道的訊息")
    async def record_channel(
        self, ctx: discord.ApplicationContext, channel: discord.Option(discord.TextChannel, "選擇要記錄的頻道", default=None)
    ):  # type: ignore
        if not utils.is_operator(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name}嘗試使用記錄頻道指令，但沒有權限。")
            return
        else:
            """記錄指定頻道的訊息"""
            if channel is None:
                channel = ctx.channel  # 如果沒有指定頻道，則使用當前頻道
            await ctx.respond(f"正在記錄頻道 {channel.mention} 的訊息...", ephemeral=True)
            await self.record_channel_message(channel)
            self.logger.info(f"✅ {ctx.author.name} 使用指令記錄頻道 {channel.name} 的訊息。")
            await ctx.followup.send(f"✅ 頻道 {channel.mention} 的訊息已記錄完成。", ephemeral=True)

    @discord.slash_command(name="log", description="查看日誌")
    async def log(
        self, ctx: discord.ApplicationContext, date: str = discord.Option(default=None, description="你想查詢的日期，例如 20250627")
    ):  # type: ignore
        if ctx.author.id not in utils.DEVELOPER:
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name}嘗試使用日誌指令，但沒有權限。")
            return
        else:
            """查看日誌"""
            # 確保 logs 目錄存在
            if not os.path.exists("logs"):
                await ctx.respond("日誌目錄不存在。")
                return
            if date is None:
                # 設置日誌文件名（包含日期）
                log_filename = utils.LOGS_DIR / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
            else:
                log_filename = utils.LOGS_DIR / f"bot_{date}.log"

            # 檢查日誌文件是否存在
            if not os.path.isfile(log_filename):
                await ctx.respond("當日的日誌文件不存在。")
                return

            # 發送日誌內容
            await ctx.respond(file=discord.File(log_filename))
            self.logger.info(f"日誌文件 {log_filename} 已發送給 {ctx.author.name}")

    @discord.slash_command(name="restart", description="重啟機器人")
    async def restart(self, ctx: discord.ApplicationContext):
        if ctx.author.id in utils.DEVELOPER:
            await ctx.respond("🔄 機器人正在重啟...", ephemeral=True)
            self.logger.info(f"🔄 {ctx.author.name} 使用指令重啟機器人")
            # 進程內重啟（re-exec）：重新以相同參數啟動程式，避免僅關閉導致 RESUME 使用已關閉 Session
            await asyncio.sleep(1)
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 嘗試使用重啟指令，但沒有權限。")

    @discord.slash_command(name="command_history", description="查看指令與任務的執行歷史紀錄")
    async def command_history(
        self,
        ctx: discord.ApplicationContext,
        limit: discord.Option(int, description="顯示筆數 (1-50)", min_value=1, max_value=50, default=10),  # type: ignore
        filter_type: discord.Option(
            str,
            description="篩選紀錄類型",
            choices=["All", "Slash Command", "Text Command", "Background Task"],
            default="All",
        ),  # type: ignore
        user: discord.Option(discord.User, description="篩選特定使用者", default=None, required=False),  # type: ignore
    ):
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return

        from sqlmodel import select

        from internal import db

        try:
            await ctx.defer(ephemeral=True)
        except Exception:
            pass

        try:
            with db.get_session() as session:
                sql = select(CommandLog)
                if user:
                    sql = sql.where(CommandLog.user_id == user.id)

                if filter_type == "Slash Command":
                    sql = sql.where(CommandLog.command_content.like("/%"))
                elif filter_type == "Text Command":
                    sql = sql.where(CommandLog.command_content.like("!%"))
                elif filter_type == "Background Task":
                    sql = sql.where(CommandLog.command_content.like("Task:%"))

                sql = sql.order_by(CommandLog.id.desc()).limit(limit)
                results = session.exec(sql).all()

            if not results:
                await ctx.respond("沒有找到任何符合的紀錄。", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"📋 指令與任務執行歷史紀錄 (最新 {len(results)} 筆)",
                color=discord.Color.blue(),
                timestamp=datetime.now(utils.TIME_ZONE),
            )

            lines = []
            for r in results:
                time_str = r.time.strftime("%m-%d %H:%M:%S")
                user_info = f"**{r.user_name}**"
                if r.user_id:
                    user_info += f" ({r.user_id})"

                lines.append(f"`[{time_str}]` {user_info}: `{r.command_content}`")

            embed.description = "\n".join(lines)
            if len(embed.description) > 4096:
                embed.description = embed.description[:4000] + "\n... (內容過長已截斷)"

            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error querying command history: {e}")
            await ctx.respond(f"❌ 查詢時發生錯誤: {e}", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(Log(bot))
