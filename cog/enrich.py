import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils
import random
import json
import base64
import aiohttp
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
        is_force = message.content == ".enrich" and utils.is_operator(message.author)
        
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
            
        user_id = str(message.author.id)
        
        if user_id in enrich_data:
            
            with open("JSON/webhook.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            choice = ["我覺得老公說的對", "我非常支持老公的觀點", "老公說得真好", "我完全同意老公的看法"]
            if enrich_data[user_id].get("custom_messages"):
                for msg in enrich_data[user_id]["custom_messages"]:
                    choice.append(msg)
            mes = random.choice(choice)
            if user_id in data:
                webhook_id = data[user_id]["id"]
                webhook_token = data[user_id]["token"]
                async with aiohttp.ClientSession() as session:
                        webhook = Webhook.partial(webhook_id, webhook_token, session=session)
                        try:
                            await webhook.fetch()
                            await webhook.send(content=mes)
                            await message.delete() if is_force else None
                            return
                        except:
                            pass
            
            webhook = await self.create_webhook(message.channel, user_id)
            await webhook.send(content=mes)
            await message.delete() if is_force else None
            return

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
                with open("JSON/webhook.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
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
            if not enrich_data[user_id].get("online_remind", False):
                return
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
