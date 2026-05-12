import discord
from discord.ext import commands
import asyncio
import os
import logging
from datetime import datetime, timedelta, date, time
from pathlib import Path
import utils

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.date = datetime.now().strftime("%Y%m%d")
        self.initial_extensions = []
        for p in Path("./cog").iterdir():
            if p.suffix == ".py":
                self.initial_extensions.append(f"cog.{p.stem}")

    async def on_ready(self):
        game = discord.Game("🦪")
        print(f"✅ Logged in as {self.user}")
        await self.change_presence(status=discord.Status.online, activity=game)
        self.remove_command("help")
        # 防止斷線重連時重複創建 task
        if not hasattr(self, 'midnight_log_task'):
            self.midnight_log_task = self.loop.create_task(self.auto_update_log_at_midnight())

    def load_extensions(self):
        for ext in self.initial_extensions:
            try:
                self.load_extension(ext)
                print(f"✅ 已加載擴展：{ext}")
            except Exception as e:
                print(f"❌ 無法加載擴展 {ext}: {e}")

    def __unload_extensions(self):
        for ext in self.initial_extensions:
            self.unload_extension(ext)
            print(f"✅ 已卸載擴展：{ext}")

    async def auto_update_log_at_midnight(self):
        while True:
            now = datetime.now()
            # 算到下個 0 點還有幾秒
            tomorrow = datetime.combine(date.today() + timedelta(days=1), time.min)
            seconds_to_midnight = (tomorrow - now).seconds
            print(f"將於 {seconds_to_midnight + 5} 秒後更新日誌")
            await asyncio.sleep(seconds_to_midnight + 5)  # 加上 5 秒的偏移
            print('每日 12 點已到，正在更新日誌...')
            setup_daily_logger()  # 更新日誌設定



def setup_daily_logger():
    """設定每日日誌"""
    # 清除現有的 handlers
    logging.getLogger().handlers.clear()

    # 創建日誌目錄
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_dir = Path('logs')
    if not log_dir.is_dir():
        log_dir.mkdir(parents=True, exist_ok=True)

    # 設定日誌檔案名稱
    log_file = log_dir / f'bot_{datetime.now():%Y%m%d}.log'

    # 重新配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ],
        force=True  # 強制重新設定
    )

    return logging.getLogger()

def setup_tmp_dir():
    """確保 tmp 目錄存在"""
    tmp_dir = Path('tmp')
    if not tmp_dir.is_dir():
        tmp_dir.mkdir(parents=True, exist_ok=True)

async def main():
    logger = None
    current_date = None
    while True:
        now = datetime.now()
        today = now.strftime("%Y%m%d")

        # 檢查是否需要更新日誌檔案
        if current_date != today:
            logger = setup_daily_logger()
            current_date = today
            logger.info(f"日誌系統已更新至 {today}")

        setup_tmp_dir()

        async with MyBot() as bot:
            try:
                if os.environ.get("CI_RUNNING") == "true":
                    logger.info("CI 環境中，將不會啟動機器人")
                    await asyncio.sleep(30)

                async with bot:
                    bot.load_extensions()
                    # 交由外層 while-loop 負責重啟，避免在關閉時與內部重連產生競態
                    await bot.start(utils.BOT_TOKEN)
            finally:
                # 確保正常關閉，避免殘留資源或已關閉的會話被重用
                if not bot.is_closed():
                    await bot.close()
        await asyncio.sleep(10)  # 確保在重啟前有短暫的延遲

if __name__ == "__main__":
    asyncio.run(main())
