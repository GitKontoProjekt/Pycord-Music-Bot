import discord
from discord.ext import commands

from cogs.CreateEmbed import CreateEmbed

import wavelink

from typing import Optional, List, cast

import os
from dotenv import load_dotenv

load_dotenv()
LAVALINK_KEY = os.getenv("LAVALINK_KEY")


class MusicPlayer(commands.Cog):
    """Handles playing music in voice chat"""

    def __init__(self, client: commands.Bot):
        """Inits the Music Class"""

        self.client = client
        self.create_embed = CreateEmbed(self.client)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Runs when the bot is ready and connects to wavelink api"""

        try:
            node: wavelink.Node = wavelink.Node(
                uri="http://localhost:2333", 
                password=LAVALINK_KEY, 
                inactive_player_timeout=300
            )
            await wavelink.Pool.connect(client=self.client, nodes=[node])
        except Exception as e:
            print(f"Exception occured when trying to connect to lavalink: {e}")

        print("MusicPlayer.py is ready!")
    
    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Playable) -> None:
        channel = self.client.get_channel(player.home)

        await player.disconnect()
        await self.create_embed.reset_embeds()
        await channel.send(embed=await self.create_embed.disconnect())

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        """Shows current song and checks voice channel activity, disconnects when appropriate"""

        channel = self.client.get_channel(payload.player.home)

        if len(self.client.voice_clients[0].channel.members) <= 1:
            await self.create_embed.reset_embeds()
            await payload.player.disconnect()

            await channel.send(embed=await self.create_embed.disconnect())
        else:
            button_view = ButtonView(self.client)
            await channel.send(
                embed=await self.create_embed.get_now_playing(payload.track), view=button_view
            )

    async def play(self, ctx: discord.ApplicationContext, query: str) -> None:
        """Initiates vc and plays given track"""
        
        await ctx.response.defer()

        if not ctx.user.voice:
            await ctx.followup.send(
                embed=await self.create_embed.user_not_in_channel()
            )
        player: wavelink.Player
        player = cast(wavelink.Player, ctx.guild.voice_client)  # type: ignore

        if not player:
            player = await ctx.user.voice.channel.connect(cls=wavelink.Player)
            player.home = ctx.channel.id

        if not await self.check_channel_condition(ctx, player):
            return
        
        tracks: wavelink.Search = await wavelink.Playable.search(query)

        if not tracks:
            return await ctx.followup.send(
                embed=await self.create_embed.one_line_embed("Låten hittades inte")
            )
        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)

            if player.queue:
                await ctx.followup.send(
                    embed=await self.create_embed.list_added(
                        query, tracks, player.queue, ctx.user, added, player
                    )
                )
        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)

            if player.queue:
                await ctx.followup.send(
                    embed=await self.create_embed.song_added(
                        track, player.queue, ctx.user, player
                    )
                )
        await self.create_embeds(ctx, tracks)
        if not player.playing:
            await player.play(player.queue.get(), volume=30)

        player.autoplay = wavelink.AutoPlayMode.partial

    async def pause(self, ctx: discord.ApplicationContext) -> None:
        """Pauses the player"""

        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)

        if not await self.check_channel_condition(ctx, player):
            return
        
        if player.paused:
            return await ctx.response.send_message(
                embed=await self.create_embed.one_line_embed("Redan pausad!")
            )
        else:
            await player.pause(True)
            await ctx.response.send_message(
                embed=await self.create_embed.pause_resume(player)
            )

    async def resume(self, ctx: discord.ApplicationContext) -> None:
        """Resumes the player"""

        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)

        if not await self.check_channel_condition(ctx, player):
            return

        if not player.paused:
            return await ctx.response.send_message(
                embed=await self.create_embed.one_line_embed("Spelar redan!")
            )
        else:
            await player.pause(False)
            await ctx.response.send_message(
                embed=await self.create_embed.pause_resume(player)
            )

    async def skip(self, ctx: discord.ApplicationContext) -> None:
        """Skips the current song"""

        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)

        if not await self.check_channel_condition(ctx, player):
            return

        await player.skip()
        await ctx.response.send_message(
            embed=await self.create_embed.one_line_embed("Låt skippad!")
        )

    async def shuffle(self, ctx: discord.ApplicationContext) -> None:
        """Shuffles the queue"""

        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)
        player.queue.shuffle()
        
        return await ctx.response.send_message(
            embed=await self.create_embed.one_line_embed("Låtkön blandad!")
        )
    
    async def queue_show(self, ctx: discord.ApplicationContext) -> None:
        """Shows the queue"""

        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)
        if not await self.check_channel_condition(ctx, player):
            return

        if not player.queue:
            return await ctx.response.send_message(
                embed=await self.create_embed.one_line_embed("Finns ingen låtkö!")
            )
        await self.create_embed.queue_show(ctx, player)

    async def queue_clear(self, ctx: discord.ApplicationContext) -> None:
        """Clears the queue"""
        
        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)

        if not await self.check_channel_condition(ctx, player):
            return
        
        player.queue.clear()
        await ctx.response.send_message(
            embed=await self.create_embed.one_line_embed("Låtkön rensad!")
        )
        await self.create_embed.reset_embeds()

    async def disconnect(self, ctx: discord.ApplicationContext) -> None:
        """Disconnects the player"""

        player: wavelink.Player = cast(wavelink.Player, ctx.guild.voice_client)

        if not await self.check_channel_condition(ctx, player):
            return
        
        await player.disconnect()
        await ctx.response.send_message(
            embed=await self.create_embed.one_line_embed(
                f"{self.client.user.display_name} har bortkopplats!"
            )
        )
        await self.create_embed.reset_embeds()

    async def check_channel_condition(
            self, ctx: discord.ApplicationContext, player: wavelink.Player
        ) -> bool:
        """Returns error message if bot not in channel or not in same channel as user"""

        if not player:
            await ctx.response.send_message(
                embed=await self.create_embed.not_in_channel()
            )
            return False
        
        if player.channel != ctx.user.voice.channel:
            await ctx.response.send_message(
                embed=await self.create_embed.not_same_channel(player)
            )
            return False
        
        return True
    
    async def create_embeds(self, ctx: discord.ApplicationContext, tracks: list) -> None:
            """Creates embeds to show when playing song"""  

            if isinstance(tracks, wavelink.Playlist):
                for track in tracks:
                    await self.create_embed.now_playing(track, ctx.user)
            else:
                await self.create_embed.now_playing(tracks[0], ctx.user)


class ButtonView(discord.ui.View):
    """Button view for player functions"""

    def __init__(self, client: commands.Cog, timeout=300):
        super().__init__(timeout=timeout)
        self.client = client
        self.music_player = MusicPlayer(self.client)

    @discord.ui.button(emoji="▶️")
    async def resume(self, button: discord.ui.Button, ctx: discord.ApplicationContext) -> None:
        
        await self.music_player.resume(ctx)

    @discord.ui.button(emoji="⏸️")
    async def pause(self, button: discord.ui.Button, ctx: discord.ApplicationContext) -> None:
        
        await self.music_player.pause(ctx)

    @discord.ui.button(emoji="⏭️")
    async def skip(self, button: discord.ui.Button, ctx: discord.ApplicationContext) -> None:

        await self.music_player.skip(ctx)

    @discord.ui.button(emoji="⏹️", row=1)
    async def queue_clear(self, button: discord.ui.Button, ctx: discord.ApplicationContext) -> None:

        await self.music_player.queue_clear(ctx)

    @discord.ui.button(emoji="🔀", row=1)
    async def shuffle(self, button: discord.ui.Button, ctx: discord.ApplicationContext) -> None:

        await self.music_player.shuffle(ctx)

    @discord.ui.button(emoji="🔽", row=1)
    async def queue_show(self, button: discord.ui.Button, ctx: discord.ApplicationContext) -> None:

        await self.music_player.queue_show(ctx)


def setup(client: commands.Bot) -> None:
    """Setup the cog"""

    client.add_cog(MusicPlayer(client))
