import discord
from discord.ext import commands
import random
import utils

RECORD_FILE = utils.JSON_DIR / 'lotto.json'

class Lotto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/lotto.py: 日誌系統初始化完成")

        utils.check_exist_or_create_json(self.logger, RECORD_FILE, default_content={"lotto_pool": []})

        lotto_pool = utils.read_json(self.logger, RECORD_FILE, default_content={"lotto_pool": []}).get("lotto_pool", [])
        self.lotto_pool = [int(lotto) for lotto in lotto_pool]

    lotto_command_group = discord.SlashCommandGroup(name="lotto", description="樂透相關指令")

    async def __save_lotto(self):
        utils.write_json(self.logger, RECORD_FILE, {"lotto_pool": self.lotto_pool})

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @lotto_command_group.command(nam="draw", description="隨機抽選成員")
    async def draw(self, ctx: discord.ApplicationContext): # type: ignore
        try:
            user = random.choice(self.lotto_pool)
            await ctx.respond(f"抽到 <@{user}> 了！")
        except Exception as e:
            self.logger.error(f"抽選成員時發生錯誤：{e}")
            await ctx.respond("❌ 發生錯誤，無法完成抽選", ephemeral=True)

    @lotto_command_group.command(name="add-user", description="新增成員至抽選池")
    async def add_user(self, ctx: discord.ApplicationContext,
                                 user: discord.Option(discord.Member, description="欲加入抽選池的成員", required=True, default=None)): # type: ignore
        if user is None:
            await ctx.respond("❌ 請指定欲加入抽選池的成員")
            return
        
        if user.id in self.lotto_pool:
            await ctx.respond(f"❌ <@{user.id}> 已在抽選池中")
            return
        
        self.lotto_pool.append(user.id)
        self.lotto_pool.sort()
        await self.__save_lotto()

        try:
            await ctx.respond(f"✅ 已將 <@{user.id}> 新增至抽選池")
        except Exception as e:
            self.logger.error(f"Error responding to lotto add-user command: {e}")
            await ctx.respond("❌ 發生錯誤，請稍後再試", ephemeral=True)

    @lotto_command_group.command(name="remove-user", description="從抽選池移除成員")
    async def remove_user(self, ctx: discord.ApplicationContext,
                                    user: discord.Option(discord.Member, description="欲從抽選池移除的成員", required=True, default=None)): # type: ignore
        if user is None:
            await ctx.respond("❌ 請指定欲從抽選池移除的成員")
            return
        
        if user.id not in self.lotto_pool:
            await ctx.respond(f"❌ <@{user.id}> 不在抽選池中")
            return
        
        self.lotto_pool.remove(user.id)
        self.lotto_pool.sort()
        await self.__save_lotto()

        try:
            await ctx.respond(f"✅ 已將 <@{user.id}> 從抽選池移除")
        except Exception as e:
            self.logger.error(f"Error responding to lotto remove-user command: {e}")
            await ctx.respond("❌ 發生錯誤，請稍後再試", ephemeral=True)

    @lotto_command_group.command(name="list-users", description="列出抽選池中的成員")
    async def list_users(self, ctx: discord.ApplicationContext): # type: ignore
        if not self.lotto_pool:
            await ctx.respond("抽選池目前沒有成員")
            return
        
        embed = discord.Embed(title="抽選池成員列表", color=discord.Color.blue())

        embed.description = "\n".join(f"<@{user_id}>" for user_id in self.lotto_pool)

        try:
            await ctx.respond(embed=embed)
        except Exception as e:
            self.logger.error(f"Error responding to lotto list-users command: {e}")
            await ctx.respond("❌ 發生錯誤，請稍後再試", ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(Lotto(bot))