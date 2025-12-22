import discord
from discord.ext import commands
import os
import asyncio
import sys
from datetime import datetime
import utils
import chat_exporter
import io

class Log(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/log.py: 日誌系統初始化完成")
        
    async def record_channel_message(self, channel: discord.TextChannel):
        """在指定頻道記錄訊息"""
        transcript = await chat_exporter.export(channel, limit=None, tz_info="Asia/Taipei")
        channel_log_channel = self.bot.get_channel(utils.CHANNEL_LOG_CHANNEL_ID)
        
        if channel_log_channel is not None and transcript is not None:
            file = discord.File(io.BytesIO(transcript.encode()), filename=f"{channel.name}.html")
            await channel_log_channel.send(file=file)
        
    @discord.slash_command(name="record_channel", description="記錄指定頻道的訊息")
    async def record_channel(self, ctx: discord.ApplicationContext, channel: discord.Option(discord.TextChannel, "選擇要記錄的頻道", default=None)): # type: ignore
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
            
    @discord.slash_command(name="delete_channel", description="刪除指定頻道")
    async def delete_channel(self, ctx: discord.ApplicationContext, channel: discord.Option(discord.TextChannel, "選擇要刪除的頻道", default=None)): # type: ignore
        if not utils.is_operator(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name}嘗試使用刪除頻道指令，但沒有權限。")
            return
        else:
            """刪除指定頻道"""
            if channel is None:
                channel = ctx.channel  # 如果沒有指定頻道，則使用當前頻道
            await ctx.respond(f"正在記錄頻道 {channel.mention} 的訊息...", ephemeral=True)
            await self.record_channel_message(channel)
            await channel.delete(reason=f"由 {ctx.author} 使用指令刪除")
            self.logger.info(f"✅ {ctx.author.name} 使用指令刪除頻道 {channel.name}。")
        
    @discord.slash_command(name="log", description="查看日誌")
    async def log(self, ctx: discord.ApplicationContext, date: str = discord.Option(default=None, description="你想查詢的日期，例如 20250627")): # type: ignore
        if ctx.author.id not in utils.DEVELOPER:
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name}嘗試使用日誌指令，但沒有權限。")
            return
        else:
            """查看日誌"""
            # 確保 logs 目錄存在
            if not os.path.exists('logs'):
                await ctx.respond("日誌目錄不存在。")
                return
            if date is None:
                # 設置日誌文件名（包含日期）
                log_filename = utils.LOGS_DIR / f'bot_{datetime.now().strftime("%Y%m%d")}.log'
            else:
                log_filename = utils.LOGS_DIR / f'bot_{date}.log'

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


def setup(bot: commands.Bot):
    bot.add_cog(Log(bot))