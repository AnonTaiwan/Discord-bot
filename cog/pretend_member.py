import aiohttp
import discord
from discord import Webhook
from discord.ext import commands

from model import user_webhook

from internal import utils


class PretendCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/pretend_member.py: 系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        utils.get_logger(__name__).info("PretendCog 已準備就緒")
        pass

    @discord.slash_command(name="fun_pretend", description="pretend to be other users by webhook")
    async def pretend(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Member,
        message: str,
        channel: discord.Option(discord.TextChannel, description="選擇頻道", required=False, default=None) = None,
    ):  # type: ignore
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。")
            return

        if channel is None:
            channel = ctx.channel

        await ctx.defer(ephemeral=True)

        try:
            webhook_data = user_webhook.get_webhook_data(member.id, channel.id)
            if webhook_data is None or not await utils.is_webhook_avaliable(webhook_data.webhook_id, self.bot):
                webhook_id, webhook_token = await utils.create_webhook(channel, member.id)
                if webhook_id is None or webhook_token is None:
                    return
                await user_webhook.update_user_webhook(member.id, channel.id, webhook_id, webhook_token)
            else:
                webhook_id, webhook_token = webhook_data.webhook_id, webhook_data.webhook_token

            async with aiohttp.ClientSession() as session:
                webhook = Webhook.partial(webhook_id, webhook_token, session=session)
                await webhook.fetch()
                await webhook.send(content=message)

            await ctx.respond(f"✅ 已成功在 {channel.mention} 傳送訊息。", ephemeral=True)

        except Exception as e:
            self.logger.error(f"在頻道 {channel.id} 傳送 webhook 訊息時發生錯誤：{e}")
            await ctx.respond("❌ 發生錯誤，無法傳送訊息。", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(PretendCog(bot))
