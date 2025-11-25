import discord
from discord.ext import commands
import asyncio
import re
import utils
from datetime import datetime, timedelta

class Sixty(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/sixty.py: 日誌系統初始化完成")
        self.target_messages = []

    async def __get_target_member(self, message: discord.Message, times: int):
        messages = []
        if message.reference is not None:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                messages.append(ref_msg.author)
            except Exception as e:
                self.logger.error(f"無法取得引用訊息：{e}")
                return None
            return messages
        
        next_message = False
        async for msg in message.channel.history(limit=times + 10):
            if next_message:
                messages.append(msg.author)
                if len(messages) == times:
                    return messages
            if msg.id == message.id:
                next_message = True
        return None

    async def __timeout_user(self, user: discord.Member, duration: timedelta, reason: str) -> bool:
        try:
            await user.timeout_for(duration, reason=reason)
        except discord.Forbidden:
            self.logger.warning(f"❌ Cannot timeout {user.mention}")
        except Exception as e:
            self.logger.error(f"禁言成員 {user} 時發生錯誤：{e}")
            await self.logger.warning(f"❌ 發生錯誤，無法禁言 {user.mention}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if utils.is_operator(message.author):
            pattern = r"^我討厭你\s+(\d+)$"
            match = re.match(pattern, message.content)
            if "我討厭你" == message.content or match:
                if message.author.id == self.bot.user.id:
                    return

                if match:
                    times = int(match.group(1))
                else:
                    times = 1
                    
                target_member = await self.__get_target_member(message, times)
                if match:
                    await message.delete()
                
                if target_member:
                    for member in target_member:
                        print(f"Attempting to timeout member: {member}")
                        await self.__timeout_user(member, timedelta(minutes=1), "使用「我討厭你」指令被自動禁言")
            
def setup(bot):
    bot.add_cog(Sixty(bot))