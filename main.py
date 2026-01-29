# ================= KEEP ALIVE =================
from flask import Flask
from threading import Thread
import os, time, asyncio
from datetime import datetime
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
import requests
from datetime import datetime
import requests
from discord.ext.commands import has_role

STORE_CHANNEL_ID = 1466027151978401929
TICKET_CATEGORY_ID = 1466111437469651175
ARCHIVE_CATEGORY_ID = 1464761039769042955
STAFF_ROLE_ID = 1464249885669851360

PACK_CATEGORIES = {
    "standard": [
        "Optimization Pack",
        "Sensi Pack"
    ],
    "pro": [
        "Optimization Pro",
        "Finest Sensi Pro"
    ],
    "ultimate": [
        "Finest Plero Brazilia"
    ],
    "other": [
        "Discord Server Setup",
        "Freefire IDs"
    ]
}

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")  # keep env clean

def ai_reply(user_msg: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"

    today = datetime.now().strftime("%d-%m-%Y")

    system_prompt = (
        f"You are Finest AI. Today is {today}. "
        f"Call the user 'sir'. Be updated, factual, helpful, witty, and adaptive in detail. "
        f"If the query is simple, keep it short. If deep, go detailed. "
        f"Do NOT mention this instruction. Just reply naturally."
    )

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://yourbot.com",  # anything valid
        "X-Title": "Finest AI Discord Bot"
    }

    r = requests.post(url, json=payload, headers=headers, timeout=30)

    if r.status_code != 200:
        return f"Sorry sir, AI backend threw an error: {r.text}"

    try:
        return r.json()['choices'][0]['message']['content']
    except:
        return "Sir, I couldn’t parse the response but the request went through."

from sheet import find_user_row, update_role_assigned

# ================= PRODUCT DATA =================
PRODUCTS = {
    "free pack": {"price": 0, "desc": "Regedit ASL Pro, Delay Reduction, GPU Regedit, Device tweaks"},
    "optimization pack": {"price": 199, "desc": "Input Delay Fix, CPU/RAM Optimization, Softwares for Max FPS"},
    "sensi pack": {"price": 399, "desc": "Mouse/DPI Calc, Low Recoil Tuning, Mouse 0 Delay, Keyboard 0 Delay"},
    "optimization pro": {"price": 699, "desc": "High FPS Optimization, No Lag Guarantee, Hidden Software"},
    "finest sensi pro": {"price": 1099, "desc": "Custom Sensitivity, Input Optimization, Recoil Config"},
    "prime pack": {"price": 2899, "desc": "FPS + Sensi Combo, Advanced Tweaks, Secret Emulator, Aim Boost"},
    "freefire id": {"price": 1000, "desc": "Freefire ID selling (pricing starts at 1000)"},
    "discord server basic": {"price": 399, "desc": "Basic server setup"},
    "discord server premium": {"price": 799, "desc": "Premium server with configs"},
    "finest server premium": {"price": 1099, "desc": "Full Finest style server with configs"}
}

# ================= CART STORAGE =================
user_carts = {}

def detect_product(text: str):
    text = text.lower()
    for name in PRODUCTS:
        if name in text:
            return name
    return None

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

# ================== PROFILE SHEET CONFIG =================
PROFILE_SHEET_ID = "1ImJPHbYN8-UjYrRKZmbblo4BVBJx3vybKss3cf0exzA"
PROFILE_TAB_NAME = "Profiles"

# ================= AI CONFIG =================
AI_GENERAL_CHANNELS = [1214601102100791346, 1457708857777197066]
FINEST_MEMBER_ROLE = 1463993521827483751
STAFF_ROLE = 1464249885669851360
FINEST_LOG_CHANNEL = 1465979396484632712

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
start_time = datetime.utcnow()

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

