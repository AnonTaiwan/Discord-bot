import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils
import random
from pypinyin import pinyin, lazy_pinyin, Style

LLAMA_ID = 870191937913774091

LLAMA_VIRUS_RATIO = 0.003

class AutoReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/auto_reply.py: 日誌系統初始化完成")
        self.reply = [  # (reply, probability, tag user, [match substrings])
            ("咪咪洛德 幹他", 1, False, ["mi1mi1luo4de2", "mi1mi1luo4de5"]),
            ("掐囉～(∠·ω< )⌒★", 1, False, ["掐"]),
            ("# 羊 駝 病 毒", 0.25, False, ["羊駝"]),
            ("對了！說到機...", 1, False, ["機吧"]),
            ("不行", 1, False, ["我可不可以吃東西"]),
            ("你再問問看", 1, False, ["你除了說不行，還會說什麼"]),
            ("%s 被 琪涵雅的女裝 可愛死了", 1, True, ["琪涵雅女裝"]),
            ("%s 被 優打的女裝 可愛死了", 1, True, ["優打女裝", "yoda 女裝", "yoda女裝"]),
            ("%s 被 高麗菜的女裝 可愛死了", 1, True, ["高麗菜女裝", "懷勳女裝"]),
            ("要支持阿農台灣一輩子喔 👊", 1, False, ["一輩子"]),
            ("%s 你是湊企鵝 你是湊企鵝 你是湊企鵝 你是誰呀？", 1, True, ["湊企鵝"])
        ]
        self.special_care = [  # (USER ID, reply, probability)
            (870191937913774091, "# 羊 駝 病 毒", 0.003),  # llama
            (271297517432340480, "漢堡煎完沒，沒有還不趕快去煎", 0.003)  # memelord
        ]

    def __ignore_message(self, message: discord.Message) -> bool:
        return message.author.id == self.bot.user.id or message.channel.id == utils.TTS_CHANNEL_ID
    
    async def __special_care(self, message: discord.Message):
        for (user_id, reply, probability) in self.special_care:
            if message.author.id == user_id and random.random() <= probability:
                try:
                    await message.channel.send(reply)
                except Exception as e:
                    self.logger.error(f"無法發送特殊關懷訊息：{e}")

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.__ignore_message(message):
            return

        await self.__special_care(message)

        content_pinyin = "".join(lazy_pinyin(message.content, style=Style.TONE2, tone_sandhi=True, neutral_tone_with_five=True))
        replied = False
        
        for (reply_msg, probability, tag_user, match_strings) in self.reply:
            for match_str in match_strings:
                if (match_str in content_pinyin or match_str in message.content) and random.random() <= probability:
                    if tag_user:
                        reply_msg = reply_msg % (message.author.mention if message.reference is None else (await message.channel.fetch_message(message.reference.message_id)).author.mention)

                    if message.reference is not None and not replied:
                        try:
                            ref_msg = await message.channel.fetch_message(message.reference.message_id)
                            if ref_msg.author.id == self.bot.user.id:
                                return
                            
                            await ref_msg.reply(reply_msg)
                            replied = True
                            break
                        except Exception as e:
                            self.logger.error(f"無法取得引用訊息：{e}")
                        
                    await message.channel.send(reply_msg)
                    break
                
def setup(bot: commands.Bot):
    bot.add_cog(AutoReply(bot))