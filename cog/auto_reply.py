import discord
from discord.ext import commands
from internal import utils
import random
from pypinyin import lazy_pinyin, Style

LLAMA_ID = 870191937913774091

LLAMA_VIRUS_RATIO = 0.003

class AutoReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/auto_reply.py: 日誌系統初始化完成")
        self.reply = [  # (reply, probability, [match substrings])
            ("咪咪洛德 幹他", 1, ["mi1mi1luo4de2", "mi1mi1luo4de5"]),
            ("掐囉～(∠·ω< )⌒★", 1, ["掐"]),
            ("# 羊 駝 病 毒", 0.25, ["羊駝"]),
            ("快用你那無敵的羊駝病毒想想辦法", 0.5, ["羊駝病毒"]),
            ("對了！說到機...", 1, ["機吧"]),
            ("不行", 1, ["我可不可以吃東西"]),
            ("你再問問看", 1, ["你除了說不行，還會說什麼"]),
            ("要支持阿農台灣一輩子喔 👊", 1, ["一輩子"]),
        ]
        self.tagged_reply = [  # (reply, probability, [match substrings])
            ("%s 被 琪涵雅的女裝 可愛死了", 1, ["琪涵雅女裝"]),
            ("%s 被 優打的女裝 可愛死了", 1, ["優打女裝", "yoda 女裝", "yoda女裝"]),
            ("%s 被 高麗菜的女裝 可愛死了", 1, ["高麗菜女裝", "懷勳女裝"]),
            ("%s 你是湊企鵝 你是湊企鵝 你是湊企鵝 你是誰呀？", 1, ["湊企鵝"]),
        ]
        self.sticker_reply = [  # (sticker_id, probability, [match substrings])
            ("1493560382046867546", 1, ["薯KI", "薯ki", "薯Ki", "薯kI", "薯\\ KI", "薯\\ Ki", "薯\\ kI", "薯\\ kI"]),
        ]
        self.special_care = [  # (USER ID, reply, is_media, probability)
            (870191937913774091, "# 羊 駝 病 毒", False, 0.003),  # llama
            (271297517432340480, "漢堡煎完沒，沒有還不趕快去煎", False, 0.003),  # memelord
            (417680398211088384, "static/xiaoan_spam.png", True, 0.003),  # 小安
        ]

    def __ignore_message(self, message: discord.Message) -> bool:
        return message.author.id == self.bot.user.id or message.channel.id == utils.TTS_CHANNEL_ID

    async def __send_message(self, message: discord.Message, reply_msg: str, replied=False, is_sticker=False):
        if message.reference is not None and not replied:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                if ref_msg.author.id == self.bot.user.id:
                    return

                if is_sticker:
                    sticker_id = int(reply_msg)
                    sticker = self.bot.get_sticker(sticker_id) or await message.guild.fetch_sticker(sticker_id)
                    await ref_msg.reply(stickers=[sticker])
                else:
                    await ref_msg.reply(reply_msg)

                return
            except Exception as e:
                self.logger.error(f"無法取得引用訊息：{e}")

        try:
            if is_sticker:
                sticker_id = int(reply_msg)
                sticker = self.bot.get_sticker(sticker_id) or await message.guild.fetch_sticker(sticker_id)
                await message.channel.send(stickers=[sticker])
            else:
                await message.channel.send(reply_msg)
        except Exception as e:
            self.logger.error(f"無法發送訊息：{e}")

    async def __special_care(self, message: discord.Message):
        for (user_id, reply, is_media, probability) in self.special_care:
            if message.author.id == user_id and random.random() <= probability:
                try:
                    if is_media:
                        await message.channel.send(file=discord.File(reply))
                    else:
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

        for (reply_msg, probability, match_strings) in self.reply:
            for match_str in match_strings:
                if (match_str in content_pinyin or match_str in message.content) and random.random() <= probability:
                    await self.__send_message(message, reply_msg, replied)
                    replied = True

                    break

        for (reply_msg, probability, match_strings) in self.tagged_reply:
            for match_str in match_strings:
                if (match_str in content_pinyin or match_str in message.content) and random.random() <= probability:
                    reply_msg = reply_msg % (message.author.mention if message.reference is None else (await message.channel.fetch_message(message.reference.message_id)).author.mention)

                    await self.__send_message(message, reply_msg, replied)
                    replied = True

                    break

        for (sticker_id, probability, match_strings) in self.sticker_reply:
            for match_str in match_strings:
                if (match_str in content_pinyin or match_str in message.content) and random.random() <= probability:
                    await self.__send_message(message, sticker_id, replied, is_sticker=True)
                    replied = True

                    break

def setup(bot: commands.Bot):
    bot.add_cog(AutoReply(bot))
