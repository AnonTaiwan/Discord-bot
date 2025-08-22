import discord
from discord.ext import commands, tasks
from curl_cffi import requests
from datetime import datetime, time
import pytz
import utils

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

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/health.py: 日誌系統初始化完成")
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(utils.TEST_CHANNEL_ID)

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

        self.logger.info("Health check completed and message sent.")

    @health_message.after_loop
    async def after_dayly_message(self):
        if self.health_message.is_running():
            now = datetime.now(timezone)
            if now not in health_message_time:
                self.health_message_sent = False

    @discord.slash_command(name='healthcheck', description='確認服務運作狀態')
    async def health_check_command(self, ctx: discord.ApplicationContext):
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用這個指令。", ephemeral=True)
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