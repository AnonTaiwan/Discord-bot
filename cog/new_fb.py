import discord
from discord.ext import commands, tasks
from curl_cffi import requests
import json
import logging
from datetime import datetime, timedelta, time
import os
import pytz
from PIL import Image, ImageDraw, ImageFont

timezone = pytz.timezone('Asia/Taipei')  # 設定時區為台北時間
daily_message_time = time(hour=16, minute=45, second=0, tzinfo=timezone)  # 每日訊息時間設定

class NewFB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.latest = []
        self.daily_message_sent = False
        self.setup_logging()
        with open('JSON/bot.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.FACEBOOK_TOKEN = config.get("FACEBOOK_TOKEN")
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
        self.logger.info("cog/new_fb.py: 日誌系統初始化完成")
    
    def get_datas(self, limit=3):
        response = requests.get(f'https://graph.facebook.com/v23.0/419295154604542/posts?fields=message,created_time,full_picture,permalink_url,shares&access_token={self.FACEBOOK_TOKEN}&limit={limit}')
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

    async def _send_update_message(self, data_id, embed, file):
        msg = await self.channel.send(content = '', embed=embed, file=file)
        await msg.publish()
        self.logger.info(f"已發送新貼文通知: {data_id}")
        os.remove(f"{data_id}.jpg")

    async def _send_post_update_message(self, data):
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
        await self._send_update_message(data['id'], embed, file)
    
    async def _send_reel_update_message(self, reel):
        reel_data_id = reel['id']
        url = f'https://www.facebook.com{reel['permalink_url'].replace('\\','')}'
        message = reel.get('description', 'No description provided')
        message = bytes(message,'utf-8').decode(encoding="utf-8", errors="ignore")
        picture_url = reel.get('picture', {}).get('url', '')
        with open(f'{reel_data_id}.jpg', 'wb') as f:
            f.write(requests.get(picture_url).content)
        embed = discord.Embed(title='Anon Taiwan 更新了新 Reel！', url=url, color=discord.Color.blue())
        file = discord.File(f"{reel_data_id}.jpg", filename=f"{reel_data_id}.jpg")
        embed.set_image(url=f"attachment://{reel_data_id}.jpg")
        embed.add_field(name='Reel 連結', value=url, inline=False)
        embed.add_field(name='Reel 內容', value=message or "（無內容）", inline=False)
        await self._send_update_message(reel_data_id, embed, file)
        
    @commands.Cog.listener()
    async def on_ready(self):
        datas = self.get_datas()
        self.latest = [i['id'] for i in datas]
        self.reel = requests.get(f'https://graph.facebook.com/v23.0/419295154604542/video_reels?fields=description,created_time,permalink_url&access_token={self.FACEBOOK_TOKEN}&limit=3').json()['data'][0]['id']
        self.check_post_updates.start()
        self.check_reel_updates.start()
        # main channel
        # self.channel = self.bot.get_channel(1357294484903297127)
        # test channel
        self.channel = self.bot.get_channel(1404889560068001864)

        self.daily_message.start()
        print(f'new_fb.cog: {self.bot.user} (ID: {self.bot.user.id})')
    
    @tasks.loop(minutes=1)
    async def check_post_updates(self):
        try:
            datas = self.get_datas()
            new_post = [i for i in datas if i['id'] not in self.latest]
            if new_post:
                self.logger.info(f"發現 {len(new_post)} 條新貼文")
                for post in new_post:
                    await self._send_post_update_message(post)
                self.latest = [i['id'] for i in datas]
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")

    @tasks.loop(minutes=5)
    async def check_reel_updates(self):
        try:
            response = requests.get(f'https://graph.facebook.com/v23.0/419295154604542/video_reels?fields=description,created_time,permalink_url,picture&access_token={self.FACEBOOK_TOKEN}&limit=3')
            reels_data = response.json()
            if self.reel != reels_data['data'][0]['id']:
                self.reel = reels_data['data'][0]['id']
                self._send_reel_update_message(reels_data['data'][0])
        except Exception as e:
            self.logger.error(f"Error checking for reels: {e}")

    def _formatted_time_to_unix_timestamp(self, formatted_time):
        try:
            dt = datetime.strptime(formatted_time, "%Y-%m-%d %H:%M:%S")
            localized_dt = self.timezone.localize(dt)
            return int(localized_dt.timestamp())
        except ValueError as e:
            self.logger.error(f"時間格式錯誤: {e}")
            return None
        
    def _get_posts_and_reels_count(self, start_timestamp, end_timestamp):
        try:
            response = requests.get(f'https://graph.facebook.com/v23.0/419295154604542/posts?fields=&access_token={self.FACEBOOK_TOKEN}&since={start_timestamp}&until={end_timestamp}&limit=100')
            posts_data = json.loads(response.text)
            posts_count = len(posts_data.get('data', []))

            response = requests.get(f'https://graph.facebook.com/v23.0/419295154604542/video_reels?fields=&access_token={self.FACEBOOK_TOKEN}&since={start_timestamp}&until={end_timestamp}&limit=100')
            reels_data = json.loads(response.text)
            reels_count = len(reels_data.get('data', []))

            return posts_count, reels_count
        except Exception as e:
            self.logger.error(f"Error fetching posts and reels count: {e}")
            return 0, 0

    def generate_daily_post_picture(self, posts_count, reels_count):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        background_path = os.path.join(current_dir, "../File/background.png")
        img = Image.open(background_path)
        draw = ImageDraw.Draw(img)
        font_path = os.path.join(current_dir, "../File/NotoSansTC-Bold.ttf")
        font = ImageFont.truetype(font_path, 150)
        coordinate = img.width // 2 - 100 , img.height // 2 -110
        draw.text(coordinate, f"{posts_count} 則貼文", font=font, fill=(0, 0, 0), anchor="mm")
        draw.text((coordinate[0], coordinate[1] + 400), f"{reels_count} 則Reels", font=font, fill=(0, 0, 0), anchor="mm")
        output_path = os.path.join("output.png")
        img.save(output_path, format='PNG', optimize=False)
        
    @tasks.loop(time=daily_message_time)
    async def daily_message(self):
        if self.daily_message_sent:
            return
        
        try:
            today = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = today - timedelta(days=1)
            today_timestamp = int(today.timestamp())
            yesterday_timestamp = int(yesterday.timestamp())
            posts_count, reels_count = self._get_posts_and_reels_count(yesterday_timestamp, today_timestamp)
            embed = discord.Embed(title='今日統整', color=discord.Color.blue())
            self.generate_daily_post_picture(posts_count, reels_count)
            file = discord.File("output.png", filename="output.png")
            embed.set_image(url="attachment://output.png")
            channel = self.bot.get_channel(1405253533540024340)
            await channel.send(embed=embed,file=file)
            self.logger.info(f"每日訊息已發送, 時間: {yesterday.strftime('%Y-%m-%d %H:%M:%S')} ~ {today.strftime('%Y-%m-%d %H:%M:%S')}")
            os.remove("output.png")
            # TODO: Remove after testing
            current_time = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
            self.logger.info(f"當前時間: {current_time}")

            self.daily_message_sent = True
        except Exception as e:
            self.logger.error(f"Error sending daily message: {e}")

    @daily_message.after_loop
    async def after_dayly_message(self):
        if self.daily_message.is_running():
            now = datetime.now(timezone)
            if now.hour != 0 and now.minute != 0 and now.second != 0:
                self.daily_message_sent = False
                self.logger.info("每日訊息已重置，將於明天午夜再次發送。")

    @discord.slash_command(name="query", description="查看指定時間範圍內有幾篇貼文")
    async def query(self, ctx: discord.ApplicationContext, start_date: discord.Option(description="開始日期，格式為 YYYY-MM-DD HH:MM:SS", required=True), end_date: discord.Option(default=None, description="結束日期，格式為 YYYY-MM-DD HH:MM:SS", required=False)): #type:ignore

        has_allowed_role = any(role.id == 1359938675768557719 for role in ctx.author.roles) # 小編身份組
        if ctx.author.id not in self.DEVELOPER and has_allowed_role is False:
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 嘗試使用查詢指令，但沒有權限。")
            return
        
        if start_date is None:
            await ctx.respond("❌ 請提供開始日期，格式為 YYYY-MM-DD HH:MM:SS。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 未提供開始日期。")
            return
        
        try:
            start_timestamp = self._formatted_time_to_unix_timestamp(start_date) if start_date else None

            if end_date is None:
                end_timestamp = int(datetime.now().timestamp())
            else:
                end_timestamp = self._formatted_time_to_unix_timestamp(end_date)

            posts_count, reels_count = self._get_posts_and_reels_count(start_timestamp, end_timestamp)

            start_date_str = datetime.fromtimestamp(start_timestamp).strftime("%Y-%m-%d %H:%M:%S") if start_timestamp else "<unknown>"
            end_date_str = datetime.fromtimestamp(end_timestamp).strftime("%Y-%m-%d %H:%M:%S") if end_timestamp else "<unknown>"

            content = f"在 {start_date_str} 到 {end_date_str} 之間：\n- 貼文: {posts_count} 篇\n- Reels: {reels_count} 篇"
            if posts_count == 100 or reels_count == 100:
                content += "\n\n注意：因為 Facebook API 的限制，查詢結果至多為 100。"
            await ctx.respond(content)
        except Exception as e:
            await ctx.respond(f"❌ 發生錯誤: {e}")
            self.logger.error(f"Error in query command: {e}")

def setup(bot: commands.Bot):
    bot.add_cog(NewFB(bot))