import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import utils
import random
import json
import base64
import aiohttp
import re
from discord import Webhook

class DcPostCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger('dc_post')
        path = utils.JSON_DIR/'dc_post.json'
        utils.check_exist_or_create_json(self.logger, path, default_content={})
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("DcPostCog is ready.")
        
        if not self.scheduled_post.is_running():
            self.scheduled_post.start()
        
    @tasks.loop(minutes=1)
    async def scheduled_post(self):
        datas = utils.read_json(self.logger, utils.JSON_DIR/'dc_post.json')
        now = datetime.now()
        for message_id, data in list(datas.items()):
            scheduled_time_str = data.get("scheduled_time")
            if not scheduled_time_str:
                continue
            try:
                scheduled_time = datetime.strptime(scheduled_time_str, "%Y-%m-%d %H:%M")
            except ValueError:
                self.logger.error(f"無效的時間格式：{scheduled_time_str}，跳過此訊息。")
                continue
            
            if now >= scheduled_time:
                target_channel_id = data.get("target_channel_id")
                message_id_int = data.get("message_id")
                target_channel = await self.bot.get_channel(target_channel_id)
                
                if target_channel is None:
                    self.logger.error(f"無法取得目標頻道 {target_channel_id}，跳過此訊息。")
                    continue
                
                message_channel = await self.__get_message_channel(utils.ADMIN_CHANNEL_ID)
                target_message = await self.__get_message_by_id(message_channel, message_id_int)
                content = target_message.content
                files = [await attachment.to_file() for attachment in target_message.attachments]
                
                await target_channel.send(content=content, files=files)
                self.logger.info(f"已成功轉發訊息 {message_id_int} 到頻道 {target_channel_id}。")

                datas.pop(message_id, None)
                utils.write_json(self.logger, utils.JSON_DIR/'dc_post.json', datas)
        
    async def __get_message_channel(self, channel_id: int):
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                self.logger.error(f"無法取得頻道 {channel_id}:{e}")
                return None
        return channel
    
    async def __get_message_by_id(self, channel: discord.TextChannel, message_id: int):
        try:
            message = await channel.fetch_message(message_id)
            return message
        except Exception as e:
            self.logger.error(f"無法取得訊息 {message_id}:{e}")
            return None
        
    class SelectView(discord.ui.Modal):
        def __init__(self, bot, message_id):
            super().__init__(title="選擇轉發方式")
            self.bot = bot
            self.message_id = message_id
            self.add_item(discord.ui.InputText(label="轉發時間", placeholder="輸入格式：YYYY-MM-DD HH:MM 範例：2024-06-01 15:30", required=True))

        async def callback(self, interaction: discord.Interaction):
            time_str = self.children[0].value
            try:
                datas = utils.read_json(DcPostCog.logger, utils.JSON_DIR/'dc_post.json')
                data = datas.get(str(self.message_id))
                if data is None:
                    await interaction.response.send_message("找不到對應的轉發資料。", ephemeral=True)
                    return
                data["scheduled_time"] = time_str
                utils.write_json(DcPostCog.logger, utils.JSON_DIR/'dc_post.json', datas)
                await interaction.response.send_message(f"已設定轉發時間為 {time_str}。", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"設定轉發時間時發生錯誤：{e}", ephemeral=True)
        
    class ConfirmView(discord.ui.View):
        def __init__(self, bot, message_id):
            super().__init__(timeout=None)
            self.bot = bot
            self.message_id = message_id

        @discord.ui.button(label="是否要直接發布", style=discord.ButtonStyle.green)
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            await interaction.response.send_message("已確認轉發。", ephemeral=True)
            datas = utils.read_json(self.bot.logger, utils.JSON_DIR/'dc_post.json')
            data = datas.get(str(self.message_id))
            
            if data is None:
                await interaction.followup.send("找不到對應的轉發資料。", ephemeral=True)
                return
            target_channel_id = data.get("target_channel_id")
            message_id = data.get("message_id")
            target_channel = await self.bot.get_channel(target_channel_id)
            
            if target_channel is None:
                await interaction.followup.send("無法取得目標頻道。", ephemeral=True)
                return
            target_message = await interaction.channel.fetch_message(message_id)
            
            content = target_message.content
            files = [await attachment.to_file() for attachment in target_message.attachments]
            await target_channel.send(content=content, files=files)
            await interaction.followup.send("訊息已成功轉發！", ephemeral=True)
            
            datas.pop(str(self.message_id), None)
            utils.write_json(self.bot.logger, utils.JSON_DIR/'dc_post.json', datas)
            
        @discord.ui.button(label="取消", style=discord.ButtonStyle.red)
        async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
            datas = utils.read_json(self.bot.logger, utils.JSON_DIR/'dc_post.json')
            datas.pop(str(self.message_id), None)
            utils.write_json(self.bot.logger, utils.JSON_DIR/'dc_post.json', datas)
            
            await interaction.response.send_message("已取消轉發。", ephemeral=True)
        
    class DcPostView(discord.ui.View):
        def __init__(self, bot):
            super().__init__(timeout=None)
            self.bot = bot
            self.value = None

        @discord.ui.button(label="直接轉發", style=discord.ButtonStyle.green,emoji="✅",custom_id="dc_post_direct")
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                await interaction.message.delete()
                await interaction.followup.send(content="請確認是否要直接發布", view=DcPostCog.ConfirmView(self.bot, interaction.message.id), ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"轉發訊息時發生錯誤：{e}", ephemeral=True)

        @discord.ui.button(label="排程轉發", style=discord.ButtonStyle.blurple,emoji="⏰",custom_id="dc_post_scheduled")
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            try:
                await interaction.message.delete()
                await interaction.followup.send(content="請選擇轉發方式", view=DcPostCog.SelectView(self.bot, interaction.message.id))
            except Exception as e:
                await interaction.followup.send(f"轉發訊息時發生錯誤：{e}", ephemeral=True)

        @discord.ui.button(label="取消", style=discord.ButtonStyle.red, emoji="❌",custom_id="dc_post_cancel")
        async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
            datas = utils.read_json(DcPostCog.logger, utils.JSON_DIR/'dc_post.json')
            datas.pop(str(interaction.message.id), None)
            utils.write_json(DcPostCog.logger, utils.JSON_DIR/'dc_post.json', datas)
            await interaction.message.delete()
            await interaction.response.send_message("已取消轉發。", ephemeral=True)

        
    @discord.slash_command(name="dc_post", description="將指定訊息轉發到指定頻道")
    async def dc_post(self, ctx: discord.ApplicationContext, channel: discord.channel.TextChannel, message_link: str):
        if not utils.is_operator(ctx.author):
            await ctx.respond("你沒有權限使用此指令。", ephemeral=True)
            return
        
        pattern = r"https://discord.com/channels/\d+/(\d+)/(\d+)"
        match = re.match(pattern, message_link)
        if not match:
            await ctx.respond("無效的訊息連結格式。請提供有效的 Discord 訊息連結。", ephemeral=True)
            return
        source_channel_id = int(match.group(1))
        message_id = int(match.group(2))
        
        source_channel = await self.__get_message_channel(source_channel_id)
        if source_channel is None:
            await ctx.respond("無法取得來源頻道。請確認連結是否正確。", ephemeral=True)
            return
        message = await self.__get_message_by_id(source_channel, message_id)
        if message is None:
            await ctx.respond("無法取得指定的訊息。請確認連結是否正確。", ephemeral=True)
            return
        
        await ctx.respond(f"請確認轉發訊息", ephemeral=True)
        
        try:
            embed = discord.Embed(title="確認轉發頻道和訊息", description=f"目標頻道：{channel.mention}", color=discord.Color.blue())
            
            view = self.DcPostView(self.bot)
            msg = await message.reply(embed=embed, view=view)
            
            data = utils.read_json(self.logger, utils.JSON_DIR/'dc_post.json')
            data[str(msg.id)] = {
                "target_channel_id": channel.id,
                "message_id": message.id}
            
        except Exception as e:
            await ctx.respond(f"發生錯誤：{e}", ephemeral=True)
            
def setup(bot):
    bot.add_cog(DcPostCog(bot))