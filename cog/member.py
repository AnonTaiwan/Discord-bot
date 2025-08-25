import discord
from discord.ext import commands
from typing import List
from datetime import datetime, timedelta, timezone
import utils

class MemberPage(discord.ui.View):
    def __init__(self, logger, members, per_page=25):
        super().__init__(timeout=None)
        self.logger = logger
        self.members = members
        self.per_page = per_page
        self.current_page = 0

    def get_page_embed(self):
        pass

    @discord.ui.button(label="⏮️ First", style=discord.ButtonStyle.primary)
    async def go_to_first(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = 0

        try:
            await interaction.response.edit_message(embed=self.get_page_embed(), view=self)
        except Exception as e:
            self.logger.error(f"Error updating member page: {e}")
            await interaction.response.send_message("❌ 發生錯誤，無法更新頁面。", ephemeral=True)

    @discord.ui.button(label="⏪ Prev", style=discord.ButtonStyle.secondary)
    async def prev_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1

        try:
            await interaction.response.edit_message(embed=self.get_page_embed(), view=self)
        except Exception as e:
            self.logger.error(f"Error updating member page: {e}")
            await interaction.response.send_message("❌ 發生錯誤，無法更新頁面。", ephemeral=True)

    @discord.ui.button(label="⏩ Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.current_page < (len(self.members) - 1) // self.per_page:
            self.current_page += 1

        try:
            await interaction.response.edit_message(embed=self.get_page_embed(), view=self)
        except Exception as e:
            self.logger.error(f"Error updating member page: {e}")
            await interaction.response.send_message("❌ 發生錯誤，無法更新頁面。", ephemeral=True)

    @discord.ui.button(label="⏭️ End", style=discord.ButtonStyle.primary)
    async def go_to_end(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page = (len(self.members) - 1) // self.per_page

        try:
            await interaction.response.edit_message(embed=self.get_page_embed(), view=self)
        except Exception as e:
            self.logger.error(f"Error updating member page: {e}")
            await interaction.response.send_message("❌ 發生錯誤，無法更新頁面。", ephemeral=True)

class NonMygoMemberPage(MemberPage):
    def __init__(self, bot, logger, ctx, members, per_page=25):
        super().__init__(logger, members, per_page)
        self.bot = bot
        self.ctx = ctx

    def get_page_embed(self):
        embed = discord.Embed(title="未領取「迷失之人」身分組的成員", color=discord.Color.blue())
        start = self.current_page * self.per_page
        end = start + self.per_page
        
        embed.add_field(name="Member", value="\n".join(member.mention for member in self.members[start:end]) or "N/A", inline=True)
        embed.add_field(name="Join Time", value="\n".join(f"`{member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}`"
                                                          for member in self.members[start:end]) or "N/A", inline=True)

        embed.set_footer(text=f"Page {self.current_page + 1}/{(len(self.members) - 1) // self.per_page + 1}")
        return embed

    @discord.ui.button(label="❌ kick", style=discord.ButtonStyle.danger)
    async def kick(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            kick_cmd = self.bot.get_application_command("kick-non-mygo-members")
            await interaction.response.defer()
            await kick_cmd(self.ctx)
        except Exception as e:
            self.logger.error(f"Error invoking kick-non-mygo-members command from button: {e}")
            await interaction.response.send_message("❌ 發生錯誤，無法從 UI 執行踢出指令。", ephemeral=True)

class KickMemberPage(MemberPage):
    def __init__(self, logger, members, per_page=25):
        super().__init__(logger, members, per_page)

    def get_page_embed(self):
        embed = discord.Embed(title="已踢出未領取「迷失之人」身分組的人", color=discord.Color.red())

        start = self.current_page * self.per_page
        end = start + self.per_page

        embed.add_field(name="Member", value="\n".join(member.mention for member in self.members[start:end]) or "N/A", inline=True)
        embed.add_field(name="Join Time", value="\n".join(f"`{member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}`"
                                                        for member in self.members[start:end]) or "N/A", inline=True)
    
        embed.set_footer(text=f"共踢出 {len(self.members)} 名成員")

        embed.set_footer(text=f"Page {self.current_page + 1}/{(len(self.members) - 1) // self.per_page + 1}")
        return embed

class KickMenu(discord.ui.View):
    def __init__(self, logger, members):
        super().__init__(timeout=None)

        self.logger = logger
        self.members = members

        self._options = [
            discord.SelectOption(label="5 天", value="5", description="踢出 5 天未領取身分組的成員"),
            discord.SelectOption(label="10 天", value="10", description="踢出 10 天未領取身分組的成員"),
            discord.SelectOption(label="15 天", value="15", description="踢出 15 天未領取身分組的成員"),
            discord.SelectOption(label="30 天", value="30", description="踢出 30 天未領取身分組的成員"),
            discord.SelectOption(label="60 天", value="60", description="踢出 60 天未領取身分組的成員"),
            discord.SelectOption(label="90 天", value="90", description="踢出 90 天未領取身分組的成員")
        ]

        select_menu = discord.ui.Select(placeholder="選擇要踢出的成員條件", options=self._options, min_values=1, max_values=1)
        select_menu.callback = self.kick_member

        self.add_item(select_menu)

    async def kick_member(self, interaction: discord.Interaction):
        if not utils.is_developer(interaction.user):
            await self.logger.error(f"Error updating member page: {e}")
            await interaction.response.send_message("❌ 你沒有權限使用此功能。", ephemeral=True)
            return

        selected_days = int(interaction.data['values'][0])
        
        threshold_time = datetime.now(timezone.utc) - timedelta(days=selected_days)
        members_to_kick = [member for member in self.members if member.joined_at < threshold_time]

        if not members_to_kick:
            await interaction.response.send_message("沒有成員符合踢出的條件。")
            return

        try:
            kicked = []
            for member in members_to_kick:
                try:
                    await member.kick(reason=f"未領取「迷失之人」身分組超過 {selected_days} 天")
                    kicked.append(member)
                except discord.Forbidden:
                    self.logger.warning(f"無法踢出成員 {member.name}，缺少權限。")
                except Exception as e:
                    self.logger.error(f"踢出成員 {member.name} 時發生錯誤: {e}")

            view = KickMemberPage(self.logger, kicked)

            await interaction.response.send_message(embed=view.get_page_embed(), view=view)
        except Exception as e:
            self.logger.error(f"Error kicking members: {e}")
            await interaction.response.send_message("❌ 發生錯誤，無法執行指令。", ephemeral=True)

class Member(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/member.py: 日誌系統初始化完成")

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    async def __get_non_mygo_members(self, guild):
        members = guild.members
        non_mygo_members = [member for member in members if
                            not any(role.id == utils.MYGO_ROLE_ID or role.id == utils.BOT_ROLE_ID
                            for role in member.roles)]
        non_mygo_members.sort(key=lambda m: m.joined_at or discord.utils.snowflake_time(m.id))
        return non_mygo_members

    @discord.slash_command(name="non-mygo-members", description="取得所有未領取「迷失之人」身分組的人")
    async def non_mygo_members(self, ctx: discord.ApplicationContext):
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return

        if ctx.guild is None:
            await ctx.respond("此指令只能在伺服器中使用。", ephemeral=True)
            return

        try:
            non_mygo_members = await self.__get_non_mygo_members(ctx.guild)

            if not non_mygo_members:
                await ctx.respond("所有成員都已領取「迷失之人」身分組。")
                return
            
            view = NonMygoMemberPage(self.bot, self.logger, ctx, non_mygo_members)
            await ctx.respond(embed=view.get_page_embed(), view=view)
        except Exception as e:
            self.logger.error(f"Error responding to non_mygo_members command: {e}")
            await ctx.respond("❌ 發生錯誤，無法取得成員列表。")

    @discord.slash_command(name="kick-non-mygo-members", description="踢出未領取「迷失之人」身分組的人")
    async def kick_non_mygo_members(self, ctx: discord.ApplicationContext):
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return

        if ctx.guild is None:
            await ctx.respond("此指令只能在伺服器中使用。", ephemeral=True)
            return

        try:
            non_mygo_members = await self.__get_non_mygo_members(ctx.guild)

            await ctx.respond("請選擇要踢出的成員條件：", view=KickMenu(self.logger, non_mygo_members))
        except Exception as e:
            self.logger.error(f"Error responding to kick_non_mygo_members command: {e}")
            await ctx.respond("❌ 發生錯誤，無法取得成員列表。")

def setup(bot: commands.Bot):
    bot.add_cog(Member(bot))