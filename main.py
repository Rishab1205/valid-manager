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
PAYMODE = "B"
STATUS_FIELD = "Status"

GIF_LINK = "https://cdn.discordapp.com/attachments/1214620206329241660/1464784224035803320/a_e8bcf2f0719b83d332a02913ff57752e.gif"

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
        title="💎 VALID GAMING — YT MEMBERSHIP",
        description=(
            "Support the channel & unlock exclusive perks 🔥\n"
            "Membership is processed via **YouTube** and auto-syncs to Discord.\n\n"
            "**Available Tiers:**"
        ),
        color=0x2B2D31
    )

    embed.add_field(
        name="🥇 GOLD — ₹59 / month",
        value="• Custom member **Badges**",
        inline=False
    )

    embed.add_field(
        name="🥈 PLATINUM — ₹119 / month",
        value="• Member-only **Shorts**",
        inline=False
    )

    embed.add_field(
        name="💠 DIAMOND — ₹179 / month",
        value="• **Friend Request**\n• **Member Shout-out**",
        inline=False
    )

    embed.add_field(
        name="🎯 Join Now",
        value="[Click here to join](https://youtube.com/@officialvalidgaming/join)",
        inline=False
    )

    embed.add_field(
        name="🔗 How to get your Membership Role",
        value=(
            "1. Link your **YouTube** account to **Discord**.\n"
            "2. Go to `User Settings` → `Connections` → **YouTube**.\n"
            "3. Authorize & link your Google account.\n"
            "4. Join the server through your **YouTube Membership** tab.\n"
            "5. Discord auto-syncs & assigns your membership role.\n\n"
            "**Membership Roles:**\n"
            "• `@YouTube Member`\n"
            "• `@Gold`\n"
            "• `@Platinum`\n"
            "• `@Diamond`\n\n"
            "If roles don’t sync or you're stuck, just ask in support."
        ),
        inline=False
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1166295699290333194/1457814947756249262/1b2d8db2-332e-42ce-80c5-54d946086c95.png?ex=695d5f78&is=695c0df8&hm=b9d50252c94669ca727b92a6a17a4fc0885f5f3428693964418bde3050cf5a43&")
    embed.set_image(url="https://cdn.discordapp.com/attachments/1166295699290333194/1457812767846301779/Colorful_Abstract_Aesthetic_Linkedin_Banner.png?ex=695d5d70&is=695c0bf0&hm=54158c4f4872f943f7dad394bbe31419d2320158f07d94bb2ff20a1997b04a22&")
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

        await interaction.response.send_message(f"👑 {interaction.user.mention} claimed this ticket.")
        log = bot.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(f"📌 Ticket claimed by {interaction.user.mention} for `{self.member.name}`")

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
• Wait for a staff member to **claim** your ticket  
• Once claimed, they will guide you through the process

📤 **Payment Verification**
Upload your screenshot in → <#{PAYOUT_CHANNEL_ID}>

🗂 **Purchase Details**
• **Name:** `{data.get('Name','N/A')}`
• **Product:** `{data.get('Product','N/A')}`
• **Payment ID:** `{data.get('Payment ID','HIDDEN' if PAYMODE=='b' else data.get('Payment ID','N/A'))}`
• **Status:** `{data.get('Status','N/A')}`

✨ Finest Support — Zero friction, just service.
"""
    embed = discord.Embed(title="Welcome to Support", description=desc, color=0x2b2d31)
    await ticket.send(embed=embed, view=ClaimButton(member))

    if log:
        await log.send(f"📂 Ticket created for {member.name} → {ticket.mention}")

    status = data.get(STATUS_FIELD, "").upper()
    if PAYMODE == "B" and status == "PAID":
        try:
            dm = discord.Embed(
                title="🎉 Payment Confirmed!",
                description=f"Hi {member.mention} 👋\nYour purchase was successful!",
                color=0x2b2d31
            )
            dm.add_field(name="📁 Ticket", value=ticket.mention, inline=False)
            dm.add_field(name="📸 Next step", value=f"Upload screenshot in → <#{PAYOUT_CHANNEL_ID}>", inline=False)
            dm.set_footer(text="✨ Thanks for choosing FINEST — performance is personal.")
            await member.send(embed=dm)
        except:
            pass

# ================= ROLE + PROCESS LOGIC =================
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

# ================= WELCOME DM =================
async def send_join_dm(member):
    try:
        embed1 = discord.Embed(
            title="👋 Welcome to **VALID DC**",
            description=(
                f"Hey **{member.name}**, welcome aboard! 🔥\n\n"
                "You're now part of a community built for gamers who respect:\n"
                "• **Performance**\n"
                "• **Discipline**\n"
                "• **Clean gameplay**\n\n"
                "Whether you're chilling, grinding, or need premium support — you're in the right place 🚀\n\n"
                "💬 **Main Chat:** `#chat`\n"
                "🛠 **Support:** Open a ticket anytime\n"
            ),
            color=0x2b2d31
        )
        embed1.set_footer(text="VALID DC • Established for serious players")

        embed2 = discord.Embed(
            title="📜 **Quick Rules & Conduct**",
            description=(
                "Before you jump in, here's the quick code we live by:\n\n"
                "1️⃣ **Respect everyone** — no harassment or hate.\n"
                "2️⃣ **No spam / self-promo** — keep chat clean & human.\n"
                "3️⃣ **No scams or shady links** — instant ban.\n"
                "4️⃣ **Follow Discord TOS** — no exceptions.\n\n"
                "⚠️ Violations may lead to warnings, mutes, or bans.\n\n"
                "If you ever feel confused or need help — staff are **one ticket away**.\n\n"
                "Glad to have you here — now go make some moves. ❤️"
            ),
            color=0x5865F2
        )
        embed2.set_footer(text="Stay respectful • Stay sharp • Stay valid")

        await member.send(embeds=[embed1, embed2])
    except Exception as e:
        print("[DM-ERROR] Could not send onboarding DM:", e)

# ================= EVENTS =================
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online 🚀")
    update_status.start()
    try:
        await tree.sync()
        print("Slash commands synced!")
    except Exception as e:
        print(e)

@bot.event
async def on_member_join(member):
    now = time.time()
    join_tracker.append(now)
    while join_tracker and now - join_tracker[0] > RAID_TIME_WINDOW:
        join_tracker.popleft()
    if len(join_tracker) >= RAID_JOIN_LIMIT:
        await lock_server(member.guild)

    await send_join_dm(member)
    await process_member(member)

# ================= PRESENCE =================
@tasks.loop(minutes=2)
async def update_status():
    if not bot.guilds:
        return
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
    if server_locked:
        return
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
    synced = await tree.sync()
    await ctx.send(f"Synced {len(synced)} commands.")

# ================= SLASH COMMANDS =================
@tree.command(name="uptime", description="Bot uptime")
async def uptime(interaction: Interaction):
    delta = datetime.datetime.utcnow() - start_time
    await interaction.response.send_message(f"⏳ `{delta}`")

@tree.command(name="price", description="Show membership prices")
async def price(interaction: Interaction):
    await interaction.response.send_message(embed=membership_embed())

# ================= CLOSE TICKET =================
from discord.app_commands import MissingPermissions

@tree.command(name="close", description="Close this ticket")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def close(interaction: Interaction):
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

    for overwrite_target in list(channel.overwrites):
        if isinstance(overwrite_target, discord.Member):
            await channel.set_permissions(overwrite_target, view_channel=False)
        if isinstance(overwrite_target, discord.Role) and overwrite_target.id == STAFF_ROLE_ID:
            await channel.set_permissions(overwrite_target, view_channel=True)

    await interaction.response.send_message("📁 Ticket archived.", ephemeral=True)

    # DM closed
    if member:
        try:
            closed_embed = discord.Embed(
                title="🎫 Ticket Closed",
                description=(
                    f"Your support ticket has been closed.\n\n"
                    "❤️ **Thank you for choosing Finest Store** ❤️\n"
                    "_Performance is personal._\n\n"
                    "If you ever need anything again, just open a new ticket!"
                ),
                color=0xff4757
            )
            closed_embed.set_thumbnail(url=GIF_LINK)
            await member.send(embed=closed_embed)
        except Exception as e:
            print("[DM-ERROR] Could not DM ticket closed:", e)

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