ai_client = OpenAI(
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
                
# ================= AI CONFIG =================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

AI_GENERAL_MODELS = [
    "gpt-4o-mini",
    "gpt-4o-mini",
    "gpt-4o-mini"  # redundancy improves stability
]

AI_ADVANCED_MODEL = "gpt-4o"  # premium model for members

AI_GENERAL_CHANNELS = [
    1214601102100791346,  # channel 1
    1457708857777197066   # channel 2
]

FINEST_MEMBER_ROLE = 1463993521827483751
STAFF_ROLE = 1464249885669851360
FINEST_LOG_CHANNEL = 1465979396484632712

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

PRODUCT_KNOWLEDGE = """
You are Finest AI, assistant of Finest Store.

Here are the packs and their exact official definitions:

[ BASIC PACKS ]
1. FREE PACK (₹0)
   - Regedit ASEL Pro
   - Optimizer Regedit
   - Delay Reduction Tools
   - GPU Optimizer
   - Device Tweaks

2. OPTIMIZATION PACK (₹199)
   - Input Delay Fix
   - Stutter Reduction
   - CPU Optimization
   - RAM Optimization
   - Hidden Softwares for Max FPS

3. SENSI PACK (₹399)
   - Mouse & DPI Calculation
   - Balanced Sensi Profile
   - Low Recoil Tuning
   - Mouse 0 Delay
   - Keyboard 0 Delay

[ PREMIUM PACKS ]
4. OPTIMIZATION PRO (₹699)
   - High FPS Optimization
   - Input Delay Reduction
   - No Lag Guarantee
   - Batch Files
   - Advanced Regedits
   - Hidden FPS Softwares

5. FINEST SENSI PRO (₹1099)
   - Custom X/Y Sensitivity
   - Mouse Input Optimization
   - Resolution & FPS Tuning
   - Low Recoil Configurations
   - Hidden Softwares for Aim Assist
   - Custom Resolution Setup

6. PRIME PACK (₹2899)
   - All-in-One Full Tweak Set
   - FPS + Sensi Combo
   - Advanced Input Tweaks
   - Secret Emulator for Smoothness
   - Best Regedits for Headshots
   - Aim & FPS Softwares

7. FREEFIRE ID SELL (from ₹1000)
   - Verified IDs
   - Clean login
   - No ban risk

8. DISCORD SERVER SERVICE
   - Basic Setup: ₹399
   - Premium Server Setup: ₹799
   - Finest Server Creation: ₹1099

RULES FOR AI:
- Always call user “Sir”.
- Always reply with pack details ONLY from this list.
- Never guess unrelated items (no cricket, no sports).
- Never hallucinate.
- Keep answers clean, sales-focused, trustworthy.
- If user asks about a product, explain only from this knowledge.
"""
async def ai_query(prompt, model="gpt-4o-mini"):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are FINEST Discord AI Assistant. "
                        "Call the user 'Sir'. "
                        "Be respectful, short, helpful, modern, accurate, up-to-date and concise. "
                        "Answer ANY question even if not related to packs. "
                        "If asked about packs, answer with business context. "
                        "Never say you lack knowledge, always answer."
                    )
                },
                {"role": "user", "content": PRODUCT_KNOWLEDGE + f"\nUser query: {prompt}\nReply as VALID AI, sir."}
            ]
        }

        response = requests.post(url, headers=headers, json=data, timeout=25)
        result = response.json()

        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("[AI ERROR]", e)
        return "Sorry sir, AI service is busy right now. Try again in a moment."

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
        return None

    guild = member.guild
    data = dict(zip(header, row))
    status = data.get("Status", "").strip().lower()

    # Assign role if paid
    member_role = guild.get_role(MEMBER_ROLE_ID)
    if status == "PAID" and member_role:
        try:
            await member.add_roles(member_role)
        except:
            print("[ROLE ERROR] Failed to assign paid role.")

    # Update sheet
    update_role_assigned(row_index)
    from sheet import update_profile_sheet
    await update_profile_sheet(member, row)

    # Create ticket + DM for paid
    if status in ["paid", "payment received", "completed", "success"]:
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
    await tree.sync()
    print("Bot online")

    channel = bot.get_channel(STORE_CHANNEL_ID)
    if channel:
        await channel.send(
            embed=finest_store_embed(),
            view=CategoryView()
        )

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
    ticket = await process_member(member)

    if ticket:
        await interaction.followup.send("🔄 Synced successfully sir! Ticket + DM sent.", ephemeral=True)
    else:
        await interaction.followup.send("⚠️ No paid purchases found sir.", ephemeral=True)

