import discord
from discord.ext import commands
import importlib
import subprocess
import sys
import asyncio
import os
from datetime import datetime
import utils

class Environment(commands.Cog):
    """自動檢查並安裝缺少的 Python 套件"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        asyncio.create_task(self.pip_install('curl_cffi'))

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/enviroment.py: 日誌系統初始化完成")

        self.date = datetime.now().strftime("%Y%m%d")

    async def pip_install(self, package: str, import_name: str = ""):
        """安裝指定的 pip 套件（可選 import 名稱）"""
        try:
            importlib.import_module(import_name or package)
        except ImportError:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except Exception as e:
                print(e)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content == '!JSON_Update' and message.author.id in utils.DEVELOPER and message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith('.json'):
                    path = os.path.join('JSON', attachment.filename)
                    # 修正：將 str 轉為 Path 物件以符合 save 的型別要求
                    from pathlib import Path
                    path_obj = Path(path)
                    await attachment.save(fp=path_obj)
                    await message.channel.send(f"♻️ 已更新 `{attachment.filename}`")
                    # 使用 display_name 以支援 User/Member
                    author_name = getattr(message.author, "display_name", getattr(message.author, "name", "未知用戶"))
                    self.logger.info(f'{author_name} 更新了 {attachment.filename}')

def setup(bot: commands.Bot):
    bot.add_cog(Environment(bot))
