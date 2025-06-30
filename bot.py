import discord
from discord.ext import commands
import asyncio
import os
import logging
from datetime import datetime

TOKEN = "OTk3MjAyMzk4NDg3NTE5MzAz.GSH0uw.dHWYigfeu43GUZMD9pM9hozr-hN8UjKlHq6nQ8"
DEVELOPER = [330256191127289856, 705432231304495205]


class MyBot(commands.Bot):

    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.initial_extensions = [
            f"cog.{i[:-3]}" for i in os.listdir("./cog") if i.endswith(".py")
        ]
        for ext in self.initial_extensions:
            self.load_extension(ext)
            print(f"✅ 已加載擴展: {ext}")
            
    async def on_ready(self):
        game = discord.Game("Blue Archive")
        print(f"✅ Logged in as {self.user}")
        await self.change_presence(status=discord.Status.online, activity=game)
        self.remove_command("help")
        await self.sync_commands()
        self.loop.create_task(auto_restart(self))
        self.loop.create_task(LogFile_Update())
        



async def main():
    while True:
        bot = MyBot()
        try:
            await bot.start(TOKEN)
        except KeyboardInterrupt:
            logger.info("⏹️ Bot stopped by user.")
            break
        logger.info("🔄 Restarting bot...")

async def LogFile_Update():
    await asyncio.sleep(1800)
    now = datetime.now().strftime("%Y%m%d")
    if now != date:
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
        logger = logging.getLogger(__name__)
        logger.info("bot.py: 日誌時間更新")

async def auto_restart(bot, delay_sec= 3600 * 3):
    await asyncio.sleep(delay_sec)
    logger.info("⏰ 例行重啟機器人...")
    await bot.close()


if __name__ == "__main__":
    global date 
    date = datetime.now().strftime("%Y%m%d")
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
    logging.basicConfig(level=logging.INFO, format=log_format, datefmt=date_format,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # 同時輸出到控制台
        ])
    global logger
    logger = logging.getLogger(__name__)
    logger.info("bot.py: 日誌系統初始化完成")
    asyncio.run(main())
