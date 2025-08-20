import discord
from discord.ext import commands, bridge, tasks
import json
import logging
from datetime import datetime, timedelta
import os

CHANNEL_ID = 1354880766126985358
JERRY_ID = 654273506921414656

class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_logging()
        self.offline_time = None
        self.cooldown_list = {}

        self._check_config_exist()
        self._read_config()

    def _check_config_exist(self):
        if not os.path.exists('config.json'):
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump({ "length": 0 }, f, ensure_ascii=False, indent=4)
            self.logger.info("config.json 不存在，已創建一個空的 config.json")
        else:
            self.logger.info("config.json 已存在")

    def _read_config(self):
        with open('config.json', 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
                self.logger.info("已成功讀取 config.json")
            except json.JSONDecodeError as e:
                self.logger.error(f"讀取 config.json 時發生錯誤: {e}")
                config = { "length": 0 }
        self.length = config.get("length", 0)

        self.logger.info(f'Length: {self.length}')

    def _write_config(self):
        with open('config.json', 'w', encoding='utf-8') as f:
            try:
                json.dump({ "length": self.length }, f, ensure_ascii=False, indent=4)
                self.logger.info("已成功寫入 config.json")
            except Exception as e:
                self.logger.error(f"寫入 config.json 時發生錯誤: {e}")

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
        self.logger.info("cog/activity.py: 日誌系統初始化完成")

    def _format_length(self):
        if int(self.length + 0.6) == int(self.length):
            return str(int(self.length))
        else:
            return format(self.length, '.1f')

    async def send_message(self):
        content = f'偵測到 <@{JERRY_ID}> 偷打 LoL，紅布條長度增加為 {self._format_length()} 公尺'
        await self.channel.send(content = content)
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(CHANNEL_ID)

    def _is_playing_league_of_legends(self, member):
        for activity in member.activities:
            if activity.type == discord.ActivityType.playing and activity.name == "League of Legends":
                return True
        return False
        
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if before.id != JERRY_ID:
            return

        if after.status == discord.Status.offline and before.status != discord.Status.offline:
            self.offline_time = datetime.now()
            self.logger.info(f"Member {after.name} is offline")
            content = f'偵測到 <@{JERRY_ID}> 下線，紅布條長度每秒增加 0.5 公尺'
            self.channel = self.bot.get_channel(CHANNEL_ID)
            await self.channel.send(content = content)
            return

        if after.status == discord.Status.online and before.status == discord.Status.offline:
            if self.offline_time:
                offline_duration = datetime.now() - self.offline_time
                self.length += offline_duration.total_seconds() * 0.5
                self.logger.info(f"Member {after.name} was offline for {offline_duration}, length updated to {self.length}")
                self._write_config()
                content = f'<@{JERRY_ID}> 已上線，共下線 {offline_duration.total_seconds()} 秒，紅布條長度增加至 {self._format_length()} 公尺'
                self.channel = self.bot.get_channel(CHANNEL_ID)
                await self.channel.send(content = content)

        if not self._is_playing_league_of_legends(before) and self._is_playing_league_of_legends(after):
            if after.name not in self.cooldown_list or datetime.now() - self.cooldown_list[after.name] > timedelta(minutes=5):
                self.logger.info(f"Member {after.name} started playing League of Legends")
                self.length += 1.5
                self.logger.info(f"Length updated to {self.length}")
                self._write_config()
                await self.send_message()

        if self._is_playing_league_of_legends(before) and not self._is_playing_league_of_legends(after):
            self.logger.info(f"Member {after.name} stopped playing League of Legends")
            self.cooldown_list[after.name] = datetime.now()

def setup(bot: commands.Bot):
    bot.add_cog(Activity(bot))