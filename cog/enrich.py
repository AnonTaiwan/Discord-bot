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

        if random.random() > 1 or message.channel.id != utils.OFFTOPIC_CHANNEL_ID:
            return
        
        with open('JSON/enrich.json', 'r', encoding='utf-8') as f:
            enrich_data = json.load(f)
            
        user_id = str(message.author.id)
        
        if user_id in enrich_data:
            
            with open("JSON/webhook.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            mes = f"我覺得老公說的對"
            if user_id in data:
                print("found webhook")
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
            
            webhook = await self.create_webhook(message.channel, user_id)
            await webhook.send(content=mes)
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

def setup(bot: commands.Bot):
    bot.add_cog(EnrichCog(bot))
