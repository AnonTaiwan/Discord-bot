import discord
from discord.ext import commands, tasks
from curl_cffi import requests
import json
from datetime import datetime, timedelta, time
import os
from PIL import Image, ImageDraw, ImageFont
import utils
import asyncio
from model import facebook

daily_message_time = time(hour=0, minute=0, second=0, tzinfo=utils.TIME_ZONE)  # 每日訊息時間設定

class ConfirmButton(discord.ui.View):
    def __init__(self, post_id, link, type, original_msg):
        super().__init__(timeout=None)
        self.post_id = post_id
        self.link = link
        self.type = type
        self.original_msg = original_msg


    async def __send_comments(self):
        url = f"https://graph.facebook.com/v23.0/{self.post_id}/comments"
        payload = {
            "message": f"{self.type} : \n{self.link}",
            "access_token": utils.FACEBOOK_TOKEN
        }
        loop = asyncio.get_event_loop()
        def sync_post():
            return requests.post(url, data=payload)
        response = await loop.run_in_executor(None, sync_post)
        return response.status_code == 200

    @discord.ui.button(label="確認", style=discord.ButtonStyle.danger)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        if await self.__send_comments():
            await interaction.response.edit_message(content=f"已為 {self.type} 補上來源連結：{self.link}", embed=None, view=None)
            await self.original_msg.delete()
        else:
            await interaction.response.edit_message(content=f"無法為 {self.type} 補上來源連結，請稍後再試。", embed=None, view=None)

    @discord.ui.button(label="取消", style=discord.ButtonStyle.secondary)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.edit_message(content="已取消補上來源連結。", embed=None, view=None)

class CommentLink(discord.ui.Modal):
    def __init__(self, post_id, post_url, type, original_msg):
        super().__init__(title="補上來源")
        self.post_id = post_id
        self.post_url = post_url
        self.type = type
        self.original_msg = original_msg
        self.add_item(discord.ui.InputText(label="請輸入來源連結", placeholder="https://example.com", required=True, style=discord.InputTextStyle.short))

    def create_embed(self):
        embed = discord.Embed(title=f"補上來源 - {self.type}", url=self.post_url, color=discord.Color.blue())
        embed.add_field(name="來源連結", value=self.link or "無連結", inline=False)
        return embed

    async def callback(self, interaction: discord.Interaction):
        self.link = self.children[0].value
        embed = self.create_embed()
        view = ConfirmButton(self.post_id, self.link, self.type, self.original_msg)
        await interaction.response.edit_message(embed=embed, view=view)

class CommentType(discord.ui.View):
    def __init__(self, post_id, url, original_msg):
        super().__init__(timeout=None)
        self.post_id = post_id
        self.url = url
        self.original_msg = original_msg

    @discord.ui.select(placeholder="選擇留言類型", min_values=1, max_values=1,
        options = [
            discord.SelectOption(label="創作分享"),
            discord.SelectOption(label="圖文分享"),
            discord.SelectOption(label="平台分享"),
            discord.SelectOption(label="傳送門"),
            discord.SelectOption(label="影片"),
        ])
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        type = select.values[0]
        await interaction.response.send_modal(CommentLink(self.post_id, self.url, type, self.original_msg))

