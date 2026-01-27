import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils
import random
import json
import base64
import aiohttp
import re
from discord import Webhook

class EnrichCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger('enrich')
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("EnrichCog is ready.")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        # 允許管理員用 .force_enrich 強制觸發
        is_force =  ".enrich" in message.content and utils.is_worker(message.author)
        
        # 如果不是強制觸發，則檢查條件
        if not is_force:
            # 不在指定頻道則跳過
            if message.channel.id != utils.OFFTOPIC_CHANNEL_ID:
                return
            # 25% 機率才觸發
            if random.random() > 0.25:
                return
        
        with open('JSON/enrich.json', 'r', encoding='utf-8') as f:
            enrich_data = json.load(f)
        
        if is_force and utils.is_developer(message.author) and len(message.content.split()) >= 2:
            user_id = message.content.split()[1].strip()
        else:
            user_id = str(message.author.id)
        
        if is_force:
            if len(message.content.split()) != 1:
                tmp = message.content.split()[1].strip()
                if tmp.isdigit() and utils.is_developer(message.author):
                    user_id = str(tmp)
            
        if user_id in enrich_data and message.content is not None:
            with open("JSON/webhook.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                
            gender = enrich_data[user_id].get("gender", "Male")
            if gender == "Female":
                choice = ["我完全同意老婆的看法","既然老婆都這麼說了，那一定沒錯！","(抱緊緊) 雖然我不懂，但我知道老婆說的一定是對的～","無條件附議老婆！", "(點頭如搗蒜) 老婆說什麼就是什麼","(蹭蹭) 我覺得老婆說得很對呀～","(親一口) 蓋章確認！同意老婆的看法！","老婆說得是！"]
            else:
                choice = ["我完全同意老公的看法","既然老公都這麼說了，那一定沒錯！","(抱緊緊) 雖然我不懂，但我知道老公說的一定是對的～","無條件附議老公！", "(點頭如搗蒜) 老公說什麼就是什麼","(蹭蹭) 我覺得老公說得很對呀～","(親一口) 蓋章確認！同意老公的看法！","老公說得是！"]
            
            if enrich_data[user_id].get("custom_messages"):
                for msg in enrich_data[user_id]["custom_messages"]:
                    choice.append(msg)
            
            # 只抓一次
            main_pattern = r"^\.enrich\s+(.*)"
            match = re.match(main_pattern, message.content)
            
            if match:
                if is_force:
                    files = [await attachment.to_file() for attachment in message.attachments]
                if message.attachments is None or len(message.attachments) == 0:
                    files = None
                
                content = match.group(1).strip()
                
                # 嘗試解析數字 (開發者模式)
                dev_match = re.match(r"^(\d+)\s+(.*)", content)
                
                if dev_match and utils.is_developer(message.author):
                    mes = dev_match.group(2).strip()
                    
                elif is_force and not utils.is_developer(message.author):
                    # 一般強行執行模式，直接用全部內容
                    mes = content
                elif files:
                    mes = None
                else:
                    mes = random.choice(choice)
                    
            else:
                # 連 .enrich 都沒對上
                mes = random.choice(choice)
                
                if is_force:
                    files = [await attachment.to_file() for attachment in message.attachments]
                    mes = None
                files = None
            
            if user_id in data:
                webhook_id = data[user_id]["id"]
                webhook_token = data[user_id]["token"]
                async with aiohttp.ClientSession() as session:
                        webhook = Webhook.partial(webhook_id, webhook_token, session=session)
                        try:
                            await webhook.fetch()
                            await webhook.send(content=mes, files=files)
                            await message.delete() if is_force else None
                            return
                        except:
                            pass
            
            webhook = await self.create_webhook(message.channel, user_id)
            await webhook.send(content=mes, files=files)
            await message.delete() if is_force else None

    async def create_webhook(self, channel: discord.TextChannel, userid):
        userid = str(userid)
        await self.clean_webhook(channel)
        with open('JSON/enrich.json', 'r', encoding='utf-8') as f:
            enrich_data = json.load(f)
        name = enrich_data.get(userid, {}).get("name", "Default Name")
        avatar_base64 = enrich_data.get(userid, {}).get("avatar", None)
        avatar_bytes = None
        if avatar_base64:
            try:
                avatar_bytes = base64.b64decode(avatar_base64)
            except Exception as e:
                self.logger.warning(f"無法解碼頭像，使用預設頭像：{e}")
                avatar_bytes = None
        webhook = await channel.create_webhook(name=name, avatar=avatar_bytes, reason="用於 Enrich 功能")
        webhook_id = webhook.id
        webhook_token = webhook.token
        with open("JSON/webhook.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        data[str(userid)] = {"id": webhook_id, "token": webhook_token}
        with open("JSON/webhook.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return webhook

    async def clean_webhook(self,channel):
        webhooks = await channel.webhooks()
        if len(webhooks) <= 9:
            return
        # 選擇要刪除的（例如：保留最新的 9 個）
        webhooks_to_delete = sorted(webhooks, key=lambda w: w.created_at)[:-9]  # 刪最舊的

        for webhook in webhooks_to_delete:
            try:
                await webhook.delete(reason="超過 Discord 限制，自動清除")
            except Exception as e:   
                continue

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if before.status == discord.Status.offline and after.status != discord.Status.offline:
            with open('JSON/enrich.json', 'r', encoding='utf-8') as f:
                enrich_data = json.load(f)

            user_id = str(after.id)
            
            if user_id in enrich_data:
                if not enrich_data[user_id].get("online_remind", False):
                    return
                if random.random() > 0.25:
                    return
                
                with open("JSON/webhook.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                gender = enrich_data[user_id].get("gender", "Male")
                if gender == "Female":
                    mes = f"哇！是<@{user_id}>老婆回來了"
                else:
                    mes = f"哇！是<@{user_id}>老公回來了"
                    
                if user_id in data:
                    webhook_id = data[user_id]["id"]
                    webhook_token = data[user_id]["token"]
                    async with aiohttp.ClientSession() as session:
                            webhook = Webhook.partial(webhook_id, webhook_token, session=session)
                            try:
                                await webhook.fetch()
                                await webhook.send(content=mes)
                                return
                            except:
                                pass
                channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
                webhook = await self.create_webhook(channel, user_id)
                await webhook.send(content=mes)

    async def invoke_jerry_webhook(self, content: str, user_id: str):
        with open('JSON/enrich.json', 'r', encoding='utf-8') as f:
            enrich_data = json.load(f)
        
        if user_id in enrich_data:
            with open("JSON/webhook.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            mes = content
            if user_id in data:
                webhook_id = data[user_id]["id"]
                webhook_token = data[user_id]["token"]
                async with aiohttp.ClientSession() as session:
                        webhook = Webhook.partial(webhook_id, webhook_token, session=session)
                        try:
                            await webhook.fetch()
                            await webhook.send(content=mes)
                            return
                        except:
                            pass
            channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
            webhook = await self.create_webhook(channel, user_id)
            await webhook.send(content=mes)

def setup(bot: commands.Bot):
    bot.add_cog(EnrichCog(bot))
