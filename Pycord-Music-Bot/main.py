import asyncio

import discord
from discord.ext import commands

import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
discord.Intents.message_content = True


@client.event
async def on_ready():
    """Prints user/guild names and ids and syncs all commands when bot is ready"""

    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f"{client.user} is connected to the following guild:\n"
        f"{guild.name}(id: {guild.id})"
    )
    members = "\n - ".join([member.name for member in guild.members])
    print(f"Guild Members:\n - {members}")


async def load():
    """Loads all cogs"""

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            client.load_extension(f"cogs.{filename[:-3]}")


async def main():
    """Calls load and starts client"""

    async with client:
        await load()
        await client.start(TOKEN)


asyncio.run(main())
