from discord.ext import commands, tasks
from discord import Option, File
import discord
import os
import logging
from datetime import datetime
import utils

class CogManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/cogupdate.py: 日誌系統初始化完成")

        self.date = datetime.now().strftime("%Y%m%d")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.content == '!Cog_Update' and message.attachments and message.author.id in utils.DEVELOPER:
            # 檢查是否有附加檔案
            for attachment in message.attachments:
                if attachment.filename.endswith('.py'):
                    # 假設所有 cog 都在 cog 資料夾中
                    # 儲存檔案
                    from pathlib import Path
                    cog_path_obj = Path(f'cog/{attachment.filename}')
                    await attachment.save(fp=cog_path_obj)
                    await message.channel.send(f"✅ 已更新 `{attachment.filename}`")
                    self.logger.info(f'{message.author.name}: 更新 {attachment.filename}')

                    # 取得 cog 的模組名稱（例如：cog.my_cog）
                    cog_name = 'cog.' + attachment.filename[:-3]  # 去掉 .py

                    try:
                        # 如果已加載，先卸載
                        if cog_name in self.bot.extensions:
                            self.bot.reload_extension(cog_name)
                            self.logger.info(f'♻️ 已重新加載 `{cog_name}`')
                            await message.channel.send(f"♻️ 已重新加載 `{cog_name}`")
                        else:
                            self.bot.load_extension(cog_name)
                            self.logger.info(f'📥 已載入新的 Cog `{cog_name}`')
                            await message.channel.send(f"📥 已載入新的 Cog `{cog_name}`")
                    except Exception as e:
                        self.logger.warning(f'❌ 加載失敗: `{e}`')
                        await message.channel.send(f"❌ 加載失敗: `{e}`")

def setup(bot: commands.Bot):
    bot.add_cog(CogManager(bot))
