import discord
from discord.ext import commands

from discord.ext.pages import Paginator, Page, PaginatorButton

from random import randrange
import time

import wavelink

EMBEDS = {}

class CreateEmbed(commands.Cog):
    """Handles creating embeds"""

    def __init__(self, client: commands.Bot):
        """Initiates the CreateEmbed Class"""

        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        """Tells that the bot is ready"""

        print("CreateEmbed.py is ready!")

    async def now_playing(
        self,
        track: wavelink.Playable,
        member: discord.Member,
    ):
        """Creates the now playing embed and stores in a dict"""
        
        now_playing = discord.Embed(
            title=track.title,
            description=f"Begärd av {member.mention}",
            url=track.uri,
            colour=discord.Colour.dark_purple(),
        )
        now_playing.set_author(name=track.author)
        now_playing.set_footer(
            text=(f"Längd: "
                  f"{time.strftime('%H:%M:%S', time.gmtime(track.length / 1000))} | "
                  f"Spelas nu")
            )

        if track in EMBEDS:
            EMBEDS[track][1] += 1
        else:
            EMBEDS[track] = [now_playing, 1]

    async def pause_resume(self, player: wavelink.Player):
        if not player.paused:
            resume = discord.Embed(
                title="Återupptar",
                colour=discord.Colour.dark_purple()
            )
            return resume
        else:
            pause = discord.Embed(
                title="Pausar",
                colour=discord.Colour.dark_purple()
            )
            return pause

    async def one_line_embed(self, message: str) -> discord.Embed:
        one_line_embed = discord.Embed(
                title=message,
                colour=discord.Colour.dark_purple()
            )
        return one_line_embed

    async def get_now_playing(self, track: wavelink.Playable) -> discord.Embed:
        """Gets the now playing embed"""

        if EMBEDS[track][1] == 1:
            return EMBEDS.pop(track)[0]
        else:
            EMBEDS[track][1] -= 1
            return EMBEDS[track][0]

    async def song_added(
        self,
        track: wavelink.Playable,
        queue: wavelink.player.Queue,
        member: discord.Member,
        player: wavelink.Player = None
    ) -> discord.Embed:
        """Creates the song added embed"""

        song_added = discord.Embed(
            title=track.title,
            description=f"Begärd av {member.mention}",
            url=track.uri,
            colour=discord.Colour.dark_purple(),
        )
        song_added.set_author(name=track.author)

        queue_text = ""
        if player.playing:
            queue_text = f"Köplats - {queue.index(track) + 1} |"

        song_added.set_footer(
            text=(f"{queue_text} Längd: "
                  f"{time.strftime('%H:%M:%S', time.gmtime(track.length / 1000))}"
            )
        )
        return song_added

    async def list_added(
        self,
        query: str,
        playlist: wavelink.Playlist,
        queue: wavelink.player.Queue,
        member: discord.Member,
        count: int,
        player: wavelink.Player = None
    ) -> discord.Embed:
        """Creates the list added embed"""

        # If query is typod but still found, try to remedy and grab link.
        query = max(query.split(), key = len)

        playlist_duration = 0
        for track in playlist:
            playlist_duration += track.length

        for i, track in enumerate(playlist):
            if playlist[i - 1].author != track.author:
                authors = "Flera artister"
                break
            else:
                authors = track.author
        
        list_added = discord.Embed(
            title=playlist.name,
            description=f"Begärd av {member.mention}",
            url=query,
            colour=discord.Colour.dark_purple(),
        )
        list_added.set_author(name=authors)

        queue_text = ""
        if player.playing:
            queue_text = f"Köplats - {queue.index(track) + 1} |"

        list_added.set_footer(
            text=(f"{queue_text} Längd: "
                f"{time.strftime('%H:%M:%S', time.gmtime(playlist_duration / 1000))} | "
                f"{count} låtar"
            )
        )
        return list_added

    async def user_not_in_channel(self) -> discord.Embed:
        """Creates user not in channel embed"""

        user_not_in_channel = discord.Embed(
            title="Du är inte kopplad till någon kanal",
            description=(f"Koppla dig till en kanal innan du hämtar "
                         f"{self.client.user.mention}"
            ),
            colour=discord.Colour.dark_purple(),
        )
        return user_not_in_channel

    async def not_in_channel(self) -> discord.Embed:
        """Creates not in channel embed"""

        not_in_channel = discord.Embed(
            title=f"{self.client.user.mention} är inte kopplad till någon kanal",
            description=f"Använd /play för att hämta {self.client.user.mention}",
            colour=discord.Colour.dark_purple(),
        )
        return not_in_channel

    async def not_same_channel(self, vc: wavelink.Player) -> discord.Embed:
        """Creates the not in same channel embed"""

        not_same_channel = discord.Embed(
            title="Vi är inte i samma kanal",
            description=f"{self.client.user.mention} befinner sig i {vc.channel.mention}",
            colour=discord.Colour.dark_purple(),
        )
        return not_same_channel

    async def queue_show(
        self,
        ctx: discord.ApplicationContext,
        player: wavelink.Player
    ):
        """Creates the show queue embed"""
    
        track_titles = []
        for i, track_title in enumerate(player.queue):
            track_titles.append(track_title)

        tracks = []
        for i, track in enumerate(player.queue):
            tracks.append(track)
        
        tracks_artists_ids = []
        embeds = []
        pages = []

        song_strings = (f"Spelas nu:\n[{player.current.title}]({player.current.uri})"
                        f" av {player.current.author}\n\nUppkommande:\n"
        )
        # Adds strings to tracks_artists_ids for use in queue pages
        for i in range(len(tracks)):
            tracks_artists_ids.append(
                f"**{(i + 1)}.** [{track_titles[i]}]({tracks[i].uri})"
                f" av {tracks[i].author}\n\n"
            )
        for i in range(len(tracks_artists_ids)):
            song_strings += tracks_artists_ids[i]

            # Makes one embed per 10 tracks
            if (i + 1) % 10 == 0:
                embeds.append(
                    discord.Embed(
                        title=f"Antal låtar i kön: {len(player.queue)}",
                        description=song_strings,
                        type="link",
                        colour=discord.Colour.dark_purple(),
                    )
                )
                song_strings = ""
        # Adds the last songs if the condition (i + 1) % 10 == 0 isn't met
        if song_strings != "":
            embeds.append(
                discord.Embed(
                    title=f"Antal låtar i kön: {len(player.queue)}",
                    description=song_strings,
                    type="link",
                    colour=discord.Colour.dark_purple(),
                )
            )
        for page in embeds:
            pages.append(Page(embeds=[page]))
        
        paginator = Paginator(pages=pages, timeout=300)

        paginator.add_button(PaginatorButton("first", label="<<", style=discord.ButtonStyle.gray))
        paginator.add_button(PaginatorButton("prev", label="<", style=discord.ButtonStyle.gray))
        paginator.add_button(PaginatorButton("page_indicator", style=discord.ButtonStyle.gray, disabled=True))
        paginator.add_button(PaginatorButton("next", label=">", style=discord.ButtonStyle.gray))
        paginator.add_button(PaginatorButton("last", label=">>", style=discord.ButtonStyle.gray))

        return await paginator.respond(ctx)
    
    async def reset_embeds(self):
        """Removes all embeds"""

        EMBEDS = {}


def setup(client: commands.Bot) -> None:
    """Setup cog"""

    client.add_cog(CreateEmbed(client))
