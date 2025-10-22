import requests
import discord
from discord.ext import commands, tasks
import json
import utils
import asyncio
from datetime import datetime, timedelta
from io import BytesIO

class Threads(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/threads.py: 日誌系統初始化完成")
        self.channel = self.bot.get_channel(utils.THREADS_CHANNEL_ID)

    async def __media_to_Disccord(self, media_url, media_type):
        channel = self.bot.get_channel(utils.THREADS_MEDIA_CHANNEL_ID)
        # 將阻塞的 HTTP 下載放到執行緒，避免阻塞事件迴圈
        response = await asyncio.to_thread(requests.get, media_url, timeout=30)
        if response.status_code == 200:
            if media_type == "IMAGE":
                fb = response.content
                buffer = BytesIO(fb)
                buffer.seek(0)
                discord_file = discord.File(fp=buffer, filename='image.jpg')
                message = await channel.send(file=discord_file)
                return message.attachments[0].url
            elif media_type == "VIDEO":
                fb = response.content
                buffer = BytesIO(fb)
                buffer.seek(0)
                discord_file = discord.File(fp=buffer, filename='video.mp4')
                message = await channel.send(file=discord_file)
                return message.attachments[0].url
        else:
            self.logger.error(f"無法下載媒體，狀態碼：{response.status_code}")
            return None

    async def _handle_posting(self, message_id):
        with open('JSON/threads.json', 'r', encoding='utf-8') as f:
            threads_data = json.load(f)
        post_info = threads_data[str(message_id)]
        post_type = post_info['type']
        post_id = post_info['post_id']
        if post_type == "TEXT":
            success = await self.__text_post(post_id, message_id)
            if success:
                with open('JSON/threads.json', 'r', encoding='utf-8') as f:
                    threads_data = json.load(f)
                del threads_data[str(message_id)]
                with open('JSON/threads.json', 'w', encoding='utf-8') as f:
                    json.dump(threads_data, f, ensure_ascii=False, indent=4)
            return
        data = await self.get_post_details(post_id)
        data = data.get('data', [])
        if data:
            if post_type == "IMAGE":
                subattachments = data[0].get('subattachments')
                if subattachments:
                    media_urls = []
                    for item in subattachments['data']:
                        url = item["media"]["image"]["src"]
                        dc_url = await self.__media_to_Disccord(url, "IMAGE")
                        if dc_url is not None:
                            media_urls.append(dc_url)
                    success = await self.__multi_post(post_id, message_id, media_urls)
                else:
                    media_url = data[0]["media"]["image"]["src"]
                    dc_url = await self.__media_to_Disccord(media_url, "IMAGE")
                    success = await self.__single_post(post_id, message_id, dc_url)
            elif post_type == "VIDEO":
                media_url = data[0]["media"]["source"]
                dc_url = await self.__media_to_Disccord(media_url, "VIDEO")
                success = await self.__video_post(post_id, message_id, dc_url)
            if success:
                with open('JSON/threads.json', 'r', encoding='utf-8') as f:
                    threads_data = json.load(f)
                del threads_data[str(message_id)]
                with open('JSON/threads.json', 'w', encoding='utf-8') as f:
                    json.dump(threads_data, f, ensure_ascii=False, indent=4)
                channel = self.bot.get_channel(utils.THREADS_CHANNEL_ID)
                message = await channel.fetch_message(message_id)
                await message.delete()

    async def __text_post(self, post_id, message_id):
        ID = utils.THREADS_ID
        API = utils.THREADS_TOKEN
        with open('JSON/threads.json', 'r', encoding='utf-8') as f:
            threads_data = json.load(f)
        post_info = threads_data[str(message_id)]
        text = post_info['text']
        post_url = f"https://graph.threads.net/v1.0/{ID}/threads"
        payload = {
            "access_token": API,
            "media_type": "TEXT",
            "text": text
        }
        response = requests.post(post_url, data=payload)
        data = response.json()
        await asyncio.sleep(5)  # 避免過快請求導致失敗
        post_media_url = f"https://graph.threads.net/v1.0/{ID}/threads_publish"
        payload = {
            "access_token": API,
            "creation_id" : data.get('id'),
        }
        response = requests.post(post_media_url, data=payload)
        data = response.json()
        return await self.__check_post_status(data, post_id)

    async def __single_post(self, post_id, message_id, media_url):
        ID = utils.THREADS_ID
        API = utils.THREADS_TOKEN
        with open('JSON/threads.json', 'r', encoding='utf-8') as f:
            threads_data = json.load(f)
        post_info = threads_data[str(message_id)]
        text = post_info['text']
        create_media_url = f"https://graph.threads.net/v1.0/{ID}/threads"
        payload = {
            "access_token": API,
            "media_type": "IMAGE",
            "image_url": media_url,
            "text": text
        }
        response = requests.post(create_media_url, data=payload)
        data = response.json()
        Media_ID = data.get('id')
        await asyncio.sleep(5)  # 避免過快請求導致失敗
        post_media_url = f"https://graph.threads.net/v1.0/{ID}/threads_publish"
        payload = {
            "access_token": API,
            "creation_id" : Media_ID,
        }
        response = requests.post(post_media_url, data=payload)
        data = response.json()
        return await self.__check_post_status(data, post_id)

    async def __video_post(self, post_id, message_id, media_url):
        ID = utils.THREADS_ID
        API = utils.THREADS_TOKEN
        with open('JSON/threads.json', 'r', encoding='utf-8') as f:
            threads_data = json.load(f)
        post_info = threads_data[str(message_id)]
        text = post_info['text']
        create_media_url = f"https://graph.threads.net/v1.0/{ID}/threads"
        payload = {
            "access_token": API,
            "media_type": "VIDEO",
            "video_url": media_url,
            "text": text
        }
        response = requests.post(create_media_url, data=payload)
        data = response.json()
        Media_ID = data.get('id')
        await asyncio.sleep(5)  # 避免過快請求導致失敗
        post_media_url = f"https://graph.threads.net/v1.0/{ID}/threads_publish"
        payload = {
            "access_token": API,
            "creation_id" : Media_ID,
        }
        response = requests.post(post_media_url, data=payload)
        data = response.json()
        return await self.__check_post_status(data, post_id)
        
    async def __multi_post(self, post_id, message_id, media_urls):
        ID = utils.THREADS_ID
        API = utils.THREADS_TOKEN
        with open('JSON/threads.json', 'r', encoding='utf-8') as f:
            threads_data = json.load(f)
        post_info = threads_data[str(message_id)]
        text = post_info['text']
        media_ids = []

        for i in media_urls:
            create_media_url = f"https://graph.threads.net/v1.0/{ID}/threads"

            payload = {
                "access_token": API,
                "media_type": "IMAGE",
                "image_url": i,
                "is_carousel_item": "true"
            }
            response = requests.post(create_media_url, data=payload)
            data = response.json()
            print("Posted thread ID:", data.get("id"))
            media_ids.append(data.get("id"))
            await asyncio.sleep(2)  # 避免過快請求導致失敗
        carousel_url = f"https://graph.threads.net/v1.0/{ID}/threads"
        payload = {
            "access_token": API,
            "media_type": "CAROUSEL",
            "children": ",".join(media_ids),
            "text": text
        }
        response = requests.post(carousel_url, data=payload)
        data = response.json()
        carousel_id = data.get("id")
        await asyncio.sleep(5)  # 避免過快請求導致失敗
        post_carousel_url = f"https://graph.threads.net/v1.0/{ID}/threads_publish"
        payload = {
            "access_token": API,
            "creation_id" : carousel_id,
        }
        response = requests.post(post_carousel_url, data=payload)
        data = response.json()
        return await self.__check_post_status(data, post_id)
        
    async def __check_post_status(self, data, post_id):
        data_id = data.get("id")
        self.channel = self.bot.get_channel(utils.THREADS_CHANNEL_ID)
        print("Posted thread with media ID:", data_id)
        if data_id is None:
            embed = discord.Embed(title="貼文發布失敗", description=f"貼文 ID: {post_id} 發布到 Threads 失敗。", color=0xff0000)
            await self.channel.send(embed=embed)
            return False
        else:
            embed = discord.Embed(title="貼文已發布", description=f"貼文 ID: {post_id} 已成功發布到 Threads。\n Threads ID: {data_id}", color=0x00ff00)
            await self.channel.send(embed=embed)
            return True

    @commands.Cog.listener()
    async def on_ready(self):
        # 註冊持久化按鈕 View，並傳入本 Cog 實例供回呼使用
        self.bot.add_view(self.PostButton(self))
        if not self.update_threads.is_running():
            self.update_threads.start()

    class PostButton(discord.ui.View):
        def __init__(self, cog):
            super().__init__(timeout=None)
            self.cog: "Threads" = cog

        @discord.ui.button(label="發布貼文", style=discord.ButtonStyle.primary, custom_id="post_button")
        async def post(self, button: discord.ui.Button, interaction: discord.Interaction):
            message_id = interaction.message.id
            with open('JSON/threads.json', 'r', encoding='utf-8') as f:
                threads_data = json.load(f)
            if str(message_id) not in threads_data:
                await interaction.response.send_message("找不到對應的貼文資料。", ephemeral=True)
                return
            post_info = threads_data[str(message_id)]
            view = Threads.ConfirmButton(self.cog, str(message_id))
            embed = discord.Embed(title="確認發布貼文", description="請確認以下貼文內容是否正確，然後選擇操作。", color=0x0000ff)
            embed.add_field(name="貼文 ID", value=post_info['post_id'], inline=False)
            embed.add_field(name="貼文內容", value=post_info['text'], inline=False)
            await interaction.response.send_message(embed=embed, view=view)
        
        @discord.ui.button(label="不發布貼文", style=discord.ButtonStyle.danger, custom_id="delete_button")
        async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
            with open('JSON/threads.json', 'r', encoding='utf-8') as f:
                threads_data = json.load(f)
            message_id = interaction.message.id
            if str(message_id) in threads_data:
                del threads_data[str(message_id)]
                with open('JSON/threads.json', 'w', encoding='utf-8') as f:
                    json.dump(threads_data, f, ensure_ascii=False, indent=4)
            await interaction.response.send_message("已取消發布貼文。", ephemeral=True)
            await interaction.delete_original_message()
            
    class ConfirmButton(discord.ui.View):
        def __init__(self, cog, mes_id):
            super().__init__(timeout=None)
            self.cog: "Threads" = cog
            with open('JSON/threads.json', 'r', encoding='utf-8') as f:
                threads_data = json.load(f)
            post_info = threads_data[mes_id]
            self.mes_id = mes_id
            self.post_info = post_info

        @discord.ui.button(label="確認貼文", style=discord.ButtonStyle.success)
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            await interaction.response.send_message("貼文已確認，正在發布...", ephemeral=True)
            await interaction.delete_original_message()
            await self.cog._handle_posting(int(self.mes_id))
            
        @discord.ui.button(label="修改文字", style=discord.ButtonStyle.danger)
        async def edit_text(self, button: discord.ui.Button, interaction: discord.Interaction):
            modal = Threads.EditPost(self.cog, self.post_info, self.mes_id)
            await interaction.delete_original_message()
            await interaction.response.send_modal(modal)
            
    class EditPost(discord.ui.Modal):
        def __init__(self, cog, post_info, mes_id):
            super().__init__(title="編輯貼文文字")
            self.cog: "Threads" = cog
            self.post_info = post_info
            self.mes_id = mes_id
            self.add_item(discord.ui.InputText(label="新的貼文文字", style=discord.InputTextStyle.long, value=post_info['text']))
            
        async def callback(self, interaction: discord.Interaction):
            self.post_info['text'] = self.children[0].value
            with open('JSON/threads.json', 'r', encoding='utf-8') as f:
                threads_data = json.load(f)
            threads_data[str(self.mes_id)] = self.post_info
            with open('JSON/threads.json', 'w', encoding='utf-8') as f:
                json.dump(threads_data, f, ensure_ascii=False, indent=4)
            await interaction.response.send_message("已更新貼文文字並發布", ephemeral=True)
            await self.cog._handle_posting(int(self.mes_id))

    async def post_new_thread(self, post_info):
        channel = self.bot.get_channel(utils.THREADS_CHANNEL_ID)
        if channel is None:
            self.logger.error("無法找到 Threads 頻道")
            return

    async def get_post_details(self, post_id) -> dict:
        access_token = utils.FACEBOOK_TOKEN
        url = f"https://graph.facebook.com/{post_id}/attachments?access_token={access_token}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"無法取得貼文 {post_id} 的詳細資訊，狀態碼：{response.status_code}")
            return {}

    async def new_post_detected(self, post, page_id):
        channel = self.bot.get_channel(utils.THREADS_CHANNEL_ID)
        if channel is None:
            self.logger.error("無法找到 Facebook Thread 頻道")
            return
        data = await self.get_post_details(post['id'])
        text = post.get('message', '無內容')
        text += '''\n
--
Anon Taiwan x 女團哭迷因（GIRLS BAND CRY Memes）
各平台帳號與同好聊天社群
https://www.anontaiwan.meme/
'''
        embed = discord.Embed(title="新貼文偵測", description=f"在頁面 ID {page_id} 偵測到新貼文", url=post.get('permalink_url', '無連結'), color=0x00ff00)
        embed.add_field(name="貼文 ID", value=post['id'], inline=False)
        embed.add_field(name="貼文內容", value=text, inline=False)
        embed.add_field(name="貼文連結", value=post.get('permalink_url', '無連結'), inline=False)
        with open('JSON/threads.json', 'r', encoding='utf-8') as f:
            threads_data = json.load(f)
        view = self.PostButton(self)
        message = await channel.send(embed=embed, view=view)
        if data.get('data') is None:
            post_type = "TEXT"
        else:
            post_type = "IMAGE" if data['data'][0]['type'] == 'album' else "VIDEO"
        threads_data[str(message.id)] = {
            "post_id": post['id'],
            "text": text,
            "type": post_type
        }
        with open('JSON/threads.json', 'w', encoding='utf-8') as f:
            json.dump(threads_data, f, ensure_ascii=False, indent=4)

    @tasks.loop(hours=1)  # 每小時檢查一次
    async def update_threads(self):
        # 只在每月 1 號的 06:00 執行
        now = datetime.now(utils.TIME_ZONE)
        if now.day != 1 or now.hour != 6:
            return
            
        url = f"https://graph.threads.net/refresh_access_token?grant_type=th_refresh_token&access_token={utils.THREADS_TOKEN}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            with open(utils.BOT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config['THREADS_TOKEN'] = access_token
            with open(utils.BOT_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            utils.update_bot_config('THREADS_TOKEN', access_token)
            self.logger.info(f"成功更新 Threads 存取權杖：{data}")
        else:
            self.logger.error(f"更新 Threads 存取權杖失敗，狀態碼：{response.status_code}")
            channel = self.bot.get_channel(utils.THREADS_CHANNEL_ID)
            await channel.send(f"<@&1361994254536409088>更新 Threads 存取權杖失敗，請檢查日誌以獲取更多資訊")

def