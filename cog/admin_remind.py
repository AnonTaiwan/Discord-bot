import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils
import json
import asyncio

class AdminRemind(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/admin_remind.py: 日誌系統初始化完成")
        
    async def __clean_webhook(self,channel):
        webhooks = await channel.webhooks()
        if not webhooks:
            return
        if len(webhooks) <= 9:
            return

        webhooks_to_delete = sorted(webhooks, key=lambda w: w.created_at)[:-9]  # 刪最舊的

        for webhook in webhooks_to_delete:
            try:
                await webhook.delete(reason="超過 Discord 限制，自動清除")
            except Exception as e:   
                continue
    
    async def create_webhook(self,channel: discord.TextChannel, user: discord.Member):
        await self.__clean_webhook(channel)
        avatar = user.display_avatar
        name = user.name
        return await channel.create_webhook(name=name, avatar=avatar, reason="用於管理員提醒")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != utils.ADMIN_CHANNEL_ID:
            return
        
        try:
            with open('JSON/admin_remind.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"last_message": None, "user_id": []}
        
        if not data.get("user_id", []):
            return
            
        last_message = data.get("last_message")
        should_send = True
        
        if last_message:
            last_time = datetime.strptime(last_message, "%Y-%m-%d %H:%M:%S")
            elapsed = datetime.now() - last_time
            if elapsed < timedelta(minutes=5):
                should_send = False
        
        if should_send:
            webhook = await self.create_webhook(message.channel, message.author)
            content = message.content + "\n\n"
            for user_id in data.get("user_id", []):
                content += f"<@{user_id}> "
            try:
                message = await webhook.send(content)
                await webhook.delete(reason="提醒發送完畢，清理 webhook")
                await asyncio.sleep(1)  # 等待 1 秒
                await message.delete()
            except Exception as e:
                self.logger.error(f"發送 webhook 失敗：{e}")
            
            # 只在成功發送後才更新時間
            data["last_message"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                with open('JSON/admin_remind.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                self.logger.error(f"寫入 admin_remind.json 失敗：{e}")
    
    @discord.slash_command(description="啟用/停用管理員提醒")
    async def toggle_admin_remind(self, ctx: discord.ApplicationContext):
        if not utils.is_operator(ctx.author):
            await ctx.respond("你沒有權限使用此指令。", ephemeral=True)
            return
        with open('JSON/admin_remind.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        if ctx.author.id in data.get("user_id", []):
            data["user_id"].remove(ctx.author.id)
            await ctx.respond("你已停用管理員提醒。", ephemeral=True)
            self.logger.info(f"{ctx.author.name} 停用管理員提醒")
        else:
            data["user_id"].append(ctx.author.id)
            await ctx.respond("你已啟用管理員提醒。", ephemeral=True)
            self.logger.info(f"{ctx.author.name} 啟用管理員提醒")
            
    