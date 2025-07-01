import discord
from discord.ext import commands
import importlib
import subprocess
import sys
import asyncio
import logging
import os
from datetime import datetime

DEVELOPER = [330256191127289856, 705432231304495205]

class Environment(commands.Cog):
    """自動檢查並安裝缺少的 Python 套件"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        asyncio.create_task(self.pip_install('curl_cffi'))
        self.setup_logging()
        
    async def pip_install(self, package: str, import_name: str = None):
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
        if message.content == '!JSON_Update' and message.author.id in DEVELOPER and message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith('.json'):
                    path = f'JSON/{attachment.filename}'
                    await attachment.save(fp=path)
                    await message.channel.send(f"♻️ 已更新 `{attachment.filename}`")
                    self.logger.info(f'{message.author.nick} 更新了 {attachment.filename}')
    
    def setup_logging(self):
        """設置日誌系統"""
        # 創建 logs 目錄（如果不存在）
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # 設置日誌文件名（包含日期）
        log_filename = f'logs/fb_bot_{datetime.now().strftime("%Y%m%d")}.log'
        
        # 配置日誌格式
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # 配置日誌
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()  # 同時輸出到控制台
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("cog/cogupdate.py: 日誌系統初始化完成")
       
def setup(bot: commands.Bot):
    bot.add_cog(Environment(bot))