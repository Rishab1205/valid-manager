# ================== KEEP ALIVE (FOR UPTIME ROBOT) ==================
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_web).start()

# ===================== DISCORD BOT CODE ============================
import os
import discord
import asyncio
import datetime
from discord.ext import commands, tasks
from discord import app_commands

TOKEN = os.getenv("TOKEN")  # Token from Railway Variables
if TOKEN is None:
    print("❌ ERROR: TOKEN is missing from Railway Variables.")
else:
    print("TOKEN LOADED")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
start_time = datetime.datetime.utcnow()

# ================================================================
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"⚙️ Slash commands synced: {len(synced)}")
    except Exception as e:
        print("Slash Sync Error:", e)

    print(f"🟢 {bot.user} is online & ready!")
    update_status.start()

# ================== STATUS ROTATION ==============================
@tasks.loop(seconds=60)
async def update_status():
    guild_count = len(bot.guilds)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{guild_count} servers | /uptime"
        )
    )

# ================== SLASH: SAY COMMAND ===========================
@bot.tree.command(name="say", description="Make bot send a message in a channel")
@app_commands.describe(channel="Where to send message", message="Message content")
async def slash_say(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    await channel.send(message)
    await interaction.response.send_message("📨 Message sent!", ephemeral=True)

# ================== SLASH: UPTIME COMMAND ========================
@bot.tree.command(name="uptime", description="Shows bot uptime")
async def slash_uptime(interaction: discord.Interaction):
    now = datetime.datetime.utcnow()
    delta = now - start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    await interaction.response.send_message(
        f"⏱️ Uptime: **{hours}h {minutes}m {seconds}s**"
    )

# ================== TEXT COMMANDS (OPTIONAL) =====================
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot is alive.")

# ====================== STARTUP ================================
keep_alive()
bot.run(TOKEN)
