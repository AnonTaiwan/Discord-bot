import asyncio
from datetime import time

import discord
from curl_cffi import requests
from discord.ext import commands, tasks

from internal import utils
from model.log import log_task

health_message_time = [
    time(hour=0, minute=0, second=0, tzinfo=utils.TIME_ZONE),
    time(hour=8, minute=0, second=0, tzinfo=utils.TIME_ZONE),
    time(hour=16, minute=0, second=0, tzinfo=utils.TIME_ZONE),
]  # 每日訊息時間設定

health_check_endpoints = [
    "https://anontaiwan.meme",
    # 'https://urls.anontaiwan.meme'
]  # 網頁服務檢查端點


class Health(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/health.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(utils.TEST_CHANNEL_ID)

        if not self.health_message.is_running():
            self.health_message.start()

    @tasks.loop(time=health_message_time)
    @log_task("health_message")
    async def health_message(self):
        try:
            message = await self.channel.send("正在確認服務運作狀態...")

            await self.__health_check(message)
        except Exception as e:
            self.logger.error(f"Error sending daily message: {e}")

        self.logger.info("Health check completed and message sent.")

    @discord.slash_command(name="healthcheck", description="確認服務運作狀態")
    async def health_check_command(self, ctx: discord.ApplicationContext):
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用這個指令。", ephemeral=True)
            return

        message = await ctx.respond("正在確認服務運作狀態...")
        await self.__health_check(message)

    async def __health_check(self, message: discord.Message | discord.Interaction):
        try:
            content = "### Health Check:"

            for endpoint in health_check_endpoints:
                # 使用 asyncio.to_thread 避免阻塞事件循環，並添加 5 秒超時
                try:
                    response = await asyncio.wait_for(asyncio.to_thread(requests.get, endpoint, timeout=5), timeout=10)
                    if response.status_code == 200:
                        content += f"\n- ✅ <{endpoint}>"
                    else:
                        content += f"\n- ❌ <{endpoint}> (Status: {response.status_code})"
                except asyncio.TimeoutError:
                    content += f"\n- ⏱️ <{endpoint}> (Timeout)"
                    self.logger.warning(f"Health check timeout for {endpoint}")
                except Exception as e:
                    content += f"\n- ❌ <{endpoint}> (Error: {str(e)[:50]})"
                    self.logger.error(f"Health check error for {endpoint}: {e}")

                await message.edit(content=content)
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False


def setup(bot: commands.Bot):
    bot.add_cog(Health(bot))
