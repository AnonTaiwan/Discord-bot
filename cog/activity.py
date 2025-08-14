import discord
from discord.ext import commands, bridge, tasks
import json
import logging
from datetime import datetime
import os

class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_logging()

    def setup_logging(self):
        """設置日誌系統"""
        # 創建 logs 目錄（如果不存在）
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # 設置日誌文件名（包含日期）
        log_filename = f'logs/activity_{datetime.now().strftime("%Y%m%d")}.log'
        
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
        self.logger.info("cog/activity.py: 日誌系統初始化完成")

    async def send_message(self, data):
        await self.get_photo(data)
        message = data.get('message', 'No message provided')
        message = bytes(message,'utf-8').decode(encoding="utf-8", errors="ignore")
        url = data.get('permalink_url', 'No URL provided').replace('\\','')
        embed = discord.Embed(title='Anon Taiwan 更新了新貼文！', url = url, color=0x00ff00)
        embed.add_field(name='貼文連結', value=url, inline=False)
        embed.add_field(name='貼文內容', value=message or "（無內容）", inline=False)
        file = discord.File(f"{data['id']}.jpg", filename=f"{data['id']}.jpg")
        embed.set_image(url=f"attachment://{data['id']}.jpg")
        # main setting
        # msg = await self.channel.send(content = '<@&1357315095235137636>', embed=embed, file=file)
        # test setting
        msg = await self.channel.send(content = '', embed=embed, file=file)
        await msg.publish()
        self.logger.info(f"已發送新貼文通知: {data['id']}")
        os.remove(f"{data['id']}.jpg")
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(1354880766126985358)
        print(f'activity.cog: {self.bot.user} (ID: {self.bot.user.id})')
        
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        self.logger.info(f"Member {before.name} (ID: {before.id}) presence updated")
        if before.status != after.status:
            self.logger.info(f"Member {after.name} changed status from {before.status} to {after.status}")
            # await self.channel.send(f"{after.mention} 的狀態已更新為: {after.status}")

def setup(bot: commands.Bot):
    bot.add_cog(Activity(bot))