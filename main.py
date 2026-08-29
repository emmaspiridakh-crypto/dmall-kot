import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

from database import Database
from keep_alive import keep_alive

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")


async def load_cogs():
    await bot.load_extension("cogs.dm_cog")


async def main():
    await Database.init()
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
