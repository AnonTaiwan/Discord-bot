import discord
from discord.ext import commands, tasks
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
        self.date = datetime.now().strftime("%Y%m%d")

    async def setup_hook(self):
        for ext in self.initial_extensions:
            self.load_extension(ext)
            print(f"✅ 已加載擴展: {ext}")
        await self.sync_commands()
        self.logfile_update.start()
        self.auto_restart.start()

    async def on_ready(self):
        game = discord.Game("Blue Archive")
        print(f"✅ Logged in as {self.user}")
        await self.change_presence(status=discord.Status.online, activity=game)
        await self.setup_hook()
        self.remove_command("help")

    @tasks.loop(minutes=30)
    async def logfile_update(self):
        now = datetime.now().strftime("%Y%m%d")
        if now != self.date:
            log_filename = f'logs/fb_bot_{now}.log'
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                handlers=[
                    logging.FileHandler(log_filename, encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            global logger
            logger = logging.getLogger(__name__)
            logger.info("bot.py: 日誌時間更新")
            self.date = now

    @tasks.loop(hours=6)
    async def auto_restart(self):
        logger.info("⏰ 例行重啟機器人...")
        await self.close()
    @auto_restart.before_loop
    async def before_auto_restart(self):
        await asyncio.sleep(3600 * 6)

async def main():
    bot = MyBot()
    if not os.path.exists('logs'):
        os.makedirs('logs')
    log_filename = f'logs/fb_bot_{bot.date}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    global logger
    logger = logging.getLogger(__name__)
    logger.info("bot.py: 日誌系統初始化完成")
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())