import os
from dotenv import load_dotenv
from bot_setup import bot, tree
import commands

# Load .env
load_dotenv()
DISCORD_TOKEN = os.getenv("TOKEN")
print(f"DISCORD_TOKEN: {DISCORD_TOKEN}")

# --- Bot Events ---

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    # Remove guild-specific sync
    # guild = discord.Object(id=YOUR_GUILD_ID)
    # await tree.sync(guild=guild)
    # print("Command tree synced to guild!")

    # Perform a global sync
    await tree.sync()
    print("Command tree synced globally!")

try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    print(f"Error running bot: {e}")
