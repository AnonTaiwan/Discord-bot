import discord
from discord.ext import commands, tasks
from typing import List
from datetime import datetime, timedelta, timezone
from internal import utils

RECORD_FILE = utils.JSON_DIR / "member.json"

NOTIFY_ROLE = None
NO_MYGO_ROLE = None


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
        embed.add_field(
            name="Join Time",
            value="\n".join(f"`{member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}`" for member in self.members[start:end]) or "N/A",
            inline=True,
        )

        embed.set_footer(text=f"Page {self.current_page + 1}/{(len(self.members) - 1) // self.per_page + 1}")
        return embed

    @discord.ui.button(label="❌ kick", style=discord.ButtonStyle.danger)
    async def kick(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            kick_cmd = self.bot.get_application_command("member non-mygo kick")
            await interaction.response.defer()
            await kick_cmd(self.ctx)
        except Exception as e:
            self.logger.error(f"Error invoking member non-mygo kick command from button: {e}")
            await interaction.response.send_message("❌ 發生錯誤，無法從 UI 執行踢出指令。", ephemeral=True)


class KickComfirmPage(MemberPage):
    def __init__(self, logger, days, members, per_page=25):
        super().__init__(logger, members, per_page)

        self.days = days

    def get_page_embed(self):
        embed = discord.Embed(title="確認要踢出以下成員嗎？", color=discord.Color.orange())

        start = self.current_page * self.per_page
        end = start + self.per_page

        embed.add_field(name="Member", value="\n".join(member.mention for member in self.members[start:end]) or "N/A", inline=True)
        embed.add_field(
            name="Join Time",
            value="\n".join(f"`{member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}`" for member in self.members[start:end]) or "N/A",
            inline=True,
        )

        embed.set_footer(text=f"共 {len(self.members)} 名成員")

        embed.set_footer(text=f"Page {self.current_page + 1}/{(len(self.members) - 1) // self.per_page + 1}")
        return embed

    @discord.ui.button(label="❌ Confirm Kick", style=discord.ButtonStyle.danger)
    async def kick(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            kicked = []
            for member in self.members:
                try:
                    await member.kick(reason=f"未領取「迷失之人」身分組超過 {self.days} 天")
                    kicked.append(member)
                except discord.Forbidden:
                    self.logger.error(f"無法踢出成員 {member.name}，缺少權限。")
                except Exception as e:
                    self.logger.error(f"踢出成員 {member.name} 時發生錯誤：{e}")

            view = KickMemberPage(self.logger, kicked)

            await interaction.response.send_message(embed=view.get_page_embed(), view=view)
        except Exception as e:
            self.logger.error(f"Error kicking members: {e}")
            await interaction.response.send_message("❌ 發生錯誤，無法執行指令。", ephemeral=True)


class KickMemberPage(MemberPage):
    def __init__(self, logger, members, per_page=25):
        super().__init__(logger, members, per_page)

    def get_page_embed(self):
        embed = discord.Embed(title="已踢出未領取「迷失之人」身分組的人", color=discord.Color.red())

        start = self.current_page * self.per_page
        end = start + self.per_page

        embed.add_field(name="Member", value="\n".join(member.mention for member in self.members[start:end]) or "N/A", inline=True)
        embed.add_field(
            name="Join Time",
            value="\n".join(f"`{member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}`" for member in self.members[start:end]) or "N/A",
            inline=True,
        )

        embed.set_footer(text=f"共踢出 {len(self.members)} 名成員")

        embed.set_footer(text=f"Page {self.current_page + 1}/{(len(self.members) - 1) // self.per_page + 1}")
        return embed


class RemoveRolePage(MemberPage):
    def __init__(self, logger, role, members, per_page=25):
        super().__init__(logger, members, per_page)
        self.role = role

    def get_page_embed(self):
        embed = discord.Embed(title=f"已移除所有「{self.role}」身分組", color=discord.Color.green())

        start = self.current_page * self.per_page
        end = start + self.per_page

        embed.add_field(name="Member", value="\n".join(member.mention for member in self.members[start:end]) or "N/A", inline=True)

        embed.set_footer(text=f"共 {len(self.members)} 名成員")

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
            discord.SelectOption(label="90 天", value="90", description="踢出 90 天未領取身分組的成員"),
        ]

        select_menu = discord.ui.Select(placeholder="選擇要踢出的成員條件", options=self._options, min_values=1, max_values=1)
        select_menu.callback = self.kick_member

        self.add_item(select_menu)

    async def kick_member(self, interaction: discord.Interaction):
        if interaction.user is None:
            return

        if not utils.is_developer(interaction.user):
            await interaction.response.send_message("❌ 你沒有權限使用此功能。", ephemeral=True)
            return

        selected_days = int(interaction.data["values"][0])  # type: ignore

        threshold_time = datetime.now(timezone.utc) - timedelta(days=selected_days)
        members_to_kick = [member for member in self.members if member.joined_at < threshold_time]

        if not members_to_kick:
            await interaction.response.send_message("沒有成員符合踢出的條件。")
            return

        try:
            view = KickComfirmPage(self.logger, selected_days, members_to_kick)

            await interaction.response.send_message(embed=view.get_page_embed(), view=view)
        except Exception as e:
            self.logger.error(f"Error creating kick confirmation page: {e}")
            await interaction.response.send_message("❌ 發生錯誤，無法執行指令。")


class Member(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/member.py: 日誌系統初始化完成")

        utils.check_exist_or_create_json(self.logger, RECORD_FILE, default_content={"auto_detect": False})
        self.auto_detect = utils.read_json(self.logger, RECORD_FILE, default_content={"auto_detect": False}).get("auto_detect", False)

    member_command_group = discord.SlashCommandGroup(name="member", description="成員相關指令")

    non_mygo_command_group = member_command_group.create_subgroup(name="non-mygo", description="未領取「迷失之人」身分組相關指令")

    notify_command_group = member_command_group.create_subgroup(name="notify", description="「通知用戶」身分組相關指令")

    def save_member(self):
        utils.write_json(self.logger, RECORD_FILE, {"auto_detect": self.auto_detect})

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = self.bot.get_guild(utils.CRYCHIC_GUILD_ID)

        global NOTIFY_ROLE
        NOTIFY_ROLE = self.guild.get_role(utils.NOTIFY_ROLE_ID)

        global NO_MYGO_ROLE
        NO_MYGO_ROLE = self.guild.get_role(utils.NO_MYGO_ROLE_ID)

        if not self.auto_detect_non_mygo_members.is_running():
            self.auto_detect_non_mygo_members.start()

    async def __get_non_mygo_members(self, guild: discord.Guild) -> List[discord.Member]:
        members = guild.members
        non_mygo_members = [
            member for member in members if not any(role.id == utils.MYGO_ROLE_ID or role.id == utils.BOT_ROLE_ID for role in member.roles)
        ]
        non_mygo_members.sort(key=lambda m: m.joined_at or discord.utils.snowflake_time(m.id))
        return non_mygo_members

    async def __get_mygo_members(self, guild: discord.Guild) -> List[discord.Member]:
        members = guild.members
        mygo_members = [
            member for member in members if any(role.id == utils.MYGO_ROLE_ID or role.id == utils.BOT_ROLE_ID for role in member.roles)
        ]
        mygo_members.sort(key=lambda m: m.joined_at or discord.utils.snowflake_time(m.id))
        return mygo_members

    async def __get_notify_members(self, guild: discord.Guild) -> List[discord.Member]:
        members = guild.members
        notify_members = [member for member in members if NOTIFY_ROLE in member.roles]
        notify_members.sort(key=lambda m: m.joined_at or discord.utils.snowflake_time(m.id))
        return notify_members

    async def __get_no_mygo_members(self, guild: discord.Guild) -> List[discord.Member]:
        members = guild.members
        no_mygo_members = [member for member in members if NO_MYGO_ROLE in member.roles]
        no_mygo_members.sort(key=lambda m: m.joined_at or discord.utils.snowflake_time(m.id))
        return no_mygo_members

    @tasks.loop(minutes=1)
    async def auto_detect_non_mygo_members(self):
        if not self.auto_detect:
            return

        if self.guild is None:
            self.logger.warning("Guild is not set. Cannot auto-detect non-mygo members.")
            return

        try:
            non_mygo_members = await self.__get_non_mygo_members(self.guild)

            for member in non_mygo_members:
                if NO_MYGO_ROLE not in member.roles:
                    try:
                        if NO_MYGO_ROLE is not None:
                            await member.add_roles(NO_MYGO_ROLE, reason="自動偵測未領取「迷失之人」身分組")
                            self.logger.info(f"Added No MyGO role to {member.name}#{member.discriminator} ({member.id})")
                    except Exception as e:
                        self.logger.error(f"為成員 {member.name} 添加通知用戶身分組時發生錯誤：{e}")

            mygo_members = await self.__get_mygo_members(self.guild)
            for member in mygo_members:
                if NO_MYGO_ROLE in member.roles:
                    try:
                        if NO_MYGO_ROLE is not None:
                            await member.remove_roles(NO_MYGO_ROLE, reason="自動偵測已領取「迷失之人」身分組")
                            self.logger.info(f"Removed No MyGO role from {member.name}#{member.discriminator} ({member.id})")
                    except Exception as e:
                        self.logger.error(f"為成員 {member.name} 移除通知用戶身分組時發生錯誤：{e}")
        except Exception as e:
            self.logger.error(f"Error during auto-detection of non-mygo members: {e}")

    @non_mygo_command_group.command(name="list", description="取得所有未領取「迷失之人」身分組的人")
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

    @non_mygo_command_group.command(name="kick", description="踢出未領取「迷失之人」身分組的人")
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

    @non_mygo_command_group.command(
        name="auto-detect", description="開啟或關閉自動偵測未領取「迷失之人」身分組的成員，並將他們加入「未領取必要身份組」身份組"
    )
    async def detect_non_mygo_member(self, ctx: discord.ApplicationContext, toggle: bool):
        if not utils.is_operator(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return

        if ctx.guild is None:
            await ctx.respond("此指令只能在伺服器中使用。", ephemeral=True)
            return

        try:
            if toggle:
                self.auto_detect = True
                self.save_member()
                await ctx.respond("✅ 已啟用自動偵測未領取「迷失之人」身分組的成員功能。")
            else:
                self.auto_detect = False
                self.save_member()
                await ctx.respond("✅ 已停用自動偵測未領取「迷失之人」身分組的成員功能。")
        except Exception as e:
            self.logger.error(f"Error toggling detect_non_mygo_member: {e}")
            await ctx.respond("❌ 發生錯誤，無法更新設定。")

    @notify_command_group.command(name="remove-role", description="移除所有成員的「通知用戶」身分組")
    async def remove_all_notify_role(self, ctx: discord.ApplicationContext):
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return

        if ctx.guild is None:
            await ctx.respond("此指令只能在伺服器中使用。", ephemeral=True)
            return

        try:
            members_with_notify = await self.__get_notify_members(ctx.guild)

            if not members_with_notify:
                await ctx.respond("沒有成員擁有「通知用戶」身分組。")
                return

            removed = []
            for member in members_with_notify:
                try:
                    if NOTIFY_ROLE is not None:
                        await member.remove_roles(NOTIFY_ROLE, reason="移除所有成員的「通知用戶」身分組")
                        removed.append(member)
                except Exception as e:
                    self.logger.error(f"移除成員 {member.name} 的「通知用戶」身分組時發生錯誤：{e}")

            view = RemoveRolePage(self.logger, "通知用戶", removed)

            await ctx.respond(embed=view.get_page_embed(), view=view)
        except Exception as e:
            self.logger.error(f"Error removing all notify roles: {e}")
            await ctx.respond("❌ 發生錯誤，無法執行指令。")

    @non_mygo_command_group.command(name="remove-role", description="移除所有成員的「未領取必要身份組」身分組")
    async def remove_all_no_mygo_role(self, ctx: discord.ApplicationContext):
        if not utils.is_developer(ctx.author):
            await ctx.respond("❌ 你沒有權限使用此指令。", ephemeral=True)
            return

        if ctx.guild is None:
            await ctx.respond("此指令只能在伺服器中使用。", ephemeral=True)
            return

        try:
            members_with_notify = await self.__get_no_mygo_members(ctx.guild)

            if not members_with_notify:
                await ctx.respond("沒有成員擁有「未領取必要身份組」身分組。")
                return

            removed = []
            for member in members_with_notify:
                try:
                    if NO_MYGO_ROLE is not None:
                        await member.remove_roles(NO_MYGO_ROLE, reason="移除所有成員的「未領取必要身份組」身分組")
                        removed.append(member)
                except Exception as e:
                    self.logger.error(f"移除成員 {member.name} 的「未領取必要身份組」身分組時發生錯誤：{e}")

            view = RemoveRolePage(self.logger, "未領取必要身份組", removed)

            await ctx.respond(embed=view.get_page_embed(), view=view)
        except Exception as e:
            self.logger.error(f"Error removing all No MyGO roles: {e}")
            await ctx.respond("❌ 發生錯誤，無法執行指令。")


def setup(bot: commands.Bot):
    bot.add_cog(Member(bot))
