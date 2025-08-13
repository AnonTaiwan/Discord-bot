import discord
from discord.ext import commands, tasks
import asyncio
import os
import time
import logging
from datetime import datetime, timedelta
import json

with open("JSON/bot.json", "r", encoding="utf-8") as f:
    config = json.load(f)
TOKEN = config.get("TOKEN")
DEVELOPER = config.get("DEVELOPER")

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.initial_extensions = [
            f"cog.{i[:-3]}" for i in os.listdir("./cog") if i.endswith(".py")
        ]
        self.date = datetime.now().strftime("%Y%m%d")
        for ext in self.initial_extensions:
            self.load_extension(ext)
            print(f"✅ 已加載擴展: {ext}")

    async def on_ready(self):
        game = discord.Game("Blue Archive")
        print(f"✅ Logged in as {self.user}")
        await self.change_presence(status=discord.Status.online, activity=game)
        self.remove_command("help")
        self.loop.create_task(self.auto_shutdown_at_midnight())

    async def auto_shutdown_at_midnight(self):
        now = datetime.now()
        if now.hour == 0:
            print("已到 0 點，立即關機")
            for ext in self.initial_extensions:
                self.unload_extension(ext)
                print(f"✅ 已卸載擴展: {ext}")
            await self.close()
        else:
            # 算到下個 0 點還有幾秒
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_to_midnight = int((tomorrow - now).total_seconds())
            print(f"將於 {seconds_to_midnight + 5} 秒後自動關機")
            await asyncio.sleep(seconds_to_midnight + 5)
            print('每日12點自動關機')
            for ext in self.initial_extensions:
                self.unload_extension(ext)
                print(f"✅ 已卸載擴展: {ext}")
            await self.close()


def setup_daily_logger():
    """設定每日日誌"""
    # 清除現有的 handlers
    logging.getLogger().handlers.clear()
    
    # 創建日誌目錄
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 設定日誌檔案名稱
    log_filename = f'logs/fb_bot_{datetime.now().strftime("%Y%m%d")}.log'
    
    # 重新配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ],
        force=True  # 強制重新設定
    )
    
    return logging.getLogger()

async def main():
    current_date = None
    while True:
        current_hour = datetime.now()
        if 0 <= current_hour.hour < 8:
            # 算出距離8點還有幾秒
            seconds_to_8 = ((8 - current_hour.hour) * 3600 - current_hour.minute * 60 - current_hour.second)
            print(f"夜間關機，將於 {seconds_to_8} 秒後自動開機")
            time.sleep(seconds_to_8 + 5)
            continue  # 跳過這次，等到8點再啟動
        
        now = datetime.now()
        today = now.strftime("%Y%m%d")
        
        # 檢查是否需要更新日誌檔案
        if current_date != today:
            logger = setup_daily_logger()
            current_date = today
            logger.info(f"日誌系統已更新至 {today}")
            
        bot = MyBot()

        if os.environ.get("CI_RUNNING") == "true":
            logger.info("CI 環境中，將不會啟動機器人")
            await asyncio.sleep(30)

        await bot.start(TOKEN)
        del bot

if __name__ == "__main__":
    global logger
    logger = None
    asyncio.run(main())