class CommentButton(discord.ui.View):
    def __init__(self, post_id, url):
        super().__init__(timeout=None)
        self.post_id = post_id
        self.url = url

    @discord.ui.button(label="補上來源", style=discord.ButtonStyle.primary)
    async def view_comments(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.original_msg = interaction.message
        await interaction.response.send_message(content="請選擇留言類型", view=CommentType(self.post_id, self.url, self.original_msg), ephemeral=True)

class NewFB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/facebook.py: 日誌系統初始化完成")

    fb_command_group = discord.SlashCommandGroup(name="fb", description="Facebook 相關指令")

    def __mark_posted(self, post_id: str | None):
        """將貼文 id 加入已推播紀錄並持久化。"""
        if not post_id or facebook.check_posted_id_exists(post_id):
            return
        facebook.add_posted_id(post_id)

    async def get_datas(self, page_id, limit=3):
        """Fetch Facebook posts with timeout and retry."""
        url = f'https://graph.facebook.com/v23.0/{page_id}/posts?fields=message,created_time,full_picture,permalink_url,shares&access_token={utils.FACEBOOK_TOKEN}&limit={limit}'
        max_retries = 2
        for attempt in range(1, max_retries + 1):
            try:
                response = await asyncio.to_thread(requests.get, url, timeout=30)
                datas = json.loads(response.text)
                return datas.get('data', [])
            except Exception as e:
                self.logger.warning(f"get_datas attempt {attempt}/{max_retries} failed: {e}")
                if attempt == max_retries:
                    raise
                await asyncio.sleep(2)
        return []

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
        url = data.get('full_picture', None)
        if url:
            url = url.replace('\\','')
            try:
                response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=30)
                with open(f'tmp/{data["id"]}.jpg','wb') as f:
                    f.write(response.content)
            except Exception as e:
                self.logger.error(f"Failed to download image for {data['id']}: {e}")

    async def __send_update_message(self, data_id, embed, file):
        msg = await self.channel.send(content=f'<@&{utils.ANON_TAIWAN_SUBSCRIBER_ROLE_ID}>', embed=embed, file=file if file else None)
        await msg.publish()
        self.logger.info(f"已發送新貼文通知：{data_id}")
        file_path = f"tmp/{data_id}.jpg"
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                self.logger.warning(f"無法刪除臨時檔案 {file_path}: {e}")

    async def __send_post_update_message(self, data, page_id):
        await self.get_photo(data)
        name = "Anon Taiwan" if page_id == utils.FB_PAGE_ID else "女團哭迷因"
        url = data.get('permalink_url', 'No URL provided').replace('\\', '')
        message = data.get('message', 'No message provided')
        message = bytes(message, 'utf-8').decode(encoding="utf-8", errors="ignore")
        if len(message) > 1024:
            message = message[:1021] + "..."
        if data.get('id') is not None and facebook.check_posted_id_exists(data.get('id')):
            self.logger.info(f"貼文 {data['id']} 已經發送過通知，跳過。")
            return

        embed = discord.Embed(title=f'{name} 更新了新貼文！', url=url, color=0x00ff00)
        embed.add_field(name='貼文連結', value=url, inline=False)
        embed.add_field(name='貼文內容', value=message or "（無內容）", inline=False)

        file_path = f"tmp/{data['id']}.jpg"
        if os.path.exists(file_path):
            file = discord.File(file_path, filename=f"{data['id']}.jpg")
            embed.set_image(url=f"attachment://{data['id']}.jpg")
        else:
            file = None
        await self.__send_update_message(data.get('id', None), embed, file)
        self.__mark_posted(data.get('id'))

    async def __send_reel_update_message(self, reel):
        reel_data_id = reel['id']
        permalink = reel['permalink_url'].replace('\\', '')
        url = f"https://www.facebook.com{permalink}"
        message = reel.get('description', 'No description provided')
        message = bytes(message,'utf-8').decode(encoding="utf-8", errors="ignore")
        picture_url = reel.get('picture', {})
        file_path = f"tmp/{reel_data_id}.jpg"
        try:
            response = await asyncio.to_thread(requests.get, picture_url, timeout=30)
            with open(file_path, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            self.logger.error(f"Failed to download reel picture {reel_data_id}: {e}")
            return
        embed = discord.Embed(title='Anon Taiwan 更新了新 Reel！', url=url, color=discord.Color.blue())
        file = discord.File(file_path, filename=f"{reel_data_id}.jpg")
        embed.set_image(url=f"attachment://{reel_data_id}.jpg")
        embed.add_field(name='Reel 連結', value=url, inline=False)
        embed.add_field(name='Reel 內容', value=message or "（無內容）", inline=False)
        await self.__send_update_message(reel_data_id, embed, file)
        self.__mark_posted(reel_data_id)

    async def __check_comments(self, post_id, message, post_url):
        message = bytes(message, 'utf-8').decode(encoding="utf-8", errors="ignore")
        POST_KEYWORDS = ["【pixiv 分享】", "【推特圖文】"]
        COMMENT_KEYWORDS = ["創作分享", "圖文分享", "平台分享", "傳送門", "影片"]
        if any(keyword in message for keyword in POST_KEYWORDS) and post_id and post_url:
            url = f"https://graph.facebook.com/v23.0/{post_id}?fields=message,created_time,permalink_url,full_picture,comments&access_token={utils.FACEBOOK_TOKEN}"
            try:
                response = await asyncio.to_thread(requests.get, url, timeout=30)
                response.encoding = "utf-8"
                data = response.json()
                comments_data = data.get("comments", {}).get("data", [])
                for i in comments_data:
                    if not any(word in i.get("message", "") and i.get("from", {}).get("id") == utils.FB_PAGE_ID for word in COMMENT_KEYWORDS):
                        await self.__send_comments_remind_message(post_id, post_url)
                        self.logger.info(f"貼文 {post_id} 不包含留言來源，發送提醒。")
                        break
            except Exception as e:
                self.logger.error(f"Failed to check comments for {post_id}: {e}")

    async def __send_comments_remind_message(self, post_id, post_url):
        test_channel = self.bot.get_channel(utils.TEST_CHANNEL_ID)
        embed = discord.Embed(title='Anon Taiwan 來源提醒', url=post_url, color=0xffa500)
        embed.add_field(name='提醒內容', value='請記得查看貼文下方的留言，可能有圖片來源忘記發佈！', inline=False)
        view = CommentButton(post_id, post_url)
        await test_channel.send(embed=embed, view=view)
        self.logger.info(f"已發送留言提醒通知：{post_id}")

    async def __if_post_updates(self, datas):
        # 使用持久化的 posted_ids 過濾，避免「刪除最新貼文後次新貼文被誤推」
        return [i for i in datas if i.get('id') and not facebook.check_posted_id_exists(i['id'])]

    async def __handle_new_post(self, datas, page_id):
        new_posts = await self.__if_post_updates(datas)
        if not new_posts:
            return
        # FB API 回傳預設新→舊，這裡反過來讓舊的先發，順序符合貼文時序
        new_posts.sort(key=lambda p: p.get('created_time', ''))
        for post in new_posts:
            await self.__send_post_update_message(post, page_id)
            if page_id == utils.FB_PAGE_ID:
                create_time_str = post.get('created_time', None)
                if create_time_str is None:
                    create_time = datetime.now(utils.TIME_ZONE)
                else:
                    create_time = datetime.strptime(create_time_str, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=utils.TIME_ZONE)

                post_json = json.dumps(post)
                facebook.add_comment_check_queue(post['id'], post_json, create_time)
                self.logger.info(f"已將貼文 {post['id']} 加入待檢查留言列表。")
            try:
                threads = self.bot.get_cog('Threads')
                if threads:
                    await threads.new_post_detected(post, page_id)
            except Exception as e:
                self.logger.error(f"Error notifying Threads cog: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        if not os.path.exists("tmp"):
            os.makedirs("tmp")
        # 首次部署（posted_ids 為空）時用當下最新貼文當基準，避免把當下看到的全部當新貼文推
        if not facebook.list_all_posted_ids():
            self.logger.info("posted_ids 為空，使用當下最新貼文初始化基準（不推播）")
            anon_datas = await self.get_datas(page_id=utils.FB_PAGE_ID)
            gbc_datas = await self.get_datas(page_id=utils.GBC_FB_PAGE_ID)
            for post in anon_datas + gbc_datas:
                if post.get('id'):
                    facebook.add_posted_id(post['id'])
        # self.reel = requests.get(f'https://graph.facebook.com/v23.0/{utils.FB_PAGE_ID}/video_reels?fields=description,created_time,permalink_url&access_token={utils.FACEBOOK_TOKEN}&limit=3').json()['data'][0]['id']

        if not self.check_comments_routine.is_running():
            self.check_comments_routine.start()

        if not self.check_post_updates.is_running():
            self.check_post_updates.start()

        # if not self.check_reel_updates.is_running():
        #     self.check_reel_updates.start()

        self.channel = self.bot.get_channel(utils.FB_NOTIFICATION_CHANNEL_ID)

        if not self.daily_message.is_running():
            self.daily_message.start()

    @tasks.loop(minutes=1)
    async def check_comments_routine(self):
        try:
            now = datetime.now(utils.TIME_ZONE)
            ten_minutes_ago = now - timedelta(minutes=10)
            queue_items = facebook.get_due_comment_checks(ten_minutes_ago)
            for item in queue_items:
                post_data = json.loads(item.post_data)
                await self.__check_comments(post_data['id'], post_data.get('message', ''), post_data.get('permalink_url', '').replace('\\',''))
                facebook.remove_comment_check_by_id(item.id)
        except Exception as e:
            self.logger.error(f"Error checking comments: {e}")

    @tasks.loop(minutes=1)
    async def check_post_updates(self):
        try:
            datas = await self.get_datas(page_id=utils.FB_PAGE_ID)
            await self.__handle_new_post(datas, utils.FB_PAGE_ID)
            gbc_datas = await self.get_datas(page_id=utils.GBC_FB_PAGE_ID)
            await self.__handle_new_post(gbc_datas, utils.GBC_FB_PAGE_ID)
        except Exception as e:
            await self.bot.get_channel(utils.TEST_CHANNEL_ID).send(f"<@&{utils.DEVELOPER_ROLE_ID}>\n facebook.py 報錯:\n`Error checking for updates: {e}`")
            self.logger.error(f"Error checking for updates: {e}")

    @tasks.loop(minutes=5)
    async def check_reel_updates(self):
        try:
            url = f'https://graph.facebook.com/v23.0/{utils.FB_PAGE_ID}/video_reels?fields=description,created_time,permalink_url,picture&access_token={utils.FACEBOOK_TOKEN}&limit=3'
            response = await asyncio.to_thread(requests.get, url, timeout=30)
            reels_data = response.json()
            if reels_data.get('data') and self.reel != reels_data['data'][0]['id']:
                self.reel = reels_data['data'][0]['id']
                await self.__send_reel_update_message(reels_data['data'][0])
        except Exception as e:
            self.logger.error(f"Error checking for reels: {e}")

    def __formatted_time_to_unix_timestamp(self, formatted_time):
        try:
            dt = datetime.strptime(formatted_time, "%Y-%m-%d %H:%M:%S",).replace(tzinfo=utils.TIME_ZONE)
            return int(dt.timestamp())
        except ValueError as e:
            self.logger.error(f"時間格式錯誤：{e}")
            return None

    async def __get_posts_and_reels_count(self, start_timestamp, end_timestamp):
        try:
            posts_url = f'https://graph.facebook.com/v23.0/{utils.FB_PAGE_ID}/posts?fields=&access_token={utils.FACEBOOK_TOKEN}&since={start_timestamp}&until={end_timestamp}&limit=100'
            response = await asyncio.to_thread(requests.get, posts_url, timeout=30)
            posts_data = json.loads(response.text)
            posts_count = len(posts_data.get('data', []))

            reels_url = f'https://graph.facebook.com/v23.0/{utils.FB_PAGE_ID}/video_reels?fields=&access_token={utils.FACEBOOK_TOKEN}&since={start_timestamp}&until={end_timestamp}&limit=100'
            response = await asyncio.to_thread(requests.get, reels_url, timeout=30)
            reels_data = json.loads(response.text)
            reels_count = len(reels_data.get('data', []))

            return posts_count, reels_count
        except Exception as e:
            self.logger.error(f"Error fetching posts and reels count: {e}")
            return 0, 0

    def __generate_picture_embed(self, posts_count, reels_count, background_picture_file):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        background_path = os.path.join(current_dir, background_picture_file)
        img = Image.open(background_path)
        draw = ImageDraw.Draw(img)
        font_path = os.path.join(current_dir, "../static/NotoSansTC-Bold.ttf")
        font = ImageFont.truetype(font_path, 150)
        coordinate = img.width // 2 - 100 , img.height // 2 -110
        draw.text(coordinate, f"{posts_count} 則貼文", font=font, fill=(0, 0, 0), anchor="mm")
        draw.text((coordinate[0], coordinate[1] + 400), f"{reels_count} 則短片", font=font, fill=(0, 0, 0), anchor="mm")
        output_path = os.path.join("output.png")
        img.save(output_path, format='PNG', optimize=False)

    def __generate_daily_post_picture(self, posts_count, reels_count):
        self.__generate_picture_embed(posts_count, reels_count, "../static/background.png")

    def __generate_query_picture(self, posts_count, reels_count):
        self.__generate_picture_embed(posts_count, reels_count, "../static/postquery.png")

    @tasks.loop(time=daily_message_time)
    async def daily_message(self):
        try:
            today = datetime.now(utils.TIME_ZONE).replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = today - timedelta(days=1)

            today_timestamp = int(today.timestamp())
            yesterday_timestamp = int(yesterday.timestamp())

            posts_count, reels_count = await self.__get_posts_and_reels_count(yesterday_timestamp, today_timestamp)

            embed = discord.Embed(title=f"{yesterday.strftime('%Y-%m-%d')} 統整", color=discord.Color.blue())
            self.__generate_daily_post_picture(posts_count, reels_count)
            file = discord.File("output.png", filename="output.png")
            embed.set_image(url="attachment://output.png")

            channel = self.bot.get_channel(utils.FB_PAGE_DAILY_MESSAGE_CHANNEL_ID)
            await channel.send(embed=embed, file=file)
            self.logger.info(f"每日訊息已發送，時間：{yesterday.strftime('%Y-%m-%d %H:%M:%S')} ~ {today.strftime('%Y-%m-%d %H:%M:%S')}")
            os.remove("output.png")
        except Exception as e:
            self.logger.error(f"Error sending daily message: {e}")

    @fb_command_group.command(name="query-today", description="查看今日有幾篇貼文")
    async def today_query(self, ctx: discord.ApplicationContext):
        try:
            now = datetime.now(utils.TIME_ZONE)
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

            now_timestamp = int(now.timestamp())
            midnight_timestamp = int(midnight.timestamp())

            posts_count, reels_count = await self.__get_posts_and_reels_count(midnight_timestamp, now_timestamp)

            embed = discord.Embed(title='今日統整', color=discord.Color.blue())
            self.__generate_daily_post_picture(posts_count, reels_count)
            file = discord.File("output.png", filename="output.png")
            embed.set_image(url="attachment://output.png")

            await ctx.respond(embed=embed, file=file)
            os.remove("output.png")
        except Exception as e:
            await ctx.respond("❌ 發生錯誤")
            self.logger.error(f"Error in query-today command: {e}")

    @fb_command_group.command(name="query", description="查看指定時間範圍內有幾篇貼文")
    async def query(self, ctx: discord.ApplicationContext, start_date: discord.Option(description="開始日期，格式為 YYYY-MM-DD HH:MM:SS", required=True), end_date: discord.Option(default=None, description="結束日期，格式為 YYYY-MM-DD HH:MM:SS", required=False)): #type:ignore
        if not utils.is_operator(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 嘗試使用查詢指令，但沒有權限。")
            return

        if start_date is None:
            await ctx.respond("❌ 請提供開始日期，格式為 YYYY-MM-DD HH:MM:SS。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 未提供開始日期。")
            return

        try:
            start_timestamp = self.__formatted_time_to_unix_timestamp(start_date) if start_date else None

            if end_date is None:
                end_timestamp = int(datetime.now().timestamp())
            else:
                end_timestamp = self.__formatted_time_to_unix_timestamp(end_date)

            posts_count, reels_count = await self.__get_posts_and_reels_count(start_timestamp, end_timestamp)

            start_date_str = datetime.fromtimestamp(start_timestamp).strftime("%Y-%m-%d %H:%M:%S") if start_timestamp else "<unknown>"
            end_date_str = datetime.fromtimestamp(end_timestamp).strftime("%Y-%m-%d %H:%M:%S") if end_timestamp else "<unknown>"
            embed = discord.Embed(title=f'在 {start_date_str} 到 {end_date_str} 之間：', color=discord.Color.blue())
            self.__generate_query_picture(posts_count, reels_count)
            file = discord.File("output.png", filename="output.png")
            embed.set_image(url="attachment://output.png")
            if posts_count == 100 or reels_count == 100:
                if embed.description is None:
                    embed.description = ""
                embed.description += "\n\n注意：因為 Facebook API 的限制，查詢結果至多為 100。"

            await ctx.respond(embed=embed, file=file)
            os.remove("output.png")
        except Exception as e:
            await ctx.respond("❌ 發生錯誤")
            self.logger.error(f"Error in query command: {e}")

def setup(bot: commands.Bot):
    bot.add_cog(NewFB(bot))
