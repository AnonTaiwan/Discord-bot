import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import re
from internal import utils

class TraceLinkWarning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger("InstagramTraceLinkWarning")
        self.logger.info("cog/trace_link_warning.py: 日誌系統初始化完成")

        self.FIX_TWEET_USER_ID = 1164651057243238400

        self.FB_PATTERN = r"https:\/\/www\.(facebook|fb)\.com\/share\/p\/[a-zA-Z0-9]+\/"

    @commands.Cog.listener()
    async def on_ready(self):
        self.FIX_TWEET_USER = self.bot.get_user(self.FIX_TWEET_USER_ID)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if "instagram.com" in message.content and "igsh=" in message.content:
            await self.__send_warning(message, mode = "ig")

        if re.match(self.FB_PATTERN, message.content):
            await self.__send_warning(message, mode = "fb")

    async def __send_warning(self, message, **kwargs):
        if 'mode' not in kwargs:
            self.logger.error("Mode not specified for warning.")
            return

        descriptions = {
            "ig": "此連結帶有追蹤參數 \"igsh\"，可能會洩漏您的個人帳號資料",
            "fb": """此連結帶有 Facebook 追蹤參數，可能會洩漏您的個人帳號資料\n請先使用瀏覽器訪問連結後，再複製轉換過的連結\n轉換後的連結不會是 `https://www.facebook.com/share/p/xxx/` 的格式"""
        }

        embed = discord.Embed(
            title="⚠️ 警告",
            description=descriptions.get(kwargs['mode'], "此連結可能會洩漏您的個人帳號資料"),
            color=discord.Color.orange()
        )

        delete_message_button = Button(label="刪除訊息", style=discord.ButtonStyle.red)

        async def delete_message_callback(interaction: discord.Interaction):
            if interaction.user == message.author:
                await message.delete()

                link = ""
                if kwargs['mode'] == "ig":
                    link = re.search(r"(https:\/\/www\.instagram\.com)\/[^\s\?]+", message.content).group(0)
                elif kwargs['mode'] == "fb":
                    link = re.search(self.FB_PATTERN, message.content).group(0)
                    link = link.replace("/p/", "/")

                if link[-1] == "/":
                    link = link[:-1]
                link = link.replace("www.", "")

                async for msg in message.channel.history(limit=100):
                    if msg.author == self.FIX_TWEET_USER and link in msg.content:
                        await msg.delete()
                        break

                new_embed = discord.Embed(
                    title="✅ 訊息已刪除",
                    color=discord.Color.green()
                )

                new_embed.set_footer(text="此訊息將在 5 秒後自動刪除")

                await interaction.message.edit(embed=new_embed, view=None)
                await asyncio.sleep(5)
                await interaction.message.delete()
            else:
                await interaction.response.send_message("❌ 僅訊息發送者可以刪除該訊息。", ephemeral=True)

        delete_message_button.callback = delete_message_callback

        ignore_button = Button(label="忽略警告", style=discord.ButtonStyle.success)

        async def ignore_button_callback(interaction: discord.Interaction):
            if interaction.user == message.author:
                await interaction.message.delete()
            else:
                await interaction.response.send_message("❌ 僅訊息發送者可以忽略該警告。", ephemeral=True)

        ignore_button.callback = ignore_button_callback

        view = View()
        view.add_item(delete_message_button)
        view.add_item(ignore_button)

        await message.channel.send(embed=embed, view=view)

def setup(bot):
    bot.add_cog(TraceLinkWarning(bot))
