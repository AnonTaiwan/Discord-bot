import discord
from discord.ext import commands
from typing import List
from datetime import datetime, timedelta, timezone
import utils

RECORD_FILE = utils.JSON_DIR / 'commend.json'

class Commend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/commend.py: 日誌系統初始化完成")

        utils.check_exist_or_create_json(self.logger, RECORD_FILE, default_content={"commendation": {}})

        self.commendation = utils.read_json(self.logger, RECORD_FILE, default_content={"commendation": {}}).get("commendation", {})

    async def __save_commend(self):
        utils.write_json(self.logger, RECORD_FILE, {"commend": self.commendation})

    async def __timeout_user(self, ctx: discord.ApplicationContext, user: discord.Member, duration: timedelta, reason: str) -> bool:
        try:
            await user.timeout_for(duration, reason=reason)
        except discord.Forbidden:
            await ctx.send(f"❌ Cannot timeout {user.mention}")
            return False
        except Exception as e:
            self.logger.error(f"禁言成員 {user} 時發生錯誤: {e}")
            await ctx.send(f"❌ 發生錯誤，無法禁言 {user.mention}")
            return False

        return True

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @discord.slash_command(name="commend", description="表揚成員")
    async def commend(self, ctx: discord.ApplicationContext,
                      user: discord.Option(discord.Member, description="要表揚的成員", required=True, default=None),
                      reason: discord.Option(description="表揚理由", required=False, default="")):
        if not utils.is_operator(ctx.author):
            await ctx.respond("❌ 你沒有權限使用這個指令。", ephemeral=True)
            return

        if user is None:
            await ctx.respond("請指定一個使用者來表揚。", ephemeral=True)
            return
        
        if ctx.author.id not in self.commendation:
            self.commendation[ctx.author.id] = 0

        self.commendation[ctx.author.id] += 1

        embed = discord.Embed(title="已表揚成員", color=discord.Color.green())

        embed.add_field(name="被表揚成員", value=f"{user.mention}", inline=False)
        embed.add_field(name="表揚理由", value=reason if reason else "N/A", inline=False)

        try:
            await ctx.respond(embed=embed)

            if self.commendation[ctx.author.id] == 3:
                self.commendation[ctx.author.id] = 0

                if not await self.__timeout_user(ctx, ctx.author, timedelta(minutes=1), reason="達成三次表揚，獲得 60 秒的禁言獎勵"):
                    return

                embed = discord.Embed(title="獲得禁言獎勵", color=discord.Color.gold())

                embed.add_field(name="成員", value=f"{ctx.author.mention}", inline=False)
                embed.add_field(name="獎勵", value="達成三次表揚，獲得 60 秒的禁言獎勵", inline=False)

                await ctx.send(embed=embed)

            await self.__save_commend()
        except Exception as e:
            self.logger.error(f"表揚成員時發生錯誤: {e}")
            await ctx.respond("❌ 發生錯誤，無法完成表揚。", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(Commend(bot))