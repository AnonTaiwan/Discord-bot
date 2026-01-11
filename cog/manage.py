import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils
import chat_exporter
import io

class ManageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/manage.py: 管理系統初始化完成")
        
    @commands.Cog.listener()
    async def on_ready(self):
        utils.get_logger(__name__).info("ManageCog 已準備就緒")
        
    async def record_channel_message(self, channel: discord.TextChannel):
        """在指定頻道記錄訊息"""
        transcript = await chat_exporter.export(channel, limit=None, tz_info="Asia/Taipei")
        channel_log_channel = self.bot.get_channel(utils.CHANNEL_LOG_CHANNEL_ID)
        
        if channel_log_channel is not None and transcript is not None:
            file = discord.File(io.BytesIO(transcript.encode()), filename=f"{channel.name}.html")
            await channel_log_channel.send(file=file)
        
    command_group = discord.SlashCommandGroup("delete", "刪除相關指令")
        
    @command_group.command(name="message", description="刪除訊息")
    async def check_mom(self, ctx: discord.ApplicationContext, message_id: str):
        """檢查使用者是否為 MOM 或管理員"""
        if not isinstance(ctx.author, discord.Member):
            await ctx.respond("此指令僅限伺服器成員使用。", ephemeral=True)
            return
        if not utils.is_mom(ctx.author) and not utils.is_operator(ctx.author):
            await ctx.respond("你沒有使用此指令的權限。", ephemeral=True)
            return
        await ctx.defer(ephemeral=True)
        
        message_ids = message_id.split()
        in_valid_ids = [i for i in message_ids if not i.isdigit()]
        valid_ids = [i for i in message_ids if i.isdigit()]
        
        for i in valid_ids:
            try:
                msg_id = int(i)
                msg = await ctx.channel.fetch_message(msg_id)
                await msg.delete()
            except Exception as e:
                valid_ids.remove(i)
                in_valid_ids.append(i)
                await ctx.respond(f"無法刪除訊息 ID: {i}，錯誤：{e}", ephemeral=True)
        
        if in_valid_ids:
            await ctx.respond(f"已刪除以下訊息：{'\n'.join(valid_ids)} 以下訊息 ID 無效或無法刪除：{'\n'.join(in_valid_ids)}", ephemeral=True)
        else:
            await ctx.respond(f"已刪除以下訊息：{'\n'.join(valid_ids)}", ephemeral=True)
        
    @command_group.command(name="channel", description="刪除指定頻道")
    async def delete_channel(self, ctx: discord.ApplicationContext, channel: discord.Option(discord.TextChannel, "選擇要刪除的頻道", default=None)): # type: ignore
        if not utils.is_operator(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name}嘗試使用刪除頻道指令，但沒有權限。")
            return
        else:
            """刪除指定頻道"""
            if channel is None:
                channel = ctx.channel  # 如果沒有指定頻道，則使用當前頻道
            await ctx.respond(f"正在記錄頻道 {channel.mention} 的訊息...", ephemeral=True)
            await self.record_channel_message(channel)
            await channel.delete(reason=f"由 {ctx.author} 使用指令刪除")
            self.logger.info(f"✅ {ctx.author.name} 使用指令刪除頻道 {channel.name}。")
        
def setup(bot):
    bot.add_cog(ManageCog(bot))