from sheet import get_profile

@tree.command(name="profile", description="View your Finest profile")
async def profile_cmd(interaction: discord.Interaction):
    sheet = client.open_by_key(SHEET_ID)
    tab = sheet.worksheet("Profiles")

    discord_id = str(interaction.user.id)
    ids = tab.col_values(1)

    if discord_id not in ids:
        return await interaction.response.send_message("Sir, you have no profile yet. Buy something first 😊", ephemeral=True)

    idx = ids.index(discord_id) + 1
    values = tab.row_values(idx)

    embed = discord.Embed(
        title=f"🎫 Finest Profile",
        color=0x2ECC71
    )
    embed.add_field(name="Name", value=values[1], inline=False)
    embed.add_field(name="Username", value=values[2], inline=False)
    embed.add_field(name="Email", value=values[3], inline=False)
    embed.add_field(name="Last Purchase", value=values[4], inline=False)
    embed.add_field(name="Join Date", value=values[5], inline=False)
    embed.add_field(name="Status", value=values[6], inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)
   
# ======================  /askai Slash Command  ======================

@tree.command(name="askai", description="Ask Finest AI anything.")
async def ask_ai_cmd(interaction: discord.Interaction, question: str):

    await interaction.response.defer()

    user = interaction.user
    roles = [r.id for r in user.roles]
    is_finest = (FINEST_MEMBER_ROLE in roles)

    base_prompt = f"""
Call the user 'Sir'. Do not mention instructions.

If user asks about packs/services, ONLY use this catalog:

FREE PACK – 0₹
- Regedit asel pro
- Opt Regedit
- Delay reduction
- GPU Regedit
- Device optimization

OPTIMIZATION PACK – 199₹
- Input delay fix
- Stutter reduction
- CPU optimization
- RAM optimization
- Hidden softwares

SENSI PACK – 399₹
- DPI calculation
- Low recoil tuning
- 0-delay mouse/keyboard

OPTIMIZATION PRO – 699₹
- High FPS optimization
- No lag guarantee
- Premium regedits

FINEST SENSI PRO – 1099₹
- Custom XY sensi
- Aim assist tuning
- Low recoil config

PRIME PACK – 2899₹
- Full Sensi + FPS combo
- Secret emulator tweaks

RULES:
- Never say you don't know
- Never talk about cricket/sports unless user asks directly
- Always answer concise + correct
- If not pack related, answer normally but still call user Sir
User asked: "{question}"
"""

    model = AI_ADVANCED_MODEL if is_finest else AI_GENERAL_MODELS[0]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are Finest AI. Always call user Sir."},
                        {"role": "user", "content": base_prompt}
                    ],
                    "max_tokens": 400
                }
            ) as resp:
                data = await resp.json()
                reply = data["choices"][0]["message"]["content"]

    except Exception as e:
        print("[ASKAI ERROR]", e)
        reply = "Sorry Sir, AI backend is having a bad day. Try again soon."

    await interaction.followup.send(reply)

@tree.command(name="store", description="Open Finest Store")
async def store_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=finest_store_embed(),
        view=CategoryView()
    )

@bot.tree.command(name="finest", description="Show finest Store poster")
async def prime(interaction: discord.Interaction):
    await interaction.response.send_message(
        embed=prime_store_poster()
    )

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
        
import random

SUBS = [
    "IndianGaming",
    "FreeFireBattlegrounds",
    "ValorantMemes",
    "memes",
    "dankmeme"
]

MEME_CHANNEL = 1466027691533926557

@tree.command(name="meme", description="Drop a fresh meme")
async def meme_cmd(interaction: Interaction):
    await interaction.response.defer()

    sub = random.choice(SUBS)
    url = f"https://meme-api.com/gimme/{sub}"

    try:
        r = requests.get(url).json()
        meme_url = r["url"]
        title = r["title"]

        channel = bot.get_channel(MEME_CHANNEL)
        if channel:
            await channel.send(f"**{title}**\n{meme_url}")
            await interaction.followup.send("Meme delivered sir 😎", ephemeral=True)
        else:
            await interaction.followup.send("Meme channel missing sir.", ephemeral=True)

    except:
        await interaction.followup.send("API down sir, no memes today 💀", ephemeral=True)

