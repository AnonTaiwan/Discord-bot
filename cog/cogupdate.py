from discord.ext import commands
from discord import Option, File
import discord
import os
import asyncio

DEVELOPER = [330256191127289856, 705432231304495205]

class CogManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="上傳並更新指定的cog")
    async def upload_cog(
        self,
        ctx: discord.ApplicationContext,
        file: discord.Attachment = Option(description="請上傳 .py 的 cog 檔案")
    ):
        if ctx.author.id not in DEVELOPER:
            await ctx.respond("❌ 你沒有權限使用這個指令。", ephemeral=True)
            return

        if not file.filename.endswith(".py"):
            await ctx.respond("❌ 請上傳副檔名為 `.py` 的檔案。", ephemeral=True)
            return

        await ctx.respond("📥 收到檔案，正在儲存並重新載入...", ephemeral=True)

        save_path = f"./cog/{file.filename}"
        cog_name = f"cog.{file.filename[:-3]}"

        try:
            await file.save(save_path)

            # 如果已經載入，先卸載
            if cog_name in self.bot.extensions:
                await self.bot.unload_extension(cog_name)

            # 載入（或重新載入）
            await self.bot.load_extension(cog_name)

            await ctx.followup.send(f"✅ Cog `{file.filename}` 已成功更新並重新載入！", ephemeral=True)
        except Exception as e:
            await ctx.followup.send(f"❌ 發生錯誤：```{e}```", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(CogManager(bot))
