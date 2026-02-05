import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils
import random
import json
import base64
import aiohttp
import re
import io
from discord import Webhook

class EnrichCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger('enrich')
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("EnrichCog is ready.")
    
    def __get_webhook_users(self, enrich_data, user_id):
        webhook_users = enrich_data[user_id].get("datas", None)
        return webhook_users
    
    def __choose_webhook_user(self, webhook_users):
        return random.choice(webhook_users)
    
    def __get_messages(self, webhook_user, gender):
        if gender == "Female":
                choice = ["我完全同意老婆的看法","既然老婆都這麼說了，那一定沒錯！","(抱緊緊) 雖然我不懂，但我知道老婆說的一定是對的～","無條件附議老婆！", "(點頭如搗蒜) 老婆說什麼就是什麼","(蹭蹭) 我覺得老婆說得很對呀～","(親一口) 蓋章確認！同意老婆的看法！","老婆說得是！"]
        else:
            choice = ["我完全同意老公的看法","既然老公都這麼說了，那一定沒錯！","(抱緊緊) 雖然我不懂，但我知道老公說的一定是對的～","無條件附議老公！", "(點頭如搗蒜) 老公說什麼就是什麼","(蹭蹭) 我覺得老公說得很對呀～","(親一口) 蓋章確認！同意老公的看法！","老公說得是！"]
        
        if "custom_messages" in webhook_user:
            for msg in webhook_user["custom_messages"]:
                choice.append(msg)
        return choice
    
    def __online_remind_message(self, gender, user: discord.Member):
        if gender == "Female":
            choice = [f"哇！是{user.mention}老婆上線啦！",f"{user.mention}老婆回來了！歡迎回家～",f"{user.mention}老婆上線啦！有什麼需要幫忙的嗎？"]
        else:
            choice = [f"哇！是{user.mention}老公上線啦！",f"{user.mention}老公回來了！歡迎回家～",f"{user.mention}老公上線啦！有什麼需要幫忙的嗎？"]
        return choice
    
    def __get_webhook_data(self, user_id, name, channel_id, webhook_datas):
        if webhook_datas.get(user_id, {}).get(channel_id, {}).get(name):
            webhook_data = webhook_datas[user_id][channel_id][name]
            return webhook_data["id"], webhook_data["token"]
        else:
            return None, None
        
    def __load_json(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            self.logger.warning(f"找不到檔案：{file_path}，已回傳空資料。")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析失敗：{file_path}，錯誤：{e}")
            return {}
    
    def __write_json(self, file_path, data):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    async def __send_webhook(self, channel: discord.TextChannel, user_id: str, webhook_user: dict, mes: str, files = None):
        data = self.__load_json("JSON/webhook.json")
            
        webhook_id, webhook_token = self.__get_webhook_data(user_id, webhook_user["name"], str(channel.id), data)
        if webhook_id and webhook_token:
            async with aiohttp.ClientSession() as session:
                    webhook = Webhook.partial(webhook_id, webhook_token, session=session)
                    try:
                        await webhook.fetch()
                        await webhook.send(content=mes, files=files)
                        return
                    except:
                        pass
        
        webhook = await self.create_webhook(channel, user_id, webhook_user, data)
        await webhook.send(content=mes, files=files)
        return
    
    async def create_webhook(self, channel: discord.TextChannel, userid, webhook_user, webhook_datas: dict):
        userid = str(userid)
        await self.clean_webhook(channel)

        name = webhook_user.get("name", None)
        avatar_base64 = webhook_user.get("avatar", None)
        
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
        webhook_datas.setdefault(userid, {}).setdefault(str(channel.id), {})[name] = {"id": webhook_id, "token": webhook_token}
        
        self.__write_json("JSON/webhook.json", webhook_datas)
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
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id not in utils.ENRICH_CHANNEL_IDS or message.channel.type != discord.ChannelType.text:
            return
        
        if random.random() > 0.25:
            return
        
        enrich_data = self.__load_json("JSON/enrich.json")
        
        user_id = str(message.author.id)
        
        if user_id in enrich_data and message.content is not None:
            
            if not enrich_data[user_id].get("status", True):
                return
            
            webhook_users = self.__get_webhook_users(enrich_data, user_id)
            if not webhook_users or len(webhook_users) == 0:
                return
            
            webhook_user = self.__choose_webhook_user(webhook_users) # 選擇一個 webhook 用戶，返回 name, avatar_base64, custom_messages 的 dict
                
            gender = enrich_data[user_id].get("gender", "Male")
            choice = self.__get_messages(webhook_user, gender)
            mes = random.choice(choice)
            
            await self.__send_webhook(message.channel, user_id, webhook_user, mes)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if before.status == discord.Status.offline and after.status != discord.Status.offline:
            enrich_data = self.__load_json("JSON/enrich.json")

            user_id = str(after.id)
            
            if user_id in enrich_data:
                if not enrich_data[user_id].get("online_remind", False):
                    return
                if random.random() > 0.25:
                    return
                    
                webhook_users = self.__get_webhook_users(enrich_data, user_id)
                if not webhook_users or len(webhook_users) == 0:
                    return None
                
                webhook_user = self.__choose_webhook_user(webhook_users) # 選擇一個 webhook 用戶，返回 name, avatar_base64, custom_messages 的 dict
                    
                gender = enrich_data[user_id].get("gender", "Male")
                choice = self.__online_remind_message(gender, after)
                mes = random.choice(choice)
                
                channel = after.guild.get_channel(utils.OFFTOPIC_CHANNEL_ID)
                
                await self.__send_webhook(channel, user_id, webhook_user, mes)
                
    
    command_group = discord.SlashCommandGroup("enrich", "Enrich 相關指令")

    @command_group.command(name="send", description="透過 Enrich Webhook 發送訊息")
    async def enrich_send(self, ctx: discord.ApplicationContext, 
                        content: discord.Option(str, "輸入要發送的訊息", default=None), # type: ignore
                        channel: discord.Option(discord.TextChannel, "選擇要發送的頻道", default=None), # type: ignore
                        file1 : discord.Option(discord.Attachment, "選擇要發送的檔案", default=None), # type: ignore
                        file2 : discord.Option(discord.Attachment, "選擇要發送的檔案", default=None), # type: ignore
                        file3 : discord.Option(discord.Attachment, "選擇要發送的檔案", default=None), # type: ignore
                        user : discord.Option(discord.Member, "選擇用戶", default=None), # type: ignore
                        webhook_user : discord.Option(str, "選擇 webhook 用戶", default=None)): # type: ignore
        if not utils.is_worker(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name}嘗試使用 Enrich 發送訊息指令，但沒有權限。")
            return
        
        if not utils.is_developer(ctx.author) and user is not None:
            await ctx.respond("❌ 你沒有權限為其他用戶發送 Enrich 訊息。", ephemeral=True)
            return
        
        await ctx.defer(ephemeral=True)
        
        """透過 Enrich Webhook 發送訊息"""
        if channel is None:
            channel = ctx.channel  # 如果沒有指定頻道，則使用當前頻道
        
        if channel.type != discord.ChannelType.text:
            await ctx.respond("❌ 只能選擇文字頻道。", ephemeral=True)
            return
        
        enrich_data = self.__load_json("JSON/enrich.json")
        
        if user is not None:
            user_id = str(user.id)
        else:
            user_id = str(ctx.author.id)
        
        if user_id in enrich_data:
            if not enrich_data[user_id].get("status", True) and not utils.is_developer(ctx.author):
                await ctx.respond("❌ 你的 Enrich 功能目前已關閉，無法發送訊息。", ephemeral=True)
                return
            
            webhook_users = self.__get_webhook_users(enrich_data, user_id)
            if not webhook_users or len(webhook_users) == 0:
                await ctx.respond("❌ 你沒有設定任何 Enrich Webhook 用戶資料，無法發送訊息。", ephemeral=True)
                return
            
            if webhook_user is not None:
                selected_user = None
                for u in webhook_users:
                    if webhook_user in u["name"]:
                        selected_user = u
                        break
                
                if selected_user is None:
                    await ctx.respond("❌ 找不到指定的 Enrich Webhook 用戶，請確認名稱是否正確。", ephemeral=True)
                    return
                webhook_user = selected_user
            else:
                webhook_user = self.__choose_webhook_user(webhook_users) # 選擇一個 webhook 用戶，返回 name, avatar_base64, custom_messages 的 dict
            
            # 初始化變數
            files = None
            mes = ""
            
            # 處理附件：將 Attachment 轉換為 File
            attachments = [f for f in [file1, file2, file3] if f is not None]
            if attachments:
                files = []
                for attachment in attachments:
                    file_data = await attachment.read()
                    files.append(discord.File(fp=io.BytesIO(file_data), filename=attachment.filename))
            
            if content is None and file1 is None and file2 is None and file3 is None:
                choice = self.__get_messages(webhook_user, enrich_data[user_id].get("gender", "Male"))
                mes = random.choice(choice)
                
            if content is not None:
                mes = content
            
            await self.__send_webhook(channel, user_id, webhook_user, mes, files)
            
            await ctx.respond(f"✅ 已透過 Enrich Webhook 在 {channel.mention} 發送訊息。", ephemeral=True)
            
    @command_group.command(name="list", description="列出你的 Enrich Webhook 用戶")
    async def enrich_list(self, ctx: discord.ApplicationContext):
        if not utils.is_worker(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name}嘗試使用 Enrich 列出 Webhook 用戶指令，但沒有權限。")
            return
        
        await ctx.defer(ephemeral=True)
        
        """列出你的 Enrich Webhook 用戶"""
        enrich_data = self.__load_json("JSON/enrich.json")
        
        user_id = str(ctx.author.id)
        
        if user_id in enrich_data:
            webhook_users = self.__get_webhook_users(enrich_data, user_id)
            if not webhook_users or len(webhook_users) == 0:
                await ctx.respond("❌ 你沒有設定任何 Enrich Webhook 用戶資料。", ephemeral=True)
                return
            
            embed = discord.Embed(title="你的 Enrich Webhook 用戶列表", color=discord.Color.blue())
            for wu in webhook_users:
                embed.add_field(name=wu["name"], value=f"自訂訊息數量：{len(wu.get('custom_messages', []))}", inline=False)
            
            await ctx.respond(embed=embed, ephemeral=True)
        else:
            await ctx.respond("❌ 你沒有設定任何 Enrich Webhook 用戶資料。", ephemeral=True)
            
    @command_group.command(name="change_status", description="顯示 Enrich 指令說明")
    async def enrich_change_status(self, ctx: discord.ApplicationContext, member: discord.Member):
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name}嘗試使用 Enrich Change Status 指令，但沒有權限。")
            return
        
        await ctx.defer(ephemeral=True)
        """顯示 Enrich 指令說明"""
        enrich_data = self.__load_json("JSON/enrich.json")
        user_id = str(member.id)
        if user_id in enrich_data:
            
            if enrich_data[user_id].get("status", True):
                enrich_data[user_id]["status"] = False
                self.__write_json("JSON/enrich.json", enrich_data)
                await ctx.respond(f"✅ 已關閉 <@{member.id}> 的 Enrich 功能。", ephemeral=True)
                return
            else:
                enrich_data[user_id]["status"] = True
                self.__write_json("JSON/enrich.json", enrich_data)
                await ctx.respond(f"✅ 已開啟 <@{member.id}> 的 Enrich 功能。", ephemeral=True)
        else:
            await ctx.respond(f"❌ <@{member.id}> 的 Enrich 功能尚未啟用。", ephemeral=True)
            
            
    # async def invoke_jerry_webhook(self, content: str, user_id: str):
    #     with open('JSON/enrich.json', 'r', encoding='utf-8') as f:
    #         enrich_data = json.load(f)
        
    #     if user_id in enrich_data:
    #         with open("JSON/webhook.json", "r", encoding="utf-8") as f:
    #             data = json.load(f)
    #         mes = content
    #         if user_id in data:
    #             webhook_id = data[user_id]["id"]
    #             webhook_token = data[user_id]["token"]
    #             async with aiohttp.ClientSession() as session:
    #                     webhook = Webhook.partial(webhook_id, webhook_token, session=session)
    #                     try:
    #                         await webhook.fetch()
    #                         await webhook.send(content=mes)
    #                         return
    #                     except:
    #                         pass
    #         channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
    #         webhook = await self.create_webhook(channel, user_id)
    #         await webhook.send(content=mes)

def setup(bot: commands.Bot):
    bot.add_cog(EnrichCog(bot))
