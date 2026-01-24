# ================= KEEP ALIVE =================
from flask import Flask
from threading import Thread
import os
import time
import asyncio
from collections import deque
import datetime

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_web).start()


# =============================================
# ================= DISCORD BOT ================
import discord
from discord.ext import commands, tasks
from discord import app_commands

TOKEN = os.getenv("TOKEN")
print("DEBUG TOKEN:", TOKEN)

start_time = datetime.datetime.utcnow()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ---------- RAID CONFIG ----------
RAID_JOIN_LIMIT = 5
RAID_TIME_WINDOW = 10
LOCK_DURATION = 300  # 5 minutes

join_tracker = deque()
server_locked = False


# ---------- MEMBERSHIP EMBED ----------
def membership_embed():
    embed = discord.Embed(
        title="💎 OFFICIAL VALID GAMING – YT MEMBERSHIP",
        description="Support the channel & unlock exclusive perks 🔥",
        color=0x2f3136)

    embed.add_field(name="🥇 GOLD – ₹59 / month",
                    value="• Custom member badges",
                    inline=False)
    
    embed.add_field(name="🥈 PLATINUM – ₹119 / month",
                    value="• Member-only Shorts",
                    inline=False)
    
    embed.add_field(name="💠 DIAMOND – ₹179 / month",
                    value="• Friend Request\n• Member Shout-out",
                    inline=False)

    embed.add_field(
        name="🎯 Join Now",
        value="[Click here to join](https://youtube.com/@officialvalidgaming/join)",
        inline=False)

    embed.set_footer(text="VALID GAMING • Official Membership")
    return embed


# ---------- STATUS ----------
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online 🚀")
    update_status.start()
    try:
        synced = await tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(e)


@tasks.loop(minutes=2)
async def update_status():
    if not bot.guilds:
        return
    guild = bot.guilds[0]
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{guild.member_count} users | Valid Subs"))


# ---------- LOCK / UNLOCK ----------
async def lock_server(guild):
    global server_locked
    if server_locked:
        return

    server_locked = True
    everyone = guild.default_role

    for channel in guild.text_channels:
        await channel.set_permissions(everyone, send_messages=False)

    channel = guild.system_channel or guild.text_channels[0]

    await channel.send(
        f"🚨 **ANTI-RAID ACTIVATED**\nChat locked for **5 minutes**.")

    await asyncio.sleep(LOCK_DURATION)

    for channel in guild.text_channels:
        await channel.set_permissions(everyone, send_messages=True)

    await channel.send("✅ **ANTI-RAID DISABLED**\nChat unlocked.")
    server_locked = False


# =========================
#  GOOGLE SHEETS + ROLES
# =========================
from sheet import find_user_row, update_role_assigned

MEMBER_ROLE_ID = int(os.getenv("DISCORD_MEMBER_ROLE_ID"))
STAFF_ROLE_ID = int(os.getenv("DISCORD_STAFF_ROLE_ID"))

@bot.event
async def on_member_join(member):
    now = time.time()
    join_tracker.append(now)

    while join_tracker and now - join_tracker[0] > RAID_TIME_WINDOW:
        join_tracker.popleft()

    if len(join_tracker) >= RAID_JOIN_LIMIT:
        await lock_server(member.guild)

    # -------- SHEET ROLE LOGIC --------
    row, data = find_user_row(str(member.id))
    if row:
        print(f"[SHEET] Found user in row {row}, assigning roles")
        member_role = member.guild.get_role(MEMBER_ROLE_ID)
        staff_role = member.guild.get_role(STAFF_ROLE_ID)

        if member_role:
            await member.add_roles(member_role)
            print(f"[ROLE] Added MEMBER role to {member}")

        if staff_role:
            await member.add_roles(staff_role)
            print(f"[ROLE] Added STAFF role to {member}")

        update_role_assigned(row)
        print(f"[SHEET] Updated RoleAssigned = TRUE")

    # -------- WELCOME DM --------
    try:
        embed = discord.Embed(
            title="📜 Welcome to VALID DC",
            description="To activate your purchase, open a ticket!",
            color=0x2f3136)
        await member.send(embed=embed)
    except discord.Forbidden:
        pass

    await update_status()


@bot.event
async def on_member_remove(member):
    update_status.restart()


# ---------- MESSAGE AUTOREPLIES ----------
PRICE_TRIGGERS = ["price", "prices", "how much"]

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    text = message.content.lower()

    if any(t in text for t in PRICE_TRIGGERS):
        await message.channel.send(embed=membership_embed())

    elif "how to buy" in text:
        await message.channel.send("🛒 Buy via YouTube Membership. Type **price** to see plans.")

    elif "rules" in text:
        await message.channel.send("📜 Rules were sent in your DMs.")

    elif "link" in text:
        await message.channel.send("🔗 https://youtube.com/@officialvalidgaming")

    await bot.process_commands(message)


# ---------- PREFIX COMMANDS ----------
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot is alive.")


@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, channel: discord.TextChannel, *, message: str):
    await channel.send(message)
    await ctx.message.delete()


# ---------- SLASH COMMANDS ----------
@tree.command(name="ping", description="Check bot latency")
async def ping_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! Bot is alive.")


@tree.command(name="price", description="Show membership prices")
async def price_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(embed=membership_embed())


@tree.command(name="uptime", description="Show bot uptime")
async def uptime_cmd(interaction: discord.Interaction):
    now = datetime.datetime.utcnow()
    delta = now - start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    mins, secs = divmod(remainder, 60)
    await interaction.response.send_message(
        f"⏳ Uptime: **{hours}h {mins}m {secs}s**")


# ================= START =================
keep_alive()
bot.run(TOKEN)