# ================= MESSAGE COMMANDS =================
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot online.")


# ================== AI CONFIG ==================
import os
import json

ALLOWED_AI_CHANNELS = {1214601102100791346, 1457708857777197066}

AI_GENERAL_MODELS = json.loads(
    os.getenv("AI_GENERAL_MODELS", '["gpt-4o-mini"]')
)
AI_ADVANCED_MODEL = os.getenv("AI_ADVANCED_MODEL", "gpt-4o-mini")

FINEST_MEMBER_ROLE = int(os.getenv("FINEST_MEMBER_ROLE", "0"))
FINEST_LOG_CHANNEL = int(os.getenv("FINEST_LOG_CHANNEL", "0"))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# ================== AI REQUEST FUNCTION ==================
async def ai_query(prompt: str, model: str = "gpt-4o-mini"):
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500
                }
            ) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ Sorry sir, AI is offline. Error: {e}"


# ================== ONE AND ONLY on_message ==================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    content = message.content.lower()

    # ===========================
    # CART COMMANDS
    # ===========================
    if content.startswith("add to cart"):
        product = detect_product(content)
        if not product:
            await message.channel.send("❌ Sir, product not found.")
            return
        user_carts.setdefault(user_id, []).append(product)
        await message.channel.send(f"🛒 Added **{product}** to your cart, sir.")
        return

    if content.startswith("remove from cart"):
        product = detect_product(content)
        if not product or product not in user_carts.get(user_id, []):
            await message.channel.send("❌ Sir, product not in cart.")
            return
        user_carts[user_id].remove(product)
        await message.channel.send(f"🗑 Removed **{product}** from your cart, sir.")
        return

    if content == "cart":
        cart = user_carts.get(user_id, [])
        if not cart:
            await message.channel.send("🛒 Your cart is empty, sir.")
            return
        total = sum(PRODUCTS[p]["price"] for p in cart)
        items = "\n".join(f"• {p} — ₹{PRODUCTS[p]['price']}" for p in cart)
        await message.channel.send(
            f"🛒 **Your Cart:**\n{items}\n\n💰 **Total: ₹{total}**"
        )
        return

    if content == "clearcart":
        user_carts[user_id] = []
        await message.channel.send("♻️ Cart cleared, sir.")
        return

    # ===========================
    # PRICE CHECK
    # ===========================
    product = detect_product(content)
    if product:
        p = PRODUCTS[product]
        await message.channel.send(
            f"📦 **{product.title()}**\n"
            f"💰 Price: **₹{p['price']}**\n"
            f"🧾 Description: {p['desc']}\n\n"
            f"To buy, type: `add to cart {product}`"
        )
        return

    # ===========================
    # AI CHAT (ONLY IN AI CHANNELS)
    # ===========================
    if message.channel.id in ALLOWED_AI_CHANNELS:
        user = message.author
        text = message.content.strip()

        model = (
            AI_ADVANCED_MODEL
            if any(r.id == FINEST_MEMBER_ROLE for r in user.roles)
            else AI_GENERAL_MODELS[0]
        )

        reply = await ai_query(text, model=model)
        await message.channel.send(f"**Sir**, {reply}")

        log_ch = bot.get_channel(FINEST_LOG_CHANNEL)
        if log_ch:
            await log_ch.send(
                f"[AI LOG] `{user}` in <#{message.channel.id}> said:\n> {text}"
            )
        return

    # ===========================
    # REQUIRED FOR PREFIX COMMANDS
    # ===========================
    await bot.process_commands(message)

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

def prime_store_poster():
    embed = discord.Embed(
        title="",
        description="",
        color=0x2B2D31  # dark premium color (same vibe)
    )

    embed.set_image(
        url="https://cdn.discordapp.com/attachments/1166295699290333194/1466167278067515636/ChatGPT_Image_Jan_28_2026_03_51_28_PM.png?ex=697c6aef&is=697b196f&hm=ef26cd785b213cc925573233fd70e46fe86d135f3ba86f80c007597ed4d821f7&"
    )

    return embed

