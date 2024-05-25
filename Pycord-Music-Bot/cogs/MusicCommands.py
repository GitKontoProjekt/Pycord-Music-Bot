import discord
from discord.ext import commands

from cogs.MusicPlayer import MusicPlayer

import os
from dotenv import load_dotenv

load_dotenv()
LAVALINK_KEY = os.getenv("LAVALINK_KEY")


class MusicCommands(commands.Cog):
    """Handles playing music in voice chat"""

    def __init__(self, client: commands.Bot):
        """Inits the Music Class"""

        self.client = client
        self.music_player = MusicPlayer(self.client)
        self.text = []

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Runs when the bot is ready and connects to wavelink api"""

        print("MusicCommands.py is ready!")

    @discord.command(name="play", description="Spelar/köar den angivna låten/länken.")
    async def play(self, ctx: discord.ApplicationContext, query: str) -> None:
        """Initiates vc and plays given track"""

        await self.music_player.play(ctx, query)
    
    @discord.command(name="pause", description="Pausar spelaren.")
    async def pause(self, ctx: discord.ApplicationContext) -> None:
        """Pauses the player"""

        await self.music_player.pause(ctx)

    @discord.command(name="resume", description="Återupptar spelaren.")
    async def resume(self, ctx: discord.ApplicationContext) -> None:
        """Resumes the player"""

        await self.music_player.resume(ctx)

    @discord.command(name="skip", description="Skippar nuvarande låt.")
    async def skip(self, ctx: discord.ApplicationContext) -> None:
        """Skips the current song"""

        await self.music_player.skip(ctx)

    @discord.command(name="shuffle", description="Blandar om låtkön.")
    async def shuffle(self, ctx: discord.ApplicationContext) -> None:
        """Shuffles the queue"""

        await self.music_player.shuffle(ctx)

    queue_group = discord.SlashCommandGroup(name="queue", description="Visar låtkön.")
    @queue_group.command(name="show", description="Visar låtkön.")
    async def queue_show(self, ctx: discord.ApplicationContext) -> None:
        """Shows the queue"""

        await self.music_player.queue_show(ctx)
    
    @queue_group.command(name="clear", description="Rensar låtkön.")
    async def queue_clear(self, ctx: discord.ApplicationContext) -> None:
        """Clears the queue"""
        
        await self.music_player.queue_clear(ctx)

    @discord.command(name="disconnect", description="Kopplar bort botten.")
    async def disconnect(self, ctx: discord.ApplicationContext) -> None:
        """Disconnects the player"""

        await self.music_player.disconnect(ctx)


def setup(client: commands.Bot) -> None:
    """Setup the cog"""

    client.add_cog(MusicCommands(client))
