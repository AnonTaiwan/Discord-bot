import discord
from discord.ext import commands
import json
import logging
from datetime import datetime
import os
import random

gacha_rate = [785, 185, 30] # 各稀有度的抽中機率 N, R, SR

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_logging()
        with open('JSON/bot.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.DEVELOPER = config.get("DEVELOPER")

    def setup_logging(self):
        """設置日誌系統"""
        # 創建 logs 目錄（如果不存在）
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # 設置日誌文件名（包含日期）
        log_filename = f'logs/fb_bot_{datetime.now().strftime("%Y%m%d")}.log'
        
        # 配置日誌格式
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # 配置日誌
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()  # 同時輸出到控制台
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("cog/gacha.py: 日誌系統初始化完成")
        
    @commands.Cog.listener()
    async def on_ready(self):
        # main channel
        # self.channel = self.bot.get_channel(1354880766126985358)
        # test channel
        self.channel = self.bot.get_channel(1405253533540024340)

    def _get_gacha_result(self):
        """隨機抽取一個結果"""
        rand = random.randint(1, 1000)
        if rand <= gacha_rate[0]:
            return "<:BA_gacha_N:1407235400346505226>"
        elif rand <= gacha_rate[0] + gacha_rate[1]:
            return "<:BA_gacha_R:1407235415446126663>"
        else:
            return "<:BA_gacha_SR:1407235426300858408>"

    @discord.slash_command(name="gacha", description="抽一抽")
    async def gacha(self, ctx: discord.ApplicationContext):
        has_allowed_role = any(role.id == 1359938675768557719 for role in ctx.author.roles) # 小編身份組
        if ctx.author.id not in self.DEVELOPER and has_allowed_role is False:
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 嘗試使用指令，但沒有權限。")
            return
        
        result = self._get_gacha_result()
        
        try:
            await ctx.respond(result)
        except Exception as e:
            await ctx.respond(f"❌ 發生錯誤: {e}")
            self.logger.error(f"Error in query command: {e}")

    @discord.slash_command(name="gacha10", description="抽十抽")
    async def gacha10(self, ctx: discord.ApplicationContext):
        has_allowed_role = any(role.id == 1359938675768557719 for role in ctx.author.roles) # 小編身份組
        if ctx.author.id not in self.DEVELOPER and has_allowed_role is False:
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            self.logger.warning(f"❌ {ctx.author.name} 嘗試使用指令，但沒有權限。")
            return
        
        result1 = [self._get_gacha_result() for _ in range(5)]
        result2 = [self._get_gacha_result() for _ in range(5)]

        if all(result == "<:BA_gacha_N:1407235400346505226>" for result in result1 + result2):
            result2[4] = "<:BA_gacha_R:1407235415446126663>"  # 保底

        results = " ".join(result1) + "\n" + " ".join(result2)
        
        try:
            await ctx.respond(results)
        except Exception as e:
            await ctx.respond(f"❌ 發生錯誤: {e}")
            self.logger.error(f"Error in query command: {e}")

def setup(bot: commands.Bot):
    bot.add_cog(Gacha(bot))