def finest_store_embed():
    embed = discord.Embed(
        title=" <:vg5:1466347915772690432> FINEST STORE",
        color=0x2B2D31
    )

    
    # SECTION 1 — "STANDARD PACKS",
    embed.add_field(
        name=" <:vg9:1466347811170680862> STANDARD PACKS\n",
        value=(
            "\u200b\n"
            "**<a:vga1:1466376555591897272> Optimization Pack**\n\n"
            "<:vg11:1466368081042472961> Shutter Reduction\n"
            "<:vg11:1466368081042472961> Input delay fix, CPU & RAM optimization\n"
            "<:vg11:1466368081042472961> Best power plan, unnecessary services disabled\n\n"
           
            "**<a:vga1:1466376555591897272> Sensi Packs**\n\n"
            "<:vg11:1466368081042472961> Best X/Y sensitivity, DPI calculation\n"
            "<:vg11:1466368081042472961> Balanced sensi, low recoil tuning\n"
            "<:vg11:1466368081042472961> Mouse and Keyboard 0 Delay"
        ),
        inline=False
    )
    "\u200b\n"

    # SECTION 2 — PRO / PREMIUM PACKS
    embed.add_field(
        name="<:vg2:1466347978745970841> Pro & Premium Packs",
        value=(
           "\u200b\n"
            "**<a:vga1:1466376555591897272> Optimization Pro**\n"
            "<:vg11:1466368081042472961> High FPS optimization, no lag guarantee\n"
            "<:vg11:1466368081042472961> Advanced regedits & batch files\n\n"
            
            "**<a:vga1:1466376555591897272> Finest Sensi Pro**\n"
            "<:vg11:1466368081042472961> Custom X/Y sensi, resolution & FPS tuning\n"
            "<:vg11:1466368081042472961> Low recoil configs & aim assist tweaks\n"
        ),
        inline=False
    )
    "\u200b\n"

    # SECTION 3 — ULTIMATE PACK
    embed.add_field(
        name="<:vg1:1466348025910923470> Ultimate Combo\n\n",
        value=(
            "\u200b\n"
            "**<a:vga1:1466376555591897272> Finest Plero Brazilia**\n"
            "<:vg11:1466368081042472961> All-in-one FPS + sensi combo\n"
            "<:vg11:1466368081042472961> Advanced input tweaks\n"
            "<:vg11:1466368081042472961> Secret emulator for smoothness\n"
            "<:vg11:1466368081042472961> Best regedits for headshots"
        ),
        inline=False
    )
    "\u200b\n"
    
    # SECTION 4 — OTHER SERVICES
    embed.add_field(
        name="<:vg7:1466347876580983032> OTHER SERVICES",
        value=(
            "\u200b\n"
            "**<a:vga1:1466376555591897272> Discord Server Setup**\n"
            "<:vg11:1466368081042472961> Basic Server\n"
            "<:vg11:1466368081042472961> Pro Server\n" 
            "<:vg11:1466368081042472961> Finest Server\n"
            "**<a:vga1:1466376555591897272> Freefire Id's**\n"
            "<:vg11:1466368081042472961> Starts from ₹999\n"
            "<:vg11:1466368081042472961> Buy via ticket"
        ),
        inline=False
    )

    embed.set_footer(text="Finest Store • Performance is personal")
    return embed
    
def ticket_warning_embed(pack_name: str):
    return discord.Embed(
        title="⚠️ Ticket Creation Warning",
        description=(
            "By creating a ticket, you acknowledge:\n\n"
            "• No fake or test tickets\n"
            "• Accurate information required\n"
            "• Staff will assist ASAP\n\n"
            f"**Ticket Type:** {pack_name}"
        ),
        color=0x2B2D31
    )
    
def pack_select_embed(category: str):
    return discord.Embed(
        title=category,
        description="Please select the pack you want to continue with:",
        color=0x2B2D31
    )

