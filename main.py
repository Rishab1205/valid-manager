# ================= KEEP ALIVE =================
from flask import Flask
from threading import Thread
import os, time, asyncio, datetime
from collections import deque

app = Flask('')
@app.route('/')
def home(): return "Valid Manager running!"
def run_web(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_web).start()

# ================= DISCORD =================
import discord
from discord.ext import commands, tasks
from discord import app_commands, ui, Interaction, ButtonStyle

from sheet import find_user_row, update_role_assigned

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))
MEMBER_ROLE_ID = int(os.getenv("DISCORD_MEMBER_ROLE_ID"))
STAFF_ROLE_ID = int(os.getenv("DISCORD_STAFF_ROLE_ID"))
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))
ARCHIVE_CATEGORY_ID = int(os.getenv("ARCHIVE_CATEGORY_ID"))
PAYOUT_CHANNEL_ID = int(os.getenv("PAYOUT_CHANNEL_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
STAFF_LOGIC = os.getenv("STAFF_LOGIC", "B")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

start_time = datetime.datetime.utcnow()

# ================= RAID DETECTION =================
RAID_JOIN_LIMIT = 5
RAID_TIME_WINDOW = 10
LOCK_DURATION = 300
join_tracker = deque()
server_locked = False

# ================= MEMBERSHIP EMBED =================
def membership_embed():
    embed = discord.Embed(
        title="💎 OFFICIAL VALID GAMING – YT MEMBERSHIP",
        description="Support the channel & unlock exclusive perks 🔥",
        color=0x2f3136
    )
    embed.add_field(name="🥇 GOLD – ₹59", value="• Custom Badges", inline=False)
    embed.add_field(name="🥈 PLATINUM – ₹119", value="• Shorts Access", inline=False)
    embed.add_field(name="💠 DIAMOND – ₹179", value="• FR + Shout-outs", inline=False)
    embed.add_field(name="🎯 Join Now", value="[Click](https://youtube.com/@officialvalidgaming/join)", inline=False)
    embed.set_footer(text="VALID GAMING • Membership")
    return embed

# ================= STAFF CLAIM BUTTON =================
class ClaimButton(ui.View):
    def __init__(self, member, sheet_row):
        super().__init__(timeout=None)
        self.member = member
        self.sheet_row = sheet_row

    @ui.button(label="Claim Ticket", style=ButtonStyle.blurple)
    async def claim(self, interaction: Interaction, button: ui.Button):
        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)

        await interaction.channel.set_permissions(interaction.user,
            view_channel=True, send_messages=True, attach_files=True)

        await interaction.response.send_message(f"👑 {interaction.user.mention} claimed this ticket.")

        log = bot.get_channel(LOG_CHANNEL_ID)
        if log: await log.send(f"📌 Ticket claimed by {interaction.user.mention} for `{self.member.name}`")


# ================= TICKET CREATION =================
async def create_ticket(member: discord.Member, header, row):

    guild = member.guild
    category = guild.get_channel(TICKET_CATEGORY_ID)
    log = bot.get_channel(LOG_CHANNEL_ID)

    # build map: {header: value}
    data = dict(zip(header, row))

    ticket = await guild.create_text_channel(
        name=f"ticket-{member.name}",
        category=category,
        overwrites={
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)
        }
    )

    staff_role = guild.get_role(STAFF_ROLE_ID)
    if staff_role:
        await ticket.set_permissions(staff_role, view_channel=True, send_messages=True, attach_files=True)

    desc = f"""
🎫 **Support Activated**

📌 **Next steps**
• Wait for a staff member to **claim** your ticket  
• Once claimed, they will guide you

📤 **Payment Verification**
Upload your screenshot → <#{PAYOUT_CHANNEL_ID}>

🗂 **Purchase Details**
• Name: `{data.get('Name','N/A')}`
• Product: `{data.get('Product','N/A')}`
• Payment ID: `{data.get('Payment ID','N/A')}`
• Status: `{data.get('Status','N/A')}`

✨ Finest Support • Zero friction, just service.
"""

    embed = discord.Embed(title="Welcome to Support", description=desc, color=0x2b2d31)
    await ticket.send(embed=embed, view=ClaimButton(member, row))

    if log: await log.send(f"📂 Ticket created for {member.name} → {ticket.mention}")

# ================= ROLE + TICKET LOGIC =================
async def process_member(member):

    row_index, header, row = find_user_row(str(member.id))
    if not row_index:
        print("[SHEET] No match for", member.name)
        return

    guild = member.guild
    member_role = guild.get_role(MEMBER_ROLE_ID)
    staff_role = guild.get_role(STAFF_ROLE_ID)

    data = dict(zip(header, row))
    staff_value = data.get("Staff", "NONE").upper()

    if member_role:
        await member.add_roles(member_role)
        print("MEMBER role assigned")

    if STAFF_LOGIC == "B" and staff_value != "NONE" and staff_role:
        await member.add_roles(staff_role)
        print("STAFF role assigned")

    update_role_assigned(row_index)
    print("RoleAssigned updated")

    await create_ticket(member, header, row)

# ================= EVENTS =================
@bot.event
async def on_member_join(member):
    now = time.time()
    join_tracker.append(now)
    while join_tracker and now - join_tracker[0] > RAID_TIME_WINDOW:
        join_tracker.popleft()

    if len(join_tracker) >= RAID_JOIN_LIMIT:
        print("RAID DETECTED")
        await lock_server(member.guild)

    await process_member(member)

# ================= RAID =================
async def lock_server(guild):
    global server_locked
    if server_locked: return
    server_locked = True

    everyone = guild.default_role
    for c in guild.text_channels:
        await c.set_permissions(everyone, send_messages=False)

    await asyncio.sleep(LOCK_DURATION)

    for c in guild.text_channels:
        await c.set_permissions(everyone, send_messages=True)

    server_locked = False

# ================= SLASH CMDS =================
@tree.command(name="uptime", description="Bot uptime")
async def uptime(interaction: Interaction):
    delta = datetime.datetime.utcnow() - start_time
    await interaction.response.send_message(f"⏳ `{delta}`")

@tree.command(name="price", description="Show membership prices")
async def price(interaction: Interaction):
    await interaction.response.send_message(embed=membership_embed())

@bot.command()
async def ping(ctx): await ctx.send("🏓 Pong!")
    
from discord.app_commands import MissingPermissions

@tree.command(name="close", description="Close this ticket")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def close(interaction: Interaction):
    guild = interaction.guild
    channel = interaction.channel
    member = None

    # Identify ticket owner by parsing name
    if channel.name.startswith("ticket-"):
        name = channel.name.replace("ticket-", "")
        for m in guild.members:
            if m.name.lower() == name.lower():
                member = m
                break

    archive = guild.get_channel(ARCHIVE_CATEGORY_ID)
    log_channel = guild.get_channel(LOG_CHANNEL_ID)

    if not archive:
        return await interaction.response.send_message("❌ Archive category missing.", ephemeral=True)

    # Move channel to archive
    await channel.edit(category=archive)

    # Remove member access, keep staff access
    for overwrite_target, overwrite in channel.overwrites.items():
        if isinstance(overwrite_target, discord.Member):
            await channel.set_permissions(overwrite_target, view_channel=False)
        if isinstance(overwrite_target, discord.Role) and overwrite_target.id == STAFF_ROLE_ID:
            await channel.set_permissions(overwrite_target, view_channel=True)

    await interaction.response.send_message("📁 Ticket archived.", ephemeral=True)

    # DM user summary
    if member:
        try:
            dm_embed = discord.Embed(
                title="🎫 Ticket Closed",
                description="Your support ticket has been closed.\nIf you need help again, just open a new one!",
                color=0x5865F2
            )
            await member.send(embed=dm_embed)
        except:
            pass

    # Log it
    if log_channel:
        await log_channel.send(
            f"📂 **Ticket archived** by {interaction.user.mention}\n"
            f"🧾 Channel: `{channel.name}`\n"
            f"👤 User: `{member.name if member else 'Unknown'}`"
        )


@close.error
async def close_error(interaction: Interaction, error):
    if isinstance(error, MissingPermissions):
        await interaction.response.send_message("❌ Staff only command.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ Something went wrong.", ephemeral=True)

# ================= START =================
keep_alive()
bot.run(TOKEN)

