import discord
from discord.ext import commands
from datetime import timedelta
from internal import utils
from model import commend

class Commend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/commend.py: 日誌系統初始化完成")

    commend_command_group = discord.SlashCommandGroup(name="commend", description="表揚相關指令")

    async def __timeout_user(self, ctx: discord.ApplicationContext, user: discord.Member, duration: timedelta, reason: str) -> bool:
        try:
            await user.timeout_for(duration, reason=reason)
        except discord.Forbidden:
            await ctx.send(f"❌ Cannot timeout {user.mention}")
            return False
        except Exception as e:
            self.logger.error(f"禁言成員 {user} 時發生錯誤：{e}")
            await ctx.send(f"❌ 發生錯誤，無法禁言 {user.mention}")
            return False

        return True

    @commands.Cog.listener()
    async def on_ready(self):
        self.playground_channel = self.bot.get_channel(utils.BOT_PLAYGROUND_CHANNEL_ID)

    async def send_commendation(self, user: discord.Member, reason: str):
        if user.id not in self.commendation:
            self.commendation[user.id] = 0

        embed = discord.Embed(title="已表揚成員", color=discord.Color.green())

        embed.add_field(name="被表揚成員", value=f"{user.mention}", inline=False)
        embed.add_field(name="表揚理由", value=reason if reason else "N/A", inline=False)

        try:
            await self.playground_channel.send(embed=embed)

            # if self.commendation[user.id] == 3:
            #     self.commendation[user.id] = 0
            #     await self.__save_commend()

            #     if not await self.__timeout_user(ctx, user, timedelta(minutes=1), reason="達成三次表揚，獲得 60 秒的禁言獎勵"):
            #         return

            #     embed = discord.Embed(title="獲得禁言獎勵", color=discord.Color.gold())

            #     embed.add_field(name="成員", value=f"{user.mention}", inline=False)
            #     embed.add_field(name="獎勵", value="達成三次表揚，獲得 60 秒的禁言獎勵", inline=False)

            #     await ctx.send(embed=embed)
        except Exception as e:
            self.logger.error(f"表揚成員時發生錯誤：{e}")
            await self.playground_channel.send("❌ 發生錯誤，無法完成表揚。")

    @commend_command_group.command(name="new", description="表揚成員")
    async def commend(self, ctx: discord.ApplicationContext,
                      user: discord.Option(discord.Member, description="要表揚的成員", required=True, default=None), # type: ignore
                      reason: discord.Option(description="表揚理由", required=False, default=""), # type: ignore
                      record: discord.Option(bool, description="是否紀錄", required=False, default=True)): # type: ignore
        if not utils.is_admin(ctx.author):
            await ctx.respond("❌ 你沒有權限使用這個指令。", ephemeral=True)
            return

        if user is None:
            await ctx.respond("請指定一個使用者來表揚。", ephemeral=True)
            return

        commendation = commend.create_or_update(user.id, increment=1)

        embed = discord.Embed(title="已表揚成員", color=discord.Color.green())

        embed.add_field(name="被表揚成員", value=f"{user.mention}", inline=False)
        embed.add_field(name="表揚理由", value=reason if reason else "N/A", inline=False)

        try:
            await ctx.respond(embed=embed)

            if commendation.amount >= 3:
                commendation = commend.create_or_update(user.id, set_amount=0)

                if not await self.__timeout_user(ctx, user, timedelta(minutes=1), reason="達成三次表揚，獲得 60 秒的禁言獎勵"):
                    return

                embed = discord.Embed(title="獲得禁言獎勵", color=discord.Color.gold())

                embed.add_field(name="成員", value=f"{user.mention}", inline=False)
                embed.add_field(name="獎勵", value="達成三次表揚，獲得 60 秒的禁言獎勵", inline=False)

                await ctx.send(embed=embed)
        except Exception as e:
            self.logger.error(f"表揚成員時發生錯誤：{e}")
            await ctx.respond("❌ 發生錯誤，無法完成表揚。")

    @commend_command_group.command(name="list", description="查看成員的表揚次數")
    async def show_commendations(self, ctx: discord.ApplicationContext): # type: ignore
        try:
            await ctx.defer(ephemeral=True)
        except Exception as e:
            self.logger.error(f"Error deferring response in show_commendations: {e}")
            await ctx.respond("❌ 發生錯誤", ephemeral=True)
            return

        embed = discord.Embed(title="所有表揚次數", color=discord.Color.purple())

        commendations = commend.list_all()

        commend_times = [[] for _ in range(3)]
        try:
            if not commendations:
                embed.add_field(name="目前沒有任何表揚紀錄。", value="\u200b", inline=False) # 使用零寬空格避免 Discord 不顯示欄位
            else:
                for commendation in commendations:
                    member = ctx.guild.get_member(commendation.user_id)
                    if member:
                        commend_times[commendation.amount].append(member.mention)

                for i in range(1, 3):
                    if commend_times[i]:
                        embed.add_field(name=f"已被表揚 {i} 次", value="\n".join(commend_times[i]), inline=False)
                    else:
                        embed.add_field(name=f"已被表揚 {i} 次", value="無", inline=False)

            await ctx.respond(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"查看表揚次數時發生錯誤：{e}")
            await ctx.respond("❌ 發生錯誤", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(Commend(bot))