def device_select_embed():
    return discord.Embed(
        description="**Please select your device type.**",
        color=0x2B2D31
    )

class CategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # ROW 0
    @discord.ui.button(label="Standard Packs", style=discord.ButtonStyle.secondary, row=0)
    async def standard(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=pack_select_embed("standard"),
            view=PackSelectView("standard"),
            ephemeral=True
        )

    @discord.ui.button(label="Pro & Premium", style=discord.ButtonStyle.secondary, row=0)
    async def pro(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=pack_select_embed("pro"),
            view=PackSelectView("pro"),
            ephemeral=True
        )

    # ROW 1
    @discord.ui.button(label="Ultimate Combo", style=discord.ButtonStyle.secondary, row=1)
    async def ultimate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=pack_select_embed("ultimate"),
            view=PackSelectView("ultimate"),
            ephemeral=True
        )

    @discord.ui.button(label="Other Services", style=discord.ButtonStyle.secondary, row=1)
    async def other(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=pack_select_embed("other"),
            view=PackSelectView("other"),
            ephemeral=True
        )
        
class PackSelectView(discord.ui.View):
    def __init__(self, category: str):
        super().__init__(timeout=120)
        for pack in PACK_CATEGORIES[category]:
            self.add_item(PackButton(pack))


class PackButton(discord.ui.Button):
    def __init__(self, pack_name: str):
        super().__init__(
            label=pack_name,
            style=discord.ButtonStyle.secondary
        )
        self.pack_name = pack_name

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=ticket_warning_embed(self.pack_name),
            view=TicketConfirmView(self.pack_name),
            ephemeral=True
        )
        
class TicketConfirmView(discord.ui.View):
    def __init__(self, pack_name: str):
        super().__init__(timeout=120)
        self.pack_name = pack_name

    @discord.ui.button(
        label="Confirm & Create",
        style=discord.ButtonStyle.success
    )
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        # 🚫 STEP 11 — DUPLICATE TICKET CHECK
        for ch in guild.text_channels:
            if ch.category and ch.category.id == TICKET_CATEGORY_ID:
                if ch.name == f"ticket-{user.name.lower()}":
                    await interaction.response.send_message(
                        f"❌ You already have an open ticket: {ch.mention}",
                        ephemeral=True
                    )
                    return

        category = guild.get_channel(TICKET_CATEGORY_ID)

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name.lower()}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True)
            }
        )

        await channel.send(
            content=f"<@&{STAFF_ROLE_ID}>",
            embed=device_select_embed(),
            view=DeviceSelectView(self.pack_name)
        )

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger
    )
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

class DeviceSelect(discord.ui.Select):
    def __init__(self, pack_name: str):
        self.pack_name = pack_name

        options = [
            discord.SelectOption(label="Phone (Android)", emoji="🤖"),
            discord.SelectOption(label="Phone (iPhone)", emoji="🍎"),
            discord.SelectOption(label="PC / Laptop", emoji="💻"),
        ]

        super().__init__(
            placeholder="Select your device type...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        device = self.values[0]
        await interaction.response.send_modal(
            DeviceSpecsModal(self.pack_name, device)
        )
        
class DeviceSelectView(discord.ui.View):
    def __init__(self, pack_name: str):
        super().__init__(timeout=120)
        self.add_item(DeviceSelect(pack_name))

class DeviceSpecsModal(discord.ui.Modal, title="Device Specifications"):
    def __init__(self, pack_name: str, device: str):
        super().__init__()
        self.pack_name = pack_name
        self.device = device

        self.specs = discord.ui.TextInput(
            label="Enter your device specifications",
            placeholder="e.g. Windows 11, Ryzen 5, 16GB RAM",
            required=True,
            max_length=300
        )

        self.add_item(self.specs)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"✅ **Details Submitted**\n\n"
            f"**Pack:** {self.pack_name}\n"
            f"**Device:** {self.device}\n"
            f"**Specs:** {self.specs.value}",
            ephemeral=True
        )

        # 🚨 NEXT STEP (later):
        # create ticket channel
        # ping staff
        # save transcript

# ================= START =================
keep_alive()
bot.run(TOKEN)
