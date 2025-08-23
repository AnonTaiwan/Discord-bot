import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import random
import pytz
import utils

#"大吉" Daikichi
#"吉"   Kichi
#"中吉" Chukichi
#"小吉" Shokichi
#"末吉" Suekichi
#"凶"   Kyo
#"大凶" Daikyo
omikuji_results = [
    "Daikichi",
    "Kichi", 
    "Chukichi", 
    "Shokichi", 
    "Suekichi", 
    "Kyo",
    "Daikyo"
]

timezone = pytz.timezone('Asia/Taipei')  # 設定時區為台北時間
daily_reset = time(hour=0, minute=6, second=0, tzinfo=timezone)  # 每日訊息時間設定

RECORD_FILE = utils.JSON_DIR / 'omikuji.json'
OMIKUJI_STATIC_DIR = utils.STATIC_DIR / 'omikuji'

class Omikuji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.daily_message_sent = False

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/omikuji.py: 日誌系統初始化完成")

        utils.check_exist_or_create_json(self.logger, RECORD_FILE, default_content={"omikuji": []})

        self.omikuji = utils.read_json(self.logger, RECORD_FILE, default_content={"omikuji": []}).get("omikuji", [])

    def save_omikuji(self):
        utils.write_json(self.logger, RECORD_FILE, {"omikuji": self.omikuji})

    @commands.Cog.listener()
    async def on_ready(self):
        self.daily_message.start()

    @discord.slash_command(name="omikuji", description="抽籤 (此功能由 Kevin 提供)")
    async def draw_omikuji(self, ctx: discord.ApplicationContext):
        if ctx.author.id in self.omikuji:
            await ctx.respond("你今天已經抽過籤了！請明天再來。")
            return

        weights = [0.05, 0.1, 0.2, 0.3, 0.2, 0.1, 0.05]  
        result = random.choices(omikuji_results, weights=weights)[0]

        try:
            PIC_PATH = OMIKUJI_STATIC_DIR / f'{result}.jpg'
            if PIC_PATH.exists():
                pic = discord.File(str(PIC_PATH), filename=PIC_PATH.name)
                await ctx.respond(file=pic,content = f"抽到的籤是：{result}")
            else:
                await ctx.respond(f"抽到的籤是：{result}")
            self.omikuji.append(ctx.author.id)
            self.save_omikuji()
        except Exception as e:
            self.logger.error(f"Error responding to omikuji command: {e}")
            await ctx.respond("抽籤失敗，請稍後再試。")

    @discord.slash_command(name="reset-omikuji", description="重置使用者抽籤")
    async def reset_omikuji(self, ctx: discord.ApplicationContext,
                            user: discord.Member = None):
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用這個指令。", ephemeral=True)
            return
        
        if user is None:
            await ctx.respond("請指定一個使用者來重置抽籤名單。", ephemeral=True)
            return
        
        if user.id in self.omikuji:
            self.omikuji.remove(user.id)
            self.save_omikuji()
        
        await ctx.respond(f"<@{user.id}> 已被重置。")

    @discord.slash_command(name="reset-omikuji-all", description="重置所有使用者抽籤")
    async def reset_omikuji_all(self, ctx: discord.ApplicationContext):
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用這個指令。", ephemeral=True)
            return
        
        self.omikuji = []
        self.save_omikuji()
        
        await ctx.respond("所有使用者的抽籤已被重置。")

    @tasks.loop(time=daily_reset)
    async def daily_message(self):
        if self.daily_message_sent:
            return

        self.omikuji = []
        self.save_omikuji()

        channel = self.bot.get_channel(utils.TEST_CHANNEL_ID) 
        if channel:
            await channel.send("每日運勢抽籤已重置！")
        else:
            self.logger.error("無法找到指定的頻道。")

        self.daily_message_sent = True

    @daily_message.after_loop
    async def after_daily_message(self):
        now = datetime.now(timezone)
        if now != daily_reset:
            self.daily_message_sent = False

def setup(bot: commands.Bot):
    bot.add_cog(Omikuji(bot))