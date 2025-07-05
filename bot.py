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
        self.auto_restart.start()
        self.night_shutdown.start() 

    async def on_ready(self):
        game = discord.Game("Blue Archive")
        print(f"✅ Logged in as {self.user}")
        await self.change_presence(status=discord.Status.online, activity=game)
        await self.setup_hook()
        self.remove_command("help")

    @tasks.loop(hours=6)
    async def auto_restart(self):
        logger.info("⏰ 例行重啟機器人...") #type:ignore
        await self.close()
    @auto_restart.before_loop
    async def before_auto_restart(self):
        await asyncio.sleep(3600 * 6)

    @tasks.loop(minutes=5)
    async def night_shutdown(self):
        now = datetime.now()
        # 如果現在時間在 0:00 ~ 8:00
        if 0 <= now.hour < 8:
            logger.info("⏰ 到了夜間關機時段，自動關閉機器人") #type:ignore
            logger = None
            await self.close()

async def main():
    while True:
        now = datetime.now()
        if 0 <= now.hour < 8:
            # 算出距離8點還有幾秒
            seconds_to_8 = ((8 - now.hour) * 3600 - now.minute * 60 - now.second)
            print(f"夜間關機，將於 {seconds_to_8} 秒後自動開機")
            await asyncio.sleep(seconds_to_8)
            continue  # 跳過這次，等到8點再啟動
        
        if not os.path.exists('logs'):
            os.makedirs('logs')
        log_filename = f'logs/fb_bot_{datetime.now().strftime("%Y%m%d")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info("bot.py: 日誌系統初始化完成")
        bot = MyBot()
        await bot.start(TOKEN)

if __name__ == "__main__":
    global logger
    logger = None
    asyncio.run(main())