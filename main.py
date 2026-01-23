# ================= KEEP ALIVE =================
from flask import Flask
from threading import Thread
import os
import time
import asyncio
from collections import deque

app = Flask('')


@app.route('/')
def home():
    return "Bot is alive!"


def run_web():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    Thread(target=run_web).start()


# ============================================

# ================= DISCORD BOT =================
import discord
from discord.ext import commands, tasks

TOKEN = os.getenv("TOKEN")  # Replit Secret
print("DEBUG TOKEN:", TOKEN)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- RAID CONFIG ----------
RAID_JOIN_LIMIT = 5
RAID_TIME_WINDOW = 10
LOCK_DURATION = 300  # 5 minutes

ASSISTANT_ROLE_ID = 1214555365954560030
SQUIRE_ROLE_ID = 1214555001473732609

join_tracker = deque()
server_locked = False
# --------------------------------


# ---------- STATUS ----------
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online 🚀")
    update_status.start()


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

    assistant = guild.get_role(ASSISTANT_ROLE_ID)
    squire = guild.get_role(SQUIRE_ROLE_ID)

    pings = ""
    if assistant:
        pings += assistant.mention + " "
    if squire:
        pings += squire.mention

    await channel.send(
        f"🚨 **ANTI-RAID ACTIVATED**\n{pings}\nChat locked for **5 minutes**.")

    await asyncio.sleep(LOCK_DURATION)

    for channel in guild.text_channels:
        await channel.set_permissions(everyone, send_messages=True)

    await channel.send("✅ **ANTI-RAID DISABLED**\nChat unlocked.")
    server_locked = False


# ---------- MEMBER JOIN ----------
@bot.event
async def on_member_join(member):
    now = time.time()
    join_tracker.append(now)

    while join_tracker and now - join_tracker[0] > RAID_TIME_WINDOW:
        join_tracker.popleft()

    if len(join_tracker) >= RAID_JOIN_LIMIT:
        await lock_server(member.guild)

    try:
        embed = discord.Embed(title="📜 Welcome to VALID DC",
                              description=(f"Hello **{member.name}** 👋\n\n"
                                           "1️⃣ Be respectful\n"
                                           "2️⃣ No spam or scams\n"
                                           "3️⃣ Follow Discord TOS\n\n"
                                           "🔗 https://discord.gg/jyuYckmyFG"),
                              color=0x2f3136)
        await member.send(embed=embed)
    except discord.Forbidden:
        pass

    await update_status()


@bot.event
async def on_member_remove(member):
    update_status.restart()


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
        value=
        "[Click here to join](https://youtube.com/@officialvalidgaming/join)",
        inline=False)

    embed.set_footer(text="VALID GAMING • Official Membership")
    return embed


# ---------- MESSAGE HANDLER ----------
PRICE_TRIGGERS = ["price", "prices", "how much"]


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    text = message.content.lower()

    if any(t in text for t in PRICE_TRIGGERS):
        await message.channel.send(embed=membership_embed())

    elif "how to buy" in text:
        await message.channel.send(
            "🛒 Buy via YouTube Membership. Type **price** to see plans.")

    elif "rules" in text:
        await message.channel.send("📜 Rules were sent in your DMs.")

    elif "link" in text:
        await message.channel.send("🔗 https://youtube.com/@officialvalidgaming"
                                   )

    # ⚠️ THIS LINE MUST ALWAYS BE LAST
    await bot.process_commands(message)


# ---------- COMMANDS ----------
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot is alive.")


@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx, channel: discord.TextChannel, *, message: str):
    await channel.send(message)
    await ctx.message.delete()


# ================= START =================
keep_alive()
bot.run(TOKEN)
