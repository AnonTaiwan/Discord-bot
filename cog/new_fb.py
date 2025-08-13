import discord
from discord.ext import commands, bridge, tasks
from curl_cffi import requests
import json
import logging
from datetime import datetime
import os

class NewFB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.latest = []
        # main channel
        # self.channel = self.bot.get_channel(1357294484903297127)
        # test channel
        self.channel = self.bot.get_channel(1404889560068001864)
        self.setup_logging()
    
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
        self.logger.info("cog/fb.py: 日誌系統初始化完成")
    
    def get_datas(self):
        response = requests.get('https://graph.facebook.com/v23.0/419295154604542/posts?fields=message,created_time,full_picture,permalink_url,shares&access_token=EAAOZC1rBgpBoBPIZAr87f4ZBLD5w16FfWRNb099nL0QBpVkBtZAg4ZB9nQmapg6TezqXdz8uAKwV3BIHUu3igotisHk7dZBMGHFwqiJ5cvhhHN5HEF4bgvZAvmdgP97tUn2s7XhaPt0VhaVxQzbzaKTqcfA27RdEtvZCFyEGMX2WF5YkZBms1Tl8h8m8CXTH9y0rP9Fp4821qAdjyPYZBzG0ho3u33&limit=3')
        datas = json.loads(response.text)
        return datas['data']
            
    async def get_photo(self,data):
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-TW,zh;q=0.9',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        }
        url = data['full_picture'].replace('\\','')
        response = requests.get(url, headers=headers)
        with open(f'{data['id']}.jpg','wb') as f:
            f.write(response.content)

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
        datas = self.get_datas()
        self.latest = [i['id'] for i in datas]
        self.check_for_updates.start()
        print(f'new_fb.cog: {self.bot.user} (ID: {self.bot.user.id})')
        
    @tasks.loop(minutes=1)
    async def check_for_updates(self):
        try:
            datas = self.get_datas()
            new_post = [i for i in datas if i['id'] not in self.latest]
            if new_post:
                self.logger.info(f"發現 {len(new_post)} 條新貼文")
                for post in new_post:
                    await self.send_message(post)
                self.latest = [i['id'] for i in datas]
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")

def setup(bot: commands.Bot):
    bot.add_cog(NewFB(bot))