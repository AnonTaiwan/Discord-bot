import discord
from discord.ext import commands, tasks
from curl_cffi import requests
import json
import logging
from datetime import datetime, time
import os
import pytz

timezone = pytz.timezone('Asia/Taipei')  # 設定時區為台北時間
health_message_time = [
    time(hour=0, minute=6, second=0, tzinfo=timezone),
    time(hour=8, minute=6, second=0, tzinfo=timezone),
    time(hour=16, minute=6, second=0, tzinfo=timezone),
]  # 每日訊息時間設定

health_check_endpoints = [
    'https://anontaiwan.meme',
    'https://urls.anontaiwan.meme',
]  # 網頁服務檢查端點

class Health(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.health_message_sent = False
        self.setup_logging()
        with open('JSON/bot.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.DEVELOPER = config.get("DEVELOPER")

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
        self.logger.info("cog/health.py: 日誌系統初始化完成")
        
    @commands.Cog.listener()
    async def on_ready(self):
        # main channel
        self.channel = self.bot.get_channel(1357294484903297127)
        # test channel
        # self.channel = self.bot.get_channel(1404889560068001864)

        self.health_message.start()
        
    @tasks.loop(time=health_message_time)
    async def health_message(self):
        if self.health_message_sent:
            return
        
        try:
            message = await self.channel.send("正在確認服務運作狀態...")
            self.health_message_sent = True

            await self._health_check(message)
        except Exception as e:
            self.logger.error(f"Error sending daily message: {e}")

    @health_message.after_loop
    async def after_dayly_message(self):
        if self.health_message.is_running():
            now = datetime.now(timezone)
            if now not in health_message_time:
                self.health_message_sent = False
                self.logger.info("Health Check 訊息已重置。")

    @discord.slash_command(name='healthcheck', description='確認服務運作狀態')
    async def health_check_command(self, ctx: discord.ApplicationContext):
        if ctx.author.id not in self.DEVELOPER:
            await ctx.respond("你沒有權限使用這個指令。", ephemeral=True)
            return
        
        message = await ctx.respond("正在確認服務運作狀態...")
        await self._health_check(message)

    async def _health_check(self, message: discord.Message):
        try:
            content = '### Health Check:'

            for endpoint in health_check_endpoints:
                response = requests.get(endpoint)
                if response.status_code == 200:
                    content += f'\n- ✅ <{endpoint}>'
                else:
                    content += f'\n- ❌ <{endpoint}>'
                await message.edit(content=content)
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

def setup(bot: commands.Bot):
    bot.add_cog(Health(bot))