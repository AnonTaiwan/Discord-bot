import discord
from discord.ext import commands
import asyncio
import re
import utils
from datetime import datetime, timedelta

class SayItOnce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/sayitonce.py: 日誌系統初始化完成")
        self.target_messages = []

    async def __get_target_message(self, message: discord.Message, times: int):
        messages = []
        if message.reference is not None:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                messages.append(ref_msg)
            except Exception as e:
                self.logger.error(f"無法取得引用訊息：{e}")
                return None
            return messages
        
        next_message = False
        async for msg in message.channel.history(limit=times + 10):
            if next_message:
                messages.append(msg)
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
            return False
        except Exception as e:
            self.logger.error(f"禁言成員 {user} 時發生錯誤：{e}")
            await self.logger.warning(f"❌ 發生錯誤，無法禁言 {user.mention}")
            return False
        return True

    async def add_message_to_watchlist(self, message: discord.Message):
        self.target_messages.append(message)
        await asyncio.sleep(60)  
        self.target_messages.remove(message)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        pattern = r"^你再一句\s+(\d+)$"
        match = re.match(pattern, message.content)
        if "你再一句" == message.content or match:
            if message.author.id == self.bot.user.id:
                return
            
            if match:
                times = int(match.group(1))
            else:
                times = 1
                
            target_msgs = await self.__get_target_message(message, times)
            if match:
                await message.delete()
            
            reply_msg = "你再一句！" if times == 1 else f"你們再一句！"
            
            if target_msgs:
                await target_msgs[0].reply(reply_msg)
                for target_msg in target_msgs:
                    if utils.is_operator(message.author):
                        await self.add_message_to_watchlist(target_msg)

        for target in self.target_messages:
            if message.author == target.author and message.channel == target.channel:
                try:
                    if not await self.__timeout_user(message.author, timedelta(minutes=1), reason="你還真的再一句啊！"):
                        return
                    embed = discord.Embed(title="你再一句！", description=f"{message.author.mention} 你還真的再一句啊！我討厭你 (60s)", color=discord.Color.gold())
                    await message.reply(embed=embed)
                except Exception as e:
                    self.logger.error(f"你再一句：{e}")
                break
            
def setup(bot: commands.Bot):
    bot.add_cog(SayItOnce(bot))