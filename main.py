# ================= KEEP ALIVE =================
from flask import Flask
from threading import Thread
import os, time, asyncio, datetime
from collections import deque

# ================= FREE PACK STORAGE =================
freeClaimUsers = {}

app = Flask('')
@app.route('/')
def home(): return "Valid Manager running!"
def run_web(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_web).start()

# ================= DISCORD =================
import discord
from discord.ext import commands, tasks
from discord import app_commands, ui, Interaction, ButtonStyle
from discord.ui import Modal, TextInput
from discord.app_commands import MissingPermissions

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
PAYMODE = "B"
STATUS_FIELD = "Status"

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

# ================= PRICE EMBED =================
def membership_embed():
    embed = discord.Embed(
        title="💎 VALID GAMING — YT MEMBERSHIP",
        description=(
            "Support the channel & unlock exclusive perks 🛠️\n"
            "Memberships are processed via **YouTube** and auto-sync to Discord.\n\n"
            "**Available Tiers:**\n"
        ),
        color=0x2B2D31
    )

    embed.add_field(name="🧈  GOLD — RS 59 / Month", value="• Custom member **Badges**", inline=False)
    embed.add_field(name="💷 PLATINUM — RS 119 / Month", value="• Member-only **Shorts**", inline=False)
    embed.add_field(name="💠 DIAMOND — RS 179 / Month", value="• **Friend Request** + **Shout-out**", inline=False)

    embed.add_field(
        name="How to Join",
        value="[Open Membership Page](https://youtube.com/@officialvalidgaming/join)",
        inline=False
    )

    embed.add_field(
        name="🔗  Role Sync Instructions",
        value=(
            "1. Link **YouTube → Discord** in User Settings\n"
            "2. Go to `Connections`\n"
            "3. Link Google account\n"
            "4. Join server from YouTube Membership tab\n"
            "5. Roles auto-sync\n"
        ),
        inline=False
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1166295699290333194/1457814947756249262/1b2d8db2-332e-42ce-80c5-54d946086c95.png")
    embed.set_image(url="https://cdn.discordapp.com/attachments/1166295699290333194/1457812767846301779/Colorful_Abstract_Aesthetic_Linkedin_Banner.png")
    embed.set_footer(text="VALID GAMING • Official Membership")
    return embed

# ================= STAFF CLAIM BUTTON =================
class ClaimButton(ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.member = member

    @ui.button(label="Claim Ticket", style=ButtonStyle.blurple)
    async def claim(self, interaction: Interaction, button: ui.Button):
        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Staff only.", ephemeral=True)

        await interaction.channel.set_permissions(
            interaction.user,
            view_channel=True, send_messages=True, attach_files=True
        )
        await interaction.response.send_message(f"👮🏻‍♂️ {interaction.user.mention} claimed this ticket.")

        log = bot.get_channel(LOG_CHANNEL_ID)
        if log: await log.send(f"📌 Ticket claimed by {interaction.user.mention} for `{self.member.name}`")

# ================= TICKET MODAL =================
class TicketModal(Modal, title="Open Support Ticket"):
    reason = TextInput(
        label="What do you need help with?",
        placeholder="Example: payment issue, tool help, verification...",
        style=discord.TextStyle.long,
        required=True,
        max_length=300
    )

    def __init__(self, member):
        super().__init__()
        self.member = member

    async def on_submit(self, interaction: Interaction):
        header = ["Name", "Product", "Payment ID", "Status", "Reason"]
        row = [self.member.name, "MANUAL", "N/A", "OPEN", str(self.reason)]

        await interaction.response.send_message("🎫 Ticket created!", ephemeral=True)
        await create_ticket(self.member, header, row)

# ================= TICKET CREATION =================
async def create_ticket(member: discord.Member, header, row):
    guild = member.guild
    category = guild.get_channel(TICKET_CATEGORY_ID)
    log = bot.get_channel(LOG_CHANNEL_ID)

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
• Wait for staff to **claim** your ticket  
• They will guide you end-to-end

📤 **Payment Verification**
Upload your screenshot → <#{PAYOUT_CHANNEL_ID}>

🗂 **Purchase Details**
• Name: `{data.get('Name','N/A')}`
• Product: `{data.get('Product','N/A')}`
• Payment ID: `{'HIDDEN' if PAYMODE=='B' else data.get('Payment ID','N/A')}`
• Status: `{data.get('Status','N/A')}`

✨ Finest Support — Zero friction.
"""
    await ticket.send(
        embed=discord.Embed(title="Welcome to Support", description=desc, color=0x2B2D31),
        view=ClaimButton(member)
    )

    if staff_role:
        await ticket.send(f"🔔 **Staff Notice:** {staff_role.mention} please assist this user.")

    if log:
        await log.send(f"📂 Ticket created for {member.name} → {ticket.mention}")

    return ticket

# ================= PAYMENT DM (ADDED) =================
async def send_payment_dm(member, ticket_channel):
    try:
        embed = discord.Embed(
            title="🎉 Payment Confirmed!",
            description=f"Hey **{member.name}** 👋\nYour purchase was successful!",
            color=0x2ECC71
        )

        embed.add_field(
            name="📁 Ticket",
            value=f"{ticket_channel.mention}",
            inline=False
        )

        embed.add_field(
            name="💳 Next Step",
            value=f"Upload your payment screenshot in → <#{PAYOUT_CHANNEL_ID}>",
            inline=False
        )

        embed.set_footer(text="✨ Thanks for choosing FINEST — Performance is personal")

        await member.send(embed=embed)

    except Exception as e:
        print("[DM-ERROR] Payment DM:", e)

# ================= ROLE LOGIC =================
async def process_member(member):
    row_index, header, row = find_user_row(str(member.id))
    if not row_index: return

    guild = member.guild
    member_role = guild.get_role(MEMBER_ROLE_ID)
    staff_role = guild.get_role(STAFF_ROLE_ID)

    data = dict(zip(header, row))
    staff_value = data.get("Staff", "NONE").upper()

    if member_role: await member.add_roles(member_role)
    if STAFF_LOGIC == "B" and staff_value != "NONE" and staff_role:
        await member.add_roles(staff_role)

    update_role_assigned(row_index)
    ticket = await create_ticket(member, header, row)

    status = data.get("Status", "").upper()
    if status == "PAID":
        await send_payment_dm(member, ticket)

# ================= ONBOARDING DM =================
async def send_join_dm(member):
    try:
        embed = discord.Embed(
            title="👋 Welcome to VALID DC",
            description=(
                f"Hey **{member.name}**, welcome aboard! 🎭\n\n"
                "You're now part of a community built for gamers who respect:\n"
                "• Performance\n"
                "• Discipline\n"
                "• Clean gameplay\n\n"
                "**Useful Areas**\n"
                "🏷️ Main Chat — `#chat`\n"
                "⚙ Support — Open ticket anytime\n\n"
                "**Rules & Conduct**\n"
                "• Respect everyone\n"
                "• No spam or self-promo\n"
                "• No scams or shady links\n"
                "• Follow Discord TOS\n\n"
                "If you ever need help — staff are one ticket away ❤️"
            ),
            color=0x2B2D31
        )
        embed.set_footer(text="VALID DC • Established for serious players")
        await member.send(embed=embed)
    except Exception as e:
        print("[DM-ERROR] Onboarding DM:", e)

# ================= EVENTS =================
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online 🚀")
    update_status.start()
    
    for guild in bot.guilds:
        try:
            await tree.sync(guild=discord.Object(id=GUILD_ID))
            print(f"🔗 Synced slash commands to → {guild.name}")
        except Exception as e:
            print(f"❌ Sync failed for {guild.name}: {e}")

@bot.event
async def on_member_join(member):
    now = time.time()
    join_tracker.append(now)

    while join_tracker and now - join_tracker[0] > RAID_TIME_WINDOW:
        join_tracker.popleft()

    if len(join_tracker) >= RAID_JOIN_LIMIT:
        await lock_server(member.guild)

    await send_join_dm(member)

    # >>> 🔥 FREE PACK AUTO-UNLOCK LOGIC (BACKEND VERSION) <<<
import aiohttp
try:
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:3000/freepack-unlock",
            json={ "discord_id": str(member.id) }) as r:
            
            unlock_data = await r.json()

            if unlock_data.get("unlock"):
                try:
                    await member.send(f"🎁 **Free Pack Unlocked!**\nHere is your download link:\n{unlock_data['drive']}")
                except:
                    pass
                print(f"[FREEPACK] Delivered to {member.name}")
except Exception as e:
    print("[FREEPACK-ERROR]", e)


        # notify backend to unlock browser polling
        import aiohttp
        async with aiohttp.ClientSession() as session:
            await session.post("http://localhost:3000/freepack-unlock", json={
                "discord_id": str(member.id)
            })

        # remove from memory
        freeClaimUsers.pop(str(member.id), None)

    await process_member(member)


# ================= PRESENCE =================
@tasks.loop(minutes=2)
async def update_status():
    if not bot.guilds: return
    guild = bot.guilds[0]
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{guild.member_count} users | Valid Subs"
        )
    )

# ================= LOCK SERVER =================
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

# ================= SYNC COMMAND =================
@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"Globally synced {len(synced)} commands")
    
# ================= /ticket COMMAND =================
@tree.command(name="ticket", description="Open a support ticket")
async def ticket_cmd(interaction: Interaction):
    member = interaction.user
    guild = interaction.guild

    for c in guild.text_channels:
        if c.name == f"ticket-{member.name}":
            return await interaction.response.send_message(
                "⚠️ You already have an open ticket.",
                ephemeral=True
            )

    await interaction.response.send_modal(TicketModal(member))


# ================= /price COMMAND =================
@tree.command(name="price", description="View product / membership pricing")
async def price_cmd(interaction: Interaction):
    await interaction.response.send_message(embed=membership_embed())


# ================= /uptime COMMAND =================
@tree.command(name="uptime", description="Show bot uptime")
async def uptime_cmd(interaction: Interaction):
    delta = datetime.datetime.utcnow() - start_time
    await interaction.response.send_message(f"⏳ Bot Uptime: `{delta}`")


# ================= /help COMMAND =================
@tree.command(name="help", description="Show bot commands & usage")
async def help_cmd(interaction: Interaction):
    embed = discord.Embed(
        title="🧾 Finest Manager — Commands",
        description="Here are my available commands:",
        color=0x2B2D31
    )

    embed.add_field(name="/ticket", value="Open a support ticket", inline=False)
    embed.add_field(name="/price", value="View product pricing / membership", inline=False)
    embed.add_field(name="/uptime", value="Show bot uptime", inline=False)
    embed.add_field(name="/help", value="Show this help message", inline=False)
    embed.add_field(name="/close", value="Close your current ticket (Staff Only)", inline=False)

    embed.set_footer(text="Finest Manager — Performance is personal")
    await interaction.response.send_message(embed=embed)


# ================= /close COMMAND =================
@tree.command(name="close", description="Close this ticket (staff only)")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def close_cmd(interaction: Interaction):
    guild = interaction.guild
    channel = interaction.channel
    member = None

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

    await channel.edit(category=archive)

    for target in list(channel.overwrites):
        if isinstance(target, discord.Member):
            await channel.set_permissions(target, view_channel=False)
        if isinstance(target, discord.Role) and target.id == STAFF_ROLE_ID:
            await channel.set_permissions(target, view_channel=True)

    await interaction.response.send_message("📁 Ticket archived.", ephemeral=True)

    if member:
        try:
            dm = discord.Embed(
                title="🎫 Ticket Closed",
                description=(
                    "Your support ticket has been closed.\n\n"
                    "❤️ **Thank you for choosing Finest Store** ❤️\n"
                    "_Performance is personal._\n\n"
                    "If you ever need anything — open a new ticket!"
                ),
                color=0x2B2D31
            )
            await member.send(embed=dm)
        except Exception as e:
            print("[DM-ERROR] Ticket close DM:", e)

    if log_channel:
        await log_channel.send(
            f"📂 **Ticket archived** by {interaction.user.mention}\n"
            f"🧾 Channel: `{channel.name}`\n"
            f"👤 User: `{member.name if member else 'Unknown'}`"
        )


@close_cmd.error
async def close_cmd_error(interaction: Interaction, error):
    if isinstance(error, MissingPermissions):
        await interaction.response.send_message("❌ Staff only.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ Something went wrong.", ephemeral=True)


# ================= START =================
keep_alive()
bot.run(TOKEN)
