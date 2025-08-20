import discord
from discord.ext import commands
from datetime import datetime
import os
import random
import utils

gacha_rate = [785, 185, 30] # 各稀有度的抽中機率 N, R, SR
gacha_rate_fes = [755, 185, 60] # FES 模式下的抽中機率 N, R, SR
gacha_result = [
    "<:BA_gacha_N:1407235400346505226>",
    "<:BA_gacha_R:1407235415446126663>",
    "<:BA_gacha_SR:1407235426300858408>"
]
allowed_channels = [1407248459949543455] # 機器人遊樂場

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/gacha.py: 日誌系統初始化完成")
        
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    def _get_gacha_result(self, is_fes=False):
        """隨機抽取一個結果"""
        rand = random.randint(1, 1000)

        # Fes gacha
        if is_fes:
            if rand <= gacha_rate_fes[0]:
                return gacha_result[0]  # N
            elif rand <= gacha_rate_fes[0] + gacha_rate_fes[1]:
                return gacha_result[1]  # R
            else:
                return gacha_result[2]  # SR
            
        # Normal gacha
        if rand <= gacha_rate[0]:
            return gacha_result[0]  # N
        elif rand <= gacha_rate[0] + gacha_rate[1]:
            return gacha_result[1]  # R
        else:
            return gacha_result[2]  # SR
        
    def _is_valid_request(self, ctx: discord.ApplicationContext):
        return utils.is_developer(ctx.author) or utils.is_in_bot_playground(ctx.channel)
    
    async def _send_no_permission_message(self, ctx: discord.ApplicationContext):
        await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
        self.logger.warning(f"❌ {ctx.author.name} 嘗試使用指令，但沒有權限。")

    @discord.slash_command(name="gacha", description="抽一抽普通池")
    async def gacha(self, ctx: discord.ApplicationContext):
        if not self._is_valid_request(ctx):
            await self._send_no_permission_message(ctx)
            return
        
        result = self._get_gacha_result()
        
        try:
            await ctx.respond(result)
        except Exception as e:
            await ctx.respond(f"❌ 發生錯誤: {e}")
            self.logger.error(f"Error in gacha command: {e}")

    @discord.slash_command(name="gacha10", description="抽十抽普通池")
    async def gacha10(self, ctx: discord.ApplicationContext):
        if self._is_valid_request(ctx) is False:
            await self._send_no_permission_message(ctx)
            return
        
        result1 = [self._get_gacha_result() for _ in range(5)]
        result2 = [self._get_gacha_result() for _ in range(5)]

        if result2[4] == gacha_result[0]:
            result2[4] = gacha_result[1]  # 保底

        results = " ".join(result1) + "\n" + " ".join(result2)
        
        try:
            await ctx.respond(results)
        except Exception as e:
            await ctx.respond(f"❌ 發生錯誤: {e}")
            self.logger.error(f"Error in gacha10 command: {e}")

    @discord.slash_command(name="fes_gacha", description="抽一抽 FES 池")
    async def fes_gacha(self, ctx: discord.ApplicationContext):
        if self._is_valid_request(ctx) is False:
            await self._send_no_permission_message(ctx)
            return
        
        result = self._get_gacha_result(is_fes=True)
        
        try:
            await ctx.respond(result)
        except Exception as e:
            await ctx.respond(f"❌ 發生錯誤: {e}")
            self.logger.error(f"Error in fes_gacha command: {e}")

    @discord.slash_command(name="fes_gacha10", description="抽十抽 FES 池")
    async def fes_gacha10(self, ctx: discord.ApplicationContext):
        if self._is_valid_request(ctx) is False:
            await self._send_no_permission_message(ctx)
            return
        
        result1 = [self._get_gacha_result(is_fes=True) for _ in range(5)]
        result2 = [self._get_gacha_result(is_fes=True) for _ in range(5)]

        if result2[4] == gacha_result[0]:
            result2[4] = gacha_result[1]  # 保底

        results = " ".join(result1) + "\n" + " ".join(result2)
        
        try:
            await ctx.respond(results)
        except Exception as e:
            await ctx.respond(f"❌ 發生錯誤: {e}")
            self.logger.error(f"Error in fes_gacha10 command: {e}")

def setup(bot: commands.Bot):
    bot.add_cog(Gacha(bot))