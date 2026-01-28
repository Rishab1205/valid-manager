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
from openai import OpenAI

import aiohttp

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
    embed.add_field(name="How to Join", value="[Open Membership Page](https://youtube.com/@officialvalidgaming/join)", inline=False)
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

# ================= AI CLIENT =================
import os

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

AI_MODEL = "openai/gpt-4o-mini"  # best available free model

# ================= AI CHAT CONFIG =================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

ALLOWED_AI_CHANNELS = {
    1214601102100791346,   # channel-1
    1457708857777197066    # channel-2
}

async def ask_ai(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an assistant. Call the user 'sir'. Keep replies helpful and clear."},
            {"role": "user", "content": prompt}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except:
                return "Sorry sir, AI service is not responding."

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

    if not category:
        print("[ERROR] Ticket category missing.")
        return None

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
    await asyncio.sleep(1)  # delay for Discord DM handshake
    try:
        embed = discord.Embed(
            title="🎉 Payment Confirmed!",
            description=f"Hey **{member.name}** 👋\nYour purchase was successful!",
            color=0x2ECC71
        )
        embed.add_field(name="📁 Ticket", value=f"{ticket_channel.mention}", inline=False)
        embed.add_field(name="💳 Next Step", value=f"Upload screenshot in <#{PAYOUT_CHANNEL_ID}>", inline=False)
        embed.set_footer(text="✨ Thanks for choosing FINEST — Performance is personal")
        await member.send(embed=embed)
    except Exception as e:
        print("[DM-ERROR] Payment DM:", e)

# ================= ROLE + ACCESS LOGIC =================
async def process_member(member):
    row_index, header, row = find_user_row(str(member.id))
    if not row_index:
        print(f"[PROCESS] User {member} not found in sheet.")
        return None

    guild = member.guild
    data = dict(zip(header, row))
    status = data.get("Status", "").upper()

    # assign paid role if exists
    member_role = guild.get_role(MEMBER_ROLE_ID)
    if status == "PAID" and member_role:
        try:
            await member.add_roles(member_role)
        except:
            print("[ROLE ERROR] Failed to assign paid role.")

    # update sheet that role assigned
    update_role_assigned(row_index)

    # ticket for paid users only
    if status == "PAID":
        ticket = await create_ticket(member, header, row)
        if ticket:
            await send_payment_dm(member, ticket)
            return ticket

    return None

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

    # free pack system untouched
    if str(member.id) in freeClaimUsers:
        data = freeClaimUsers[str(member.id)]
        try:
            async with aiohttp.ClientSession() as session:
                await session.post("http://localhost:3000/freepack-unlock", json={"discord_id": str(member.id)})
        except Exception as e:
            print("[FREEPACK ERROR] Backend unlock failed:", e)
        try:
            await member.send(f"🎁 **Free Pack Unlocked!**\nHere is your download link:\n{data['drive']}")
        except:
            pass
        freeClaimUsers.pop(str(member.id), None)

    # ⭐ ALWAYS PROCESS MEMBERS (PAID LOGIC)
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

# ================= SLASH COMMANDS =================
@tree.command(name="ticket", description="Open a support ticket")
async def ticket_cmd(interaction: Interaction):
    member = interaction.user
    guild = interaction.guild
    for c in guild.text_channels:
        if c.name == f"ticket-{member.name}":
            return await interaction.response.send_message(
                "⚠️ You already have an open ticket.", ephemeral=True
            )
    await interaction.response.send_modal(TicketModal(member))

@tree.command(name="price", description="View product / membership pricing")
async def price_cmd(interaction: Interaction):
    await interaction.response.send_message(embed=membership_embed())

@tree.command(name="uptime", description="Show bot uptime")
async def uptime_cmd(interaction: Interaction):
    delta = datetime.datetime.utcnow() - start_time
    await interaction.response.send_message(f"⏳ Bot Uptime: `{delta}`")

@tree.command(name="refresh", description="Sync your purchase & unlock access")
async def refresh_cmd(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)
    member = interaction.user
    await process_member(member)
    await interaction.followup.send(
        "🔄 Sync complete! Check your DMs.\nIf no ticket, use `/ticket`.", ephemeral=True
    )
    
@tree.command(name="askai", description="Ask AI anything sir.")
async def askai_cmd(interaction: Interaction, *, question: str):
    await interaction.response.defer()
    reply = await ask_ai(question)
    await interaction.followup.send(reply)

    AI_CHANNELS = [1214601102100791346, 1457708857777197066]
    FINEST_ROLE_ID = 1463993521827483751

    # Channel check
    if channel.id not in AI_CHANNELS:
        return await interaction.response.send_message(
            "Sir, please use this command inside the AI channels.",
            ephemeral=True
        )

    await interaction.response.defer()

    # Role check
    is_member = any(r.id == FINEST_ROLE_ID for r in user.roles)

    # Prompt building
    base_prompt = f"You must call the user 'Sir' in your replies. User asked: {query}"

    if is_member:
        # Finest mode: long detailed
        ai_prompt = base_prompt + "\nProvide a deep, detailed, long answer.\n"
        max_tokens = 900
    else:
        # Free mode: short with upsell
        ai_prompt = base_prompt + "\nAnswer briefly in 3-5 lines.\n"
        max_tokens = 250

    # AI Request
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": ai_prompt}],
                    "max_tokens": max_tokens
                }
            ) as resp:
                data = await resp.json()

                if "choices" not in data:
                    return await interaction.followup.send("Sir, AI service is offline, try again later.")

                reply = data["choices"][0]["message"]["content"]

                # Add upsell for free users
                if not is_member:
                    reply += "\n\n⚡ For full-length responses, deep tech answers & performance tweaks, upgrade to **Finest Membership**, Sir."

                await interaction.followup.send(reply)

    except Exception as e:
        print("[AI ERROR]", e)
        await interaction.followup.send("Sir, AI system hit a snag — try again shortly.")


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
    embed.add_field(name="/close", value="Close a ticket (Staff Only)", inline=False)
    embed.set_footer(text="Finest Manager — Performance is personal")
    await interaction.response.send_message(embed=embed)

# ================= CLOSE COMMAND =================
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

# ================= MESSAGE COMMANDS =================
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot online.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # allow ! commands to work
    await bot.process_commands(message)

    # only reply in allowed channels
    if message.channel.id not in ALLOWED_AI_CHANNELS:
        return

    # generate AI reply
    reply = await ask_ai(message.content)
    await message.channel.send(reply)

#================== AUTO ROLE ON VOICE CHANNEL =================
@bot.event
async def on_voice_state_update(member, before, after):
    ROLE_ID = 1214573354582024204
    role = member.guild.get_role(ROLE_ID)
    if not role:
        print(f"[VOICE-ROLE] Role {ROLE_ID} not found!")
        return

    if before.channel is None and after.channel is not None:
        if role not in member.roles:
            try:
                await member.add_roles(role, reason="Joined voice channel")
            except Exception as e:
                print("[VOICE-ROLE ERROR] Add:", e)

    if before.channel is not None and after.channel is None:
        if role in member.roles:
            try:
                await member.remove_roles(role, reason="Left voice channel")
            except Exception as e:
                print("[VOICE-ROLE ERROR] Remove:", e)

# ================= START =================
keep_alive()
bot.run(TOKEN)
