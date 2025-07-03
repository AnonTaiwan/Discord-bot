from discord.ext import commands, tasks
from discord import Option, File
import discord
import os
import asyncio
import logging
from datetime import datetime
DEVELOPER = [330256191127289856, 705432231304495205]

class CogManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_logging()
        self.date = datetime.now().strftime("%Y%m%d")
        self.LogFile_Update.start()
    
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
        
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.content == '!Cog_Update' and message.attachments and message.author.id in DEVELOPER:
            # 檢查是否有附加檔案
            for attachment in message.attachments:
                if attachment.filename.endswith('.py'):
                    # 假設所有 cog 都在 cog 資料夾中
                    # 儲存檔案
                    from pathlib import Path
                    cog_path_obj = Path(f'cog/{attachment.filename}')
                    await attachment.save(fp=cog_path_obj)
                    await message.channel.send(f"✅ 已更新 `{attachment.filename}`")
                    self.logger.info(f'{message.author.name}: 更新 {attachment.filename}')

                    # 取得 cog 的模組名稱（例如：cog.my_cog）
                    cog_name = 'cog.' + attachment.filename[:-3]  # 去掉 .py

                    try:
                        # 如果已加載，先卸載
                        if cog_name in self.bot.extensions:
                            self.bot.reload_extension(cog_name)
                            self.logger.info(f'♻️ 已重新加載 `{cog_name}`')
                            await message.channel.send(f"♻️ 已重新加載 `{cog_name}`")
                        else:
                            self.bot.load_extension(cog_name)
                            self.logger.info(f'📥 已載入新的 Cog `{cog_name}`')
                            await message.channel.send(f"📥 已載入新的 Cog `{cog_name}`")
                    except Exception as e:
                        self.logger.warning(f'❌ 加載失敗: `{e}`')
                        await message.channel.send(f"❌ 加載失敗: `{e}`")


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
 

def setup(bot: commands.Bot):
    bot.add_cog(CogManager(bot))
