import discord
from discord.ext import commands
from datetime import datetime, timedelta
import utils
import json
import asyncio
import chat_exporter
import io

def open_mc_ticket_config():
    try:
        with open('JSON/mc_tickets.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error reading mc_tickets.json: {e}")
        return {}

def save_mc_ticket_config(config):
    try:
        with open('JSON/mc_tickets.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error writing mc_tickets.json: {e}")

def get_category(bot):
    guild = bot.get_guild(utils.CRYCHIC_GUILD_ID)
    category = discord.utils.get(guild.categories, id=utils.MC_TICKET_ID)
    return category

def overwrite_permissions(user: discord.User, guild: discord.Guild):

    return {
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.get_role(utils.MC_MANAGER_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
}

async def create_ticket_channel(bot, name: str, overwrites: dict):
    category = get_category(bot)
    if not category:
        print("Error: Ticket category not found.")
        return None

    channel = await category.create_text_channel(name, overwrites=overwrites)
    return channel

class MCTicket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.logger = utils.get_logger(__name__)
        self.logger.info("cog/mc_ticket.py: 日誌系統初始化完成")

    class MachineApplyModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="申請 Minecraft 伺服器機器")
            self.add_item(discord.ui.InputText(label="機器名稱", placeholder="請輸入機器名稱"))
            self.add_item(discord.ui.InputText(label="尺寸", style=discord.InputTextStyle.short, placeholder="請描述機器尺寸 ex: 16*32*16"))
            self.add_item(discord.ui.InputText(label="地點", style=discord.InputTextStyle.short, placeholder="請描述您申請此機器的地點"))

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)

            overwrites = overwrite_permissions(interaction.user, interaction.guild)

            tickets = open_mc_ticket_config()
            if "machine_tickets" not in tickets:
                tickets["machine_tickets"] = 0
            channel_name = f"機器申請-{(tickets['machine_tickets'] + 1):04d}"
            channel = await create_ticket_channel(interaction.client, channel_name, overwrites)
            tickets["machine_tickets"] += 1
            save_mc_ticket_config(tickets)

            embed = discord.Embed(title="機器申請", color=0x00ff00)
            embed.add_field(name="機器名稱", value=self.children[0].value, inline=False)
            embed.add_field(name="尺寸", value=f"```{self.children[1].value}```", inline=False)
            embed.add_field(name="地點", value=f"```{self.children[2].value}```", inline=False)
            await channel.send(content = f"{interaction.user.mention} <@&{utils.MC_MANAGER_ROLE_ID}>", embed=embed)

            await interaction.followup.send("您的申請已提交，請稍候審核。", ephemeral=True)
    
    class TerritoryExpandModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="申請領地增建/擴張")
            self.add_item(discord.ui.InputText(label="增建/擴張理由", style=discord.InputTextStyle.paragraph, placeholder="請描述您想要增建或擴張的理由"))

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            
            overwrites = overwrite_permissions(interaction.user, interaction.guild)
            
            tickets = open_mc_ticket_config()
            if "territory_tickets" not in tickets:
                tickets["territory_tickets"] = 0
            channel_name = f"領地增建-{(tickets['territory_tickets'] + 1):04d}"
            channel = await create_ticket_channel(interaction.client, channel_name, overwrites)
            tickets["territory_tickets"] += 1
            save_mc_ticket_config(tickets)
            
            embed = discord.Embed(title="領地增建/擴張申請", color=0x0000ff)
            embed.add_field(name="申請理由", value=self.children[0].value, inline=False)
            await channel.send(content = f"{interaction.user.mention} <@&{utils.MC_MANAGER_ROLE_ID}>", embed=embed)
            
            await interaction.followup.send("您的領地增建/擴張申請已提交，請稍候審核。", ephemeral=True)
    
    class ReportPlayerModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="檢舉玩家")
            self.add_item(discord.ui.InputText(label="被檢舉玩家名稱", placeholder="請輸入被檢舉玩家的 Minecraft 名稱", style=discord.InputTextStyle.short))
            self.add_item(discord.ui.InputText(label="檢舉理由", style=discord.InputTextStyle.paragraph, placeholder="請描述您檢舉該玩家的理由"))
    
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            
            overwrites = overwrite_permissions(interaction.user, interaction.guild)
            
            tickets = open_mc_ticket_config()
            if "report_tickets" not in tickets:
                tickets["report_tickets"] = 0
            channel_name = f"玩家檢舉-{(tickets['report_tickets'] + 1):04d}"
            channel = await create_ticket_channel(interaction.client, channel_name, overwrites)
            tickets["report_tickets"] += 1
            save_mc_ticket_config(tickets)
            
            embed = discord.Embed(title="玩家檢舉", color=0xff0000)
            embed.add_field(name="被檢舉玩家名稱", value=self.children[0].value, inline=False)
            embed.add_field(name="檢舉理由", value=self.children[1].value, inline=False)
            await channel.send(content = f"{interaction.user.mention} <@&{utils.MC_MANAGER_ROLE_ID}>", embed=embed)

            await interaction.followup.send("您的檢舉已提交，請稍候審核。", ephemeral=True)

    class DummySetupModal(discord.ui.Modal):
        def __init__(self):
            super().__init__(title="假人設置申請")
            self.add_item(discord.ui.InputText(label="假人設置指令", placeholder="請輸入假人設置的指令", style=discord.InputTextStyle.short))
            self.add_item(discord.ui.InputText(label="設置座標", placeholder="請輸入假人座標", style=discord.InputTextStyle.short))
            self.add_item(discord.ui.InputText(label="設置理由", style=discord.InputTextStyle.paragraph, placeholder="請描述您設置假人的理由"))
    
        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            
            overwrites = overwrite_permissions(interaction.user, interaction.guild)
            
            tickets = open_mc_ticket_config()
            if "dummy_tickets" not in tickets:
                tickets["dummy_tickets"] = 0
            channel_name = f"假人設置-{(tickets['dummy_tickets'] + 1):04d}"
            channel = await create_ticket_channel(interaction.client, channel_name, overwrites)
            tickets["dummy_tickets"] += 1
            save_mc_ticket_config(tickets)
            
            embed = discord.Embed(title="假人設置申請", color=0x00ffff)
            embed.add_field(name="假人設置指令", value=self.children[0].value, inline=False)
            embed.add_field(name="設置座標", value=self.children[1].value, inline=False)
            embed.add_field(name="設置理由", value=self.children[2].value, inline=False)
            await channel.send(content = f"{interaction.user.mention} <@&{utils.MC_MANAGER_ROLE_ID}>", embed=embed)

            await interaction.followup.send("您的假人設置申請已提交，請稍候審核。", ephemeral=True)

    class TicketButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
        
        @discord.ui.button(label="機器申請", style=discord.ButtonStyle.primary, custom_id="mc_ticket:apply")
        async def machine_apply(self, button: discord.ui.Button, interaction: discord.Interaction):
            modal = MCTicket.MachineApplyModal()
            await interaction.response.send_modal(modal)
        
        @discord.ui.button(label="領地增建/擴張", style=discord.ButtonStyle.secondary, custom_id="mc_ticket:territory_expand")
        async def territory_expand(self, button: discord.ui.Button, interaction: discord.Interaction):
            modal = MCTicket.TerritoryExpandModal()
            await interaction.response.send_modal(modal)

        @discord.ui.button(label="假人設置", style=discord.ButtonStyle.green, custom_id="mc_ticket:dummy_setup")
        async def dummy_setup(self, button: discord.ui.Button, interaction: discord.Interaction):
            modal = MCTicket.DummySetupModal()
            await interaction.response.send_modal(modal)

        @discord.ui.button(label="檢舉玩家", style=discord.ButtonStyle.danger, custom_id="mc_ticket:report_player")
        async def report_player(self, button: discord.ui.Button, interaction: discord.Interaction):
            modal = MCTicket.ReportPlayerModal()
            await interaction.response.send_modal(modal)

    class CloseConfirmation(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.value = None

        @discord.ui.button(label="確認關閉", style=discord.ButtonStyle.danger)
        async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
            log_channel = interaction.guild.get_channel(utils.MC_TICKET_HISTORY_CHANNEL_ID)
            transcript = await chat_exporter.export(interaction.channel, limit=None, tz_info="Asia/Taipei")
            if log_channel is not None and transcript is not None:
                file = discord.File(io.BytesIO(transcript.encode()), filename=f"{interaction.channel.name}.html")
                await log_channel.send(file=file)
                
                await interaction.response.send_message("工單將在 5 秒後關閉。", ephemeral=True)
                await interaction.message.delete()
                await asyncio.sleep(5)
                await interaction.channel.delete()
                
            else:
                await interaction.response.send_message("無法導出工單紀錄。", ephemeral=True)

        @discord.ui.button(label="取消", style=discord.ButtonStyle.secondary)
        async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
            await interaction.message.delete()
            await interaction.response.send_message("已取消關閉工單。", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(self.TicketButton())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not utils.is_operator(message.author):
            return
        if message.content == '!mcticket':
            view = MCTicket.TicketButton()
            embed = discord.Embed(title="Minecraft 伺服器工單系統", description="請選擇您想要申請的工單類型：", color=0x00ff00)
            await message.channel.send(embed=embed, view=view)

        if message.content == '!ticketclose':
            if message.channel.category and message.channel.category.id == utils.MC_TICKET_ID:
                view = MCTicket.CloseConfirmation()
                embed = discord.Embed(title="關閉工單確認", description="您確定要關閉此工單嗎？關閉後將無法恢復。", color=0xff0000)
                await message.delete()
                await message.channel.send(embed=embed, view=view)
            else:
                await message.channel.send("❌ 此指令只能在 Minecraft 伺服器工單頻道中使用。", delete_after=10)

def setup(bot: commands.Bot):
    bot.add_cog(MCTicket(bot))