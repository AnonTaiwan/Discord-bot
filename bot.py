import discord
from discord.ext import bridge
import os
from urllib.parse import quote

bot = bridge.Bot(command_prefix=".",intents=discord.Intents.all())

for i in os.listdir("./cog"):
    if i.endswith(".py"):
        bot.load_extension(f"cog.{i[:-3]}")

@bot.event
async def on_ready():
    game = discord.Game("Blue Archive")
    print(f'Logged in as {bot.user}')
    await bot.change_presence(status=discord.Status.online, activity=game)

bot.run('') #Discord Bot Token
