import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils

JERRY_ID = 654273506921414656
FABAO_ID = 271297517432340480
KONATA_TOKI_ID = 1106473991939559504

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
        content = f'老公 <@{JERRY_ID}> 又偷打 LoL，我要繼續將你的紅地毯長度增加為 {self.__format_length()} 公尺'
        await self.enrich_cog.invoke_jerry_webhook(content, str(JERRY_ID))

        # content = f'偵測到 <@{JERRY_ID}> 偷打 LoL，紅地毯長度增加為 {self.__format_length()} 公尺'
        # await self.channel.send(content = content)
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
        
        self.enrich_cog = self.bot.get_cog('EnrichCog')
        if not self.enrich_cog:
            print('EnrichCog not found!')

    def __is_playing_league_of_legends(self, member):
        for activity in member.activities:
            if activity.type == discord.ActivityType.playing and activity.name == "League of Legends":
                return True
        return False
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.id == FABAO_ID:
            if before.display_name != after.display_name:
                self.logger.info(f"Member {after.name} changed nickname from {before.display_name} to {after.display_name}")
                content = f'📢 <@{FABAO_ID}> 的暱稱變更為 {after.display_name}'
                self.channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
                await self.channel.send(content = content)
            return
        
        fabao_keywords = ["法堡", "Fabao", "fabao", "FABAO"]
        keyword_in_before = False
        keyword_in_after = False
        for keyword in fabao_keywords:
            if keyword in before.display_name:
                keyword_in_before = True
            if keyword in after.display_name:
                keyword_in_after = True

        if not keyword_in_before and keyword_in_after:
            self.logger.info(f"Member {after.name} changed nickname to include keyword '{keyword}'")
            content = f'📢 <@{after.id}> 新開了一間法堡分店「{after.display_name}」'
            self.channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
            await self.channel.send(content = content)
            return

        if keyword_in_before and not keyword_in_after:
            self.logger.info(f"Member {after.name} changed nickname to remove keyword '{keyword}'")
            content = f'📢 <@{after.id}> 的法堡分店「{before.display_name}」歇業了'
            self.channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
            await self.channel.send(content = content)
            return
        
        if keyword_in_before and keyword_in_after and after.display_name != before.display_name:
            self.logger.info(f"Member {after.name} changed nickname but still includes keyword '{keyword}'")
            content = f'📢 <@{after.id}> 的法堡分店改名為「{after.display_name}」'
            self.channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
            await self.channel.send(content = content)
            return
        
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if before.id != JERRY_ID:
            return

        if after.status == discord.Status.offline and before.status != discord.Status.offline:
            self.offline_time = datetime.now()
            self.logger.info(f"Member {after.name} is offline")

            content = f'啊...老公離開了...我會想你的... <@{JERRY_ID}>，這段時間我來繼續為你織紅地毯吧！'
            self.enrich_cog.invoke_jerry_webhook(content, str(JERRY_ID))
            
            # content = f'偵測到 <@{JERRY_ID}> 下線，紅地毯長度每秒增加 0.5 公尺'
            # self.channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
            # await self.channel.send(content = content)
            return

        if after.status == discord.Status.online and before.status == discord.Status.offline:
            if self.offline_time:
                offline_duration = datetime.now() - self.offline_time
                self.length += offline_duration.total_seconds() * 0.5
                self.logger.info(f"Member {after.name} was offline for {offline_duration}, length updated to {self.length}")
                self.__write_config()

                content = f'歡迎老公 <@{JERRY_ID}> 回來，我等你回來等了 {offline_duration.total_seconds()} 秒呢！\n這段期間我把紅地毯長度延長至 {self.__format_length()} 公尺了喔！'
                await self.enrich_cog.invoke_jerry_webhook(content, str(JERRY_ID))

                # content = f'<@{JERRY_ID}> 已上線，共下線 {offline_duration.total_seconds()} 秒，紅地毯長度增加至 {self.__format_length()} 公尺'
                # self.channel = self.bot.get_channel(utils.OFFTOPIC_CHANNEL_ID)
                # await self.channel.send(content = content)

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