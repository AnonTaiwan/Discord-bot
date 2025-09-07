import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils

JERRY_ID = 654273506921414656
FABAO_ID = 271297517432340480

RECORD_FILE = utils.JSON_DIR / 'activity.json'

class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/activity.py: 日誌系統初始化完成")

        self.offline_time = None
        self.cooldown_list = {}

        utils.check_exist_or_create_json(self.logger, RECORD_FILE, default_content={"length": 0})

        self.length = utils.read_json(self.logger, RECORD_FILE, default_content={"length": 0}).get("length", 0)
        self.logger.info(f'Length: {self.length}')

    def __write_config(self):
        utils.write_json(self.logger, RECORD_FILE, {"length": self.length})

    def __format_length(self):
        if int(self.length + 0.6) == int(self.length):
            return str(int(self.length))
        else:
            return format(self.length, '.1f')

    async def send_message(self):
        content = f'偵測到 <@{JERRY_ID}> 偷打 LoL，紅布條長度增加為 {self.__format_length()} 公尺'
        await self.channel.send(content = content)
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)

    def __is_playing_league_of_legends(self, member):
        for activity in member.activities:
            if activity.type == discord.ActivityType.playing and activity.name == "League of Legends":
                return True
        return False
        
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if before.id != JERRY_ID and before.id != FABAO_ID:
            return
        
        if before.id == FABAO_ID:
            if before.display_name != after.display_name:
                self.logger.info(f"Member {after.name} changed nickname from {before.display_name} to {after.display_name}")
                content = f'📢 <@{FABAO_ID}> 的暱稱變更為 {after.display_name}'
                self.channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
                await self.channel.send(content = content)
            return

        if after.status == discord.Status.offline and before.status != discord.Status.offline:
            self.offline_time = datetime.now()
            self.logger.info(f"Member {after.name} is offline")
            content = f'偵測到 <@{JERRY_ID}> 下線，紅布條長度每秒增加 0.5 公尺'
            self.channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
            await self.channel.send(content = content)
            return

        if after.status == discord.Status.online and before.status == discord.Status.offline:
            if self.offline_time:
                offline_duration = datetime.now() - self.offline_time
                self.length += offline_duration.total_seconds() * 0.5
                self.logger.info(f"Member {after.name} was offline for {offline_duration}, length updated to {self.length}")
                self.__write_config()
                content = f'<@{JERRY_ID}> 已上線，共下線 {offline_duration.total_seconds()} 秒，紅布條長度增加至 {self.__format_length()} 公尺'
                self.channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
                await self.channel.send(content = content)

        if not self.__is_playing_league_of_legends(before) and self.__is_playing_league_of_legends(after):
            if after.name not in self.cooldown_list or datetime.now() - self.cooldown_list[after.name] > timedelta(minutes=5):
                self.logger.info(f"Member {after.name} started playing League of Legends")
                self.length += 1.5
                self.logger.info(f"Length updated to {self.length}")
                self.__write_config()
                await self.send_message()

        if self.__is_playing_league_of_legends(before) and not self.__is_playing_league_of_legends(after):
            self.logger.info(f"Member {after.name} stopped playing League of Legends")
            self.cooldown_list[after.name] = datetime.now()

def setup(bot: commands.Bot):
    bot.add_cog(Activity(bot))