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
        
        if random.random() > 0.25 or message.channel.id != utils.OFFTOPIC_CHANNEL_ID: 
            return
        
        with open('JSON/enrich.json', 'r', encoding='utf-8') as f:
            enrich_data = json.load(f)
        if str(message.author.id) in enrich_data.keys():
            with open("JSON/webhook.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            mes = f"我覺得老公說的對"
            if str(message.author.id) in data.keys():
                webhook_id = data[str(message.author.id)]["id"]
                webhook_token = data[str(message.author.id)]["token"]
                async with aiohttp.ClientSession() as session:
                        webhook = Webhook.partial(webhook_id, webhook_token, session=session)
                        try:
                            await webhook.fetch()
                            await webhook.send(content=mes)
                            return
                        except:
                            pass
            webhook = await self.create_webhook(message.channel, message.author.id)
            await webhook.send(content=mes)
            return

    async def create_webhook(self, channel: discord.TextChannel, userid: int):
        await self.clean_webhook(channel)
        with open('JSON/enrich.json', 'r', encoding='utf-8') as f:
            enrich_data = json.load(f)
        name = enrich_data.get(str(userid), "name")
        avatar_base64 = enrich_data.get(str(userid), None)
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




def setup(bot: commands.Bot):
    bot.add_cog(EnrichCog(bot))
