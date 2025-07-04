import discord
from discord.ext import commands, tasks
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
        self.date = datetime.now().strftime("%Y%m%d")
        self.LogFile_Update.start()
        
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
        if message.content == '!JSON_Update' and message.author.id in DEVELOPER and message.attachments:
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

    @tasks.loop(minutes = 10)
    async def LogFile_Update(self):
        now = datetime.now().strftime("%Y%m%d")
        if now != self.date:
            if not os.path.exists('logs'):
                os.makedirs('logs')

            # 設置日誌文件名（包含日期）
            log_filename = f'logs/fb_bot_{datetime.now().strftime("%Y%m%d")}.log'

            # 配置日誌格式
            log_format = '%(asctime)s - %(levelname)s - %(message)s'
            date_format = '%Y-%m-%d %H:%M:%S'

            # 配置日誌
            logging.basicConfig(level=logging.INFO, format=log_format, datefmt=date_format,
                handlers=[
                    logging.FileHandler(log_filename, encoding='utf-8'),
                    logging.StreamHandler()  # 同時輸出到控制台
            ])
            self.logger = logging.getLogger(__name__)
            self.date = now
            self.logger.info("bot.py: 日誌時間更新")
 
    
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
        self.logger.info("cog/fb.py: 日誌系統初始化完成")

       
def setup(bot: commands.Bot):
    bot.add_cog(Environment(bot))