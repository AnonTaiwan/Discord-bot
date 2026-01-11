import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils

class ManageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        utils.get_logger(__name__).info("ManageCog 已準備就緒")
        
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
        
def setup(bot):
    bot.add_cog(ManageCog(bot))