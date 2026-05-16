import requests
import discord
from discord.ext import commands, tasks
import json
from internal import utils
import asyncio
from datetime import datetime
from io import BytesIO
import os
import re
import subprocess

class Threads(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/threads.py: 日誌系統初始化完成")
        self.channel = self.bot.get_channel(utils.THREADS_CHANNEL_ID)

    async def __get_video_audio(self, post_id, link):
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-TW,zh;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'referrer': 'https://www.facebook.com/',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        }

        try:
            response = await asyncio.to_thread(requests.get, link, headers=headers, timeout=30)
            pattern = r"all_video_dash_prefetch_representations\":\[(.*?)\"nextgendash\":true}"
            matches = re.findall(pattern, response.text, re.DOTALL)
            if not matches:
                self.logger.error(f"__get_video_audio: 無法從 {link} 找到影片 manifest（pattern 不 match，可能 FB 改版）")
                return
            file = json.loads(matches[0] + '"nextgendash": true}')

            audio_url = None
            for item in file['representations']:
                if item.get("mime_type") == "audio/mp4":
                    audio_url = item.get("base_url").replace("\\/", "/")
            if not audio_url:
                self.logger.error(f"__get_video_audio: post_id={post_id} 找不到 audio/mp4 representation")
                return

            response = await asyncio.to_thread(requests.get, audio_url, headers=headers, timeout=30)
            route = utils.get_tmp_file(f"{post_id}.m4a")
            with open(route, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            self.logger.error(f"__get_video_audio 失敗 post_id={post_id}: {e}")

    async def __media_to_Discord(self, media_url, media_type, post_id=None):
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
            elif media_type == "VIDEO" and post_id is not None:
                route = utils.get_tmp_file(f"{post_id}.mp4")
                with open(route, 'wb') as f:
                    f.write(response.content)
                video_file = route
                audio_file = utils.get_tmp_file(f"{post_id}.m4a")
                output_file = utils.get_tmp_file(f"{post_id}_output.mp4")

                cmd = [
                    "ffmpeg",
                    "-y",  # 覆蓋舊檔案
                    "-i", video_file,
                    "-i", audio_file,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    output_file
                ]

                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                await asyncio.sleep(2)  # 確保文件寫入完成
                discord_file = discord.File(fp=utils.get_tmp_file(f'{post_id}_output.mp4'), filename='video.mp4')
                message = await channel.send(file=discord_file)
                return message.attachments[0].url
        else:
            self.logger.error(f"無法下載媒體，狀態碼：{response.status_code}")
            return None

    async def _handle_posting(self, message_id):
        threads_data = self.read_json_file('JSON/threads.json')
        post_info = threads_data[str(message_id)]
        post_type = post_info['type']
        post_id = post_info['post_id']
        post_link = post_info.get('link', '無連結')

        if post_type == "TEXT":
            post_data = await self.__text_post(post_id, message_id)
            await self.__after_post(post_data, post_id, message_id)
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
                        dc_url = await self.__media_to_Discord(url, "IMAGE")
                        if dc_url is not None:
                            media_urls.append(dc_url)
                    post_data = await self.__multi_post(post_id, message_id, media_urls)
                else:
                    media_url = data[0]["media"]["image"]["src"]
                    dc_url = await self.__media_to_Discord(media_url, "IMAGE")
                    post_data = await self.__single_post(post_id, message_id, dc_url)
            elif post_type == "VIDEO":
                media_url = data[0]["media"]["source"]
                await self.__get_video_audio(post_id, post_link)
                dc_url = await self.__media_to_Discord(media_url, "VIDEO", post_id)
                post_data = await self.__video_post(post_id, message_id, dc_url)

            await self.__after_post(post_data, post_id, message_id)

    async def __after_post(self, data, post_id, message_id):
        success = await self.__check_post_status(data, post_id, message_id)

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
        threads_data = self.read_json_file('JSON/threads.json')
        post_info = threads_data[str(message_id)]
        text = post_info['text']
        post_tag = post_info.get('tag', '無標籤')

        post_url = f"https://graph.threads.net/v1.0/{ID}/threads"
        payload = {
            "access_token": API,
            "media_type": "TEXT",
            "text": text
        }
        if post_tag != "無標籤":
            payload["topic_tag"] = f"{post_tag}"

        response = await asyncio.to_thread(requests.post, post_url, data=payload, timeout=30)
        data = response.json()
        if not data.get('id'):
            self.logger.error(f"__text_post 建立 container 失敗 post_id={post_id}, status={response.status_code}, response={response.text}")
            return data
        await asyncio.sleep(5)  # 避免過快請求導致失敗
        post_media_url = f"https://graph.threads.net/v1.0/{ID}/threads_publish"
        payload = {
            "access_token": API,
            "creation_id" : data.get('id'),
        }
        response = await asyncio.to_thread(requests.post, post_media_url, data=payload, timeout=30)
        data = response.json()
        if not data.get('id'):
            self.logger.error(f"__text_post publish 失敗 post_id={post_id}, status={response.status_code}, response={response.text}")
        return data

    async def __single_post(self, post_id, message_id, media_url):
        ID = utils.THREADS_ID
        API = utils.THREADS_TOKEN
        threads_data = self.read_json_file('JSON/threads.json')
        post_info = threads_data[str(message_id)]
        text = post_info['text']
        post_tag = post_info.get('tag', '無標籤')

        create_media_url = f"https://graph.threads.net/v1.0/{ID}/threads"
        payload = {
            "access_token": API,
            "media_type": "IMAGE",
            "image_url": media_url,
            "text": text
        }
        if post_tag != "無標籤":
            payload["topic_tag"] = f"{post_tag}"

        self.logger.info(f"__single_post 建立 container post_id={post_id}, image_url={media_url}")
        response = await asyncio.to_thread(requests.post, create_media_url, data=payload, timeout=30)
        data = response.json()
        Media_ID = data.get('id')
        if not Media_ID:
            self.logger.error(f"__single_post 建立 container 失敗 post_id={post_id}, status={response.status_code}, response={response.text}")
            return data
        await asyncio.sleep(5)  # 避免過快請求導致失敗
        post_media_url = f"https://graph.threads.net/v1.0/{ID}/threads_publish"
        payload = {
            "access_token": API,
            "creation_id" : Media_ID,
        }
        response = await asyncio.to_thread(requests.post, post_media_url, data=payload, timeout=30)
        data = response.json()
        if not data.get('id'):
            self.logger.error(f"__single_post publish 失敗 post_id={post_id}, status={response.status_code}, response={response.text}")
        return data

    async def __video_post(self, post_id, message_id, media_url):
        ID = utils.THREADS_ID
        API = utils.THREADS_TOKEN

        threads_data = self.read_json_file('JSON/threads.json')
        post_info = threads_data[str(message_id)]
        text = post_info['text']
        post_tag = post_info.get('tag', '無標籤')

        create_media_url = f"https://graph.threads.net/v1.0/{ID}/threads"
        payload = {
            "access_token": API,
            "media_type": "VIDEO",
            "video_url": media_url,
            "text": text
        }
        if post_tag != "無標籤":
            payload["topic_tag"] = f"{post_tag}"

        self.logger.info(f"__video_post 建立 container post_id={post_id}, video_url={media_url}")
        response = await asyncio.to_thread(requests.post, create_media_url, data=payload, timeout=30)
        data = response.json()
        Media_ID = data.get('id')
        if not Media_ID:
            self.logger.error(f"__video_post 建立 container 失敗 post_id={post_id}, status={response.status_code}, response={response.text}")
            return data
        await asyncio.sleep(60)  # 避免過快請求導致失敗
        try:
            os.remove(utils.get_tmp_file(f"{post_id}.mp4"))
            os.remove(utils.get_tmp_file(f"{post_id}.m4a"))
        except Exception as e:
            self.logger.warning(f"無法移除暫存檔 post_id={post_id}: {e}")
        post_media_url = f"https://graph.threads.net/v1.0/{ID}/threads_publish"
        payload = {
            "access_token": API,
            "creation_id" : Media_ID,
        }
        response = await asyncio.to_thread(requests.post, post_media_url, data=payload, timeout=30)
        data = response.json()
        if not data.get('id'):
            self.logger.error(f"__video_post publish 失敗 post_id={post_id}, status={response.status_code}, response={response.text}")
        return data

    async def __multi_post(self, post_id, message_id, media_urls):
        ID = utils.THREADS_ID
        API = utils.THREADS_TOKEN
        threads_data = self.read_json_file('JSON/threads.json')
        post_info = threads_data[str(message_id)]
        text = post_info['text']
        post_tag = post_info.get('tag', '無標籤')
        media_ids = []

        for idx, i in enumerate(media_urls):
            create_media_url = f"https://graph.threads.net/v1.0/{ID}/threads"

            payload = {
                "access_token": API,
                "media_type": "IMAGE",
                "image_url": i,
                "is_carousel_item": "true"
            }
            self.logger.info(f"__multi_post 建立 carousel item [{idx+1}/{len(media_urls)}] post_id={post_id}, image_url={i}")
            response = await asyncio.to_thread(requests.post, create_media_url, data=payload, timeout=30)
            data = response.json()
            if not data.get("id"):
                self.logger.error(f"__multi_post carousel item 建立失敗 post_id={post_id}, idx={idx}, status={response.status_code}, response={response.text}")
                return data
            media_ids.append(data.get("id"))
            await asyncio.sleep(2)  # 避免過快請求導致失敗
        carousel_url = f"https://graph.threads.net/v1.0/{ID}/threads"
        payload = {
            "access_token": API,
            "media_type": "CAROUSEL",
            "children": ",".join(media_ids),
            "text": text
        }
        if post_tag != "無標籤":
            payload["topic_tag"] = f"{post_tag}"

        response = await asyncio.to_thread(requests.post, carousel_url, data=payload, timeout=30)
        data = response.json()
        carousel_id = data.get("id")
        if not carousel_id:
            self.logger.error(f"__multi_post carousel 建立失敗 post_id={post_id}, status={response.status_code}, response={response.text}")
            return data
        await asyncio.sleep(5)  # 避免過快請求導致失敗
        post_carousel_url = f"https://graph.threads.net/v1.0/{ID}/threads_publish"
        payload = {
            "access_token": API,
            "creation_id" : carousel_id,
        }
        response = await asyncio.to_thread(requests.post, post_carousel_url, data=payload, timeout=30)
        data = response.json()
        if not data.get('id'):
            self.logger.error(f"__multi_post publish 失敗 post_id={post_id}, status={response.status_code}, response={response.text}")
        return data

    async def __check_post_status(self, data, post_id, message_id):
        data_id = data.get("id")
        self.channel = self.bot.get_channel(utils.THREADS_CHANNEL_ID)
        self.logger.info(f"Threads 發布結果 post_id={post_id}, response_id={data_id}")
        if data_id is None:
            err = data.get("error", {}) if isinstance(data, dict) else {}
            err_msg = err.get("message", "未知錯誤")
            err_type = err.get("type", "")
            err_code = err.get("code", "")
            err_subcode = err.get("error_subcode", "")
            err_fbtrace = err.get("fbtrace_id", "")
            self.logger.error(f"Threads 發布失敗完整回應 post_id={post_id}: {data}")
            desc = (
                f"貼文 ID: {post_id} 發布到 Threads 失敗。\n"
                f"**錯誤訊息**：{err_msg}\n"
                f"**類型 / 代碼**：{err_type} / {err_code}"
                + (f" ({err_subcode})" if err_subcode else "")
                + (f"\n**fbtrace_id**：`{err_fbtrace}`" if err_fbtrace else "")
            )
            embed = discord.Embed(title="貼文發布失敗", description=desc, color=0xff0000)
            await self.channel.send(embed=embed)
            return False
        else:
            threads_data = self.read_json_file('JSON/threads.json')

            embed = discord.Embed(title="貼文已發布", description=f"貼文 ID: {post_id} 已成功發布到 Threads。\n Threads ID: {data_id}", color=0x00ff00)
            embed.add_field(name="引流連結", value="發布中..." if threads_data[str(message_id)].get('reply_enabled', True) else "未啟用", inline=False)
            message = await self.channel.send(embed=embed)

            if threads_data[str(message_id)].get('reply_enabled', True):
                await self.__reply_post(data_id, message)
            return True

    async def __reply_post(self, threads_id, message):
        text = '''
Anon Taiwan x 女團哭迷因（GIRLS BAND CRY Memes）
各平台帳號與同好聊天社群
https://www.anontaiwan.meme/'''
        ID = utils.THREADS_ID
        API = utils.THREADS_TOKEN
        API_URL = f"https://graph.threads.net/v1.0/{ID}/threads"
        payload = {
            "media_type": "TEXT",
            "text": text,
            "reply_to_id": threads_id,
            "access_token": API
        }

        try:
            response = await asyncio.to_thread(requests.post, API_URL, data=payload, timeout=30)

            response_data = response.json()
            creation_id = response_data.get("id")

            if creation_id:
                await asyncio.sleep(5)

                publish_url = f"https://graph.threads.net/v1.0/{ID}/threads_publish"
                publish_payload = {
                    "creation_id": creation_id,
                    "access_token": API
                }

                publish_response = await asyncio.to_thread(requests.post, publish_url, data=publish_payload, timeout=30)
                publish_response.raise_for_status()

                embed = message.embeds[0]
                embed.set_field_at(0, name="引流連結", value="已成功發布", inline=False)
                await message.edit(embed=embed)
            else:
                self.logger.error(f"__reply_post 建立 reply container 失敗 threads_id={threads_id}, status={response.status_code}, response={response.text}")
                embed = message.embeds[0]
                embed.set_field_at(0, name="引流連結", value="發布回覆失敗", inline=False)
                embed.color = 0xff0000
                await message.edit(embed=embed)

        except requests.exceptions.HTTPError as errh:
            self.logger.error(f"__reply_post HTTP 錯誤 (請檢查 Access Token, Threads ID 和權限): {errh}")
            try:
                self.logger.error(f"HTTP 錯誤詳細資訊：{response.text}")
            except Exception:
                self.logger.error("無法獲取響應內容")
        except requests.exceptions.RequestException as err:
            self.logger.error(f"__reply_post 連接或超時錯誤：{err}")

    def read_json_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    def write_json_file(self, file_path, data):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    async def generate_post_embed(self, post_info):
        embed = discord.Embed(title="貼文預覽", description="以下是您即將發布的貼文內容預覽：", color=0x0000ff)
        embed.add_field(name="貼文 ID", value=post_info['post_id'], inline=False)
        embed.add_field(name="貼文內容", value=post_info['text'], inline=False)
        embed.add_field(name="標籤", value=post_info.get('tag', '無標籤'), inline=False)
        return embed

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
            threads_data = self.cog.read_json_file('JSON/threads.json')
            if str(message_id) not in threads_data:
                await interaction.response.send_message("找不到對應的貼文資料。", ephemeral=True)
                return

            post_info = threads_data[str(message_id)]
            view = Threads.TagButton(self.cog, str(message_id), post_info=post_info)
            embed = discord.Embed(title="請選擇標籤", description="請選擇以下標籤之一：", color=0x80009a)
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
            await interaction.message.delete()

    class CustomTagModal(discord.ui.Modal):
        def __init__(self, cog, message_id, post_info=None):
            super().__init__(title="自訂標籤")
            self.cog: "Threads" = cog
            self.message_id = message_id
            self.post_info = post_info
            self.add_item(discord.ui.InputText(label="請輸入自訂標籤", style=discord.InputTextStyle.short))

        async def callback(self, interaction: discord.Interaction):
            custom_tag = self.children[0].value
            view = Threads.ConfirmButton(self.cog, self.message_id, post_info=self.post_info)
            self.post_info['tag'] = custom_tag
            embed = await self.cog.generate_post_embed(self.post_info)
            await interaction.message.delete()
            await interaction.response.send_message(f"已設定自訂標籤：{custom_tag}", embed=embed, view=view)

    class TagButton(discord.ui.View):
        def __init__(self, cog, message_id=None, post_info=None):
            super().__init__(timeout=None)
            self.cog: "Threads" = cog
            self.message_id = message_id
            self.post_info = post_info

        @discord.ui.button(label="MyGO", style=discord.ButtonStyle.primary)
        async def MyGO_tag(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.post_info['tag'] = "MyGO"
            view = Threads.ConfirmButton(self.cog, self.message_id, post_info=self.post_info)
            embed = await self.cog.generate_post_embed(self.post_info)
            await interaction.message.delete()
            await interaction.response.send_message("已選擇標籤:MyGO", embed=embed, view=view)

        @discord.ui.button(label="Ave Mujica", style=discord.ButtonStyle.primary)
        async def Ave_Mujica_tag(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.post_info['tag'] = "Ave Mujica"
            view = Threads.ConfirmButton(self.cog, self.message_id, post_info=self.post_info)
            embed = await self.cog.generate_post_embed(self.post_info)
            await interaction.message.delete()
            await interaction.response.send_message("已選擇標籤:Ave Mujica", embed=embed, view=view)

        @discord.ui.button(label="GBC", style=discord.ButtonStyle.green)
        async def GBC_tag(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.post_info['tag'] = "Girls Band Cry"
            view = Threads.ConfirmButton(self.cog, self.message_id, post_info=self.post_info)
            embed = await self.cog.generate_post_embed(self.post_info)
            await interaction.message.delete()
            await interaction.response.send_message("已選擇標籤:Girls Band Cry", embed=embed, view=view)

        @discord.ui.button(label="自行輸入", style=discord.ButtonStyle.gray)
        async def custom_tag(self, button: discord.ui.Button, interaction: discord.Interaction):
            modal = Threads.CustomTagModal(self.cog, self.message_id, post_info=self.post_info)
            await interaction.message.delete()
            await interaction.response.send_modal(modal)

        @discord.ui.button(label="無標籤", style=discord.ButtonStyle.danger)
        async def no_tag(self, button: discord.ui.Button, interaction: discord.Interaction):
            view = Threads.ConfirmButton(self.cog, self.message_id, post_info=self.post_info)
            embed = await self.cog.generate_post_embed(self.post_info)
            await interaction.message.delete()
            await interaction.response.send_message("已選擇無標籤", embed=embed, view=view)


    class ConfirmButton(discord.ui.View):
        def __init__(self, cog, mes_id, post_info=None):
            super().__init__(timeout=None)
            self.cog: "Threads" = cog
            self.mes_id = mes_id
            self.post_info = post_info

        @discord.ui.button(label="確認貼文", style=discord.ButtonStyle.success)
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            await interaction.response.send_message("貼文已確認，正在發布...", ephemeral=True)
            await interaction.message.delete()

            data = self.cog.read_json_file('JSON/threads.json')
            data[str(self.mes_id)] = self.post_info
            self.cog.write_json_file('JSON/threads.json', data)

            await self.cog._handle_posting(int(self.mes_id))

        @discord.ui.button(label="修改內容", style=discord.ButtonStyle.danger)
        async def edit_text(self, button: discord.ui.Button, interaction: discord.Interaction):
            modal = Threads.EditPost(self.cog, self.post_info, self.mes_id)
            await interaction.message.delete()
            await interaction.response.send_modal(modal)

        @discord.ui.button(label="關閉引流留言", style=discord.ButtonStyle.gray)
        async def close_reply(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.post_info['reply_enabled'] = False
            await interaction.response.send_message("引流留言已關閉。", ephemeral=True)

    class EditPost(discord.ui.Modal):
        def __init__(self, cog, post_info, mes_id):
            super().__init__(title="編輯貼文內容")
            self.cog: "Threads" = cog
            self.post_info = post_info
            self.mes_id = mes_id
            self.add_item(discord.ui.InputText(label="標籤", style=discord.InputTextStyle.short, value=post_info.get('tag', '無標籤')))
            self.add_item(discord.ui.InputText(label="新的貼文文字", style=discord.InputTextStyle.long, value=post_info['text']))

        async def callback(self, interaction: discord.Interaction):
            self.post_info['tag'] = self.children[0].value
            self.post_info['text'] = self.children[1].value
            threads_data = self.cog.read_json_file('JSON/threads.json')
            threads_data[str(self.mes_id)] = self.post_info
            self.cog.write_json_file('JSON/threads.json', threads_data)
            await interaction.response.send_message("已更新貼文內容並發布", ephemeral=True)
            await self.cog._handle_posting(int(self.mes_id))

    async def post_new_thread(self, post_info):
        channel = self.bot.get_channel(utils.THREADS_CHANNEL_ID)
        if channel is None:
            self.logger.error("無法找到 Threads 頻道")
            return

    async def get_post_details(self, post_id) -> dict:
        access_token = utils.FACEBOOK_TOKEN if utils.FB_PAGE_ID in post_id else utils.GBC_TOKEN
        url = f"https://graph.facebook.com/{post_id}/attachments?access_token={access_token}"
        try:
            response = await asyncio.to_thread(requests.get, url, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"無法取得貼文 {post_id} 的詳細資訊，狀態碼：{response.status_code}, response={response.text}")
                return {}
        except Exception as e:
            self.logger.error(f"get_post_details 例外 post_id={post_id}: {e}")
            return {}

    async def new_post_detected(self, post, page_id):
        channel = self.bot.get_channel(utils.THREADS_CHANNEL_ID)
        if channel is None:
            self.logger.error("無法找到 Facebook Thread 頻道")
            return
        # 雙保險：避免上游重複觸發導致建出多份待處理草稿
        try:
            with open('JSON/threads.json', 'r', encoding='utf-8') as f:
                existing = json.load(f)
            if any(entry.get('post_id') == post['id'] for entry in existing.values()):
                self.logger.info(f"貼文 {post['id']} 已存在 threads.json 草稿池，跳過重複建立")
                return
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        data = await self.get_post_details(post['id'])
        text = post.get('message', '無內容')

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
            post_type = "IMAGE" if data['data'][0]['type'] == 'album' or data['data'][0]['type'] == 'photo' else "VIDEO"
        threads_data[str(message.id)] = {
            "post_id": post['id'],
            "text": text,
            "type": post_type,
            "link": post.get('permalink_url', '無連結')
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
        response = await asyncio.to_thread(requests.get, url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            utils.update_token(threads = access_token)
            self.logger.info(f"成功更新 Threads 存取權杖：{data}")
        else:
            self.logger.error(f"更新 Threads 存取權杖失敗，狀態碼：{response.status_code}, response={response.text}")
            channel = self.bot.get_channel(utils.THREADS_CHANNEL_ID)
            await channel.send(f"<@&{utils.DEVELOPER_ROLE_ID}>更新 Threads 存取權杖失敗，請檢查日誌以獲取更多資訊")

def setup(bot: commands.Bot):
    bot.add_cog(Threads(bot))
