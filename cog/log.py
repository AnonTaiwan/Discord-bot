import discord
from discord.ext import commands
import os
from datetime import datetime
import utils

class Log(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/log.py: 日誌系統初始化完成")
        
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
            await self.bot.close()
        else:
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 嘗試使用重啟指令，但沒有權限。")


def setup(bot: commands.Bot):
    bot.add_cog(Log(bot))