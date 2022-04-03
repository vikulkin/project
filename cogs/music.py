import discord
from discord import SlashCommandGroup
from discord.commands import slash_command
from discord.ext import commands

from bot_storage.storage import BotStorage, Queue
from constants import VK_URL_PREFIX, FFMPEG_OPTIONS, REPEAT_MODES_STR
from exceptions.custrom_exceptions import UserVoiceException, SelfVoiceException, IncorrectLinkException
from utils.commands_utils import join_channel
from utils.embed_utils import Embeds
from vk_parsing.main import get_request, find_tracks_by_name


class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.storage = BotStorage(self.client)

    @slash_command(name="player", description="Get player for current playlist")
    async def player_command(self, ctx):
        embed = self.storage.get_player_embed(ctx)
        if embed is None:
            return
        await ctx.respond(embed=embed)

    @slash_command(name="join", description="Bot join your voice channel")
    async def join_command(self, ctx):
        voice = await join_channel(ctx)

        embed = Embeds.info_embed(description=f"Connected to channel {voice.channel}")
        await ctx.respond(embed=embed)

    @slash_command(name="leave", description="Make bot leave voice channel")
    async def leave_command(self, ctx):
        voice = ctx.voice_client

        if voice.is_connected():
            await voice.disconnect()
        embed = Embeds.info_embed(description=f"Left from channel **{voice.channel}**")

        await ctx.respond(embed=embed, ephemeral=True)

    def _play_next(self, errors, ctx):
        queue: Queue = self.storage.get_queue(ctx.guild.id)

        voice = ctx.voice_client
        if voice is None:
            return

        next_track = queue.get_next_track(reverse=False)
        if next_track is None:
            self.storage.delete_queue(ctx.guild.id)
            return

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(next_track["url"],
                                   **FFMPEG_OPTIONS)
        )
        voice.play(
            source=source, after=lambda e: self._play_next(e, ctx)
        )

    async def add_tracks(self, ctx, tracks):
        if self.storage.get_queue(ctx.guild.id) is None:

            new_queue = Queue(ctx.guild.id)
            new_queue.add_tracks(tracks)
            self.storage.add_queue(new_queue, ctx.guild.id)

            track_to_play = tracks if isinstance(tracks, dict) else tracks[0]

            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(track_to_play["url"], **FFMPEG_OPTIONS)
            )
            source.volume = .5

            voice = ctx.voice_client
            voice.play(
                source=source, after=lambda e: self._play_next(e, ctx)
            )
            await self.player_command(self, ctx)

        else:
            self.storage.add_tracks(ctx.guild.id, tracks)
            if isinstance(tracks, list):
                embed = Embeds.music_embed(description=f"Added {len(tracks)} tracks to queue")
            else:
                embed = Embeds.music_embed(title="Track added to queue",
                                           description=f"**{tracks['name']}**")
            await ctx.respond(embed=embed)

    play_group = SlashCommandGroup("play", "Play commands")

    @play_group.command(name="playlist", description="Play tracks from VK playlist")
    async def playlist_command(self, ctx,
                               link: discord.Option(str, "Playlist link", required=True)):

        await ctx.defer()
        parsed_items = await get_request(link)

        await self.add_tracks(ctx, parsed_items)

    @play_group.command(name="search", description="Find track by name")
    async def search_command(self, ctx,
                             query: discord.Option(str, "Search query", required=True)):

        await ctx.defer()
        try:
            tracks = await find_tracks_by_name(query)
        except:  # TODO выяснить что там за ошибки могут быть
            embed = Embeds.error_embed(description=f"Error occurred while parsing your request: {query}")
            return await ctx.respond(embed=embed)

        if tracks is None:
            embed = Embeds.error_embed(title="Tracks can't be found",
                                       description=f"Can't find tracks with request: **{query}**")
            return await ctx.respond(embed=embed)
        tracks_str = ""
        for i, track in enumerate(tracks):
            tracks_str += f"**{i + 1}. {track['name']}**\n"

        # TODO delete VVV this VVV
        tracks_str += "Playing first one (choose is coming..)"

        embed = Embeds.music_embed(title=f"Query: {query}",
                                   description=tracks_str)
        await ctx.respond(embed=embed)

        await self.add_tracks(ctx, tracks[0])

    @slash_command(name="pause", description="Pause current queue")
    async def pause_command(self, ctx):
        voice = ctx.voice_client
        voice.pause()

        await ctx.respond(embed=Embeds.music_embed(description="Playing paused"))

    @slash_command(name="resume", description="Resume playing")
    async def resume_command(self, ctx):
        voice = ctx.voice_client
        voice.resume()

        await ctx.respond(embed=Embeds.music_embed(description="Continuing playing"))

    @slash_command(name="volume", description="Edit music volume")
    async def volume_command(self, ctx,
                             level: discord.Option(int,
                                                   description="Volume level (1 - 100)",
                                                   required=True,
                                                   min_value=1,
                                                   max_value=100)):

        ctx.voice_client.source.volume = level / 100

        embed = Embeds.music_embed(title="Volume level changed",
                                   description=f"Volume level changed to {level / 100} **({level}%)**")

        await ctx.respond(embed=embed)

    @slash_command(name="repeat", description="Switch repeat mode (None -> One -> All -> None -> ...)")
    async def repeat_command(self, ctx):
        queue = self.storage.get_queue(ctx.guild.id)
        queue.switch_repeat_mode()

        repeat_mode = queue.repeat_mode.value

        rm_str = REPEAT_MODES_STR.get(repeat_mode)

        embed = Embeds.music_embed(title="Repeat mode switched",
                                   description=f"Repeat mode switched to **{rm_str}**")

        await ctx.respond(embed=embed)

    @slash_command(name="skip", description="Skip current track")
    async def skip_command(self, ctx):
        current_track = self.storage.get_queue(ctx.guild.id).current_track
        embed = Embeds.music_embed(title="Track skipped", description=f"{current_track['name']}")
        await ctx.respond(embed=embed)

        voice = ctx.voice_client
        voice.stop()

    @playlist_command.before_invoke
    @join_command.before_invoke
    @search_command.before_invoke
    async def ensure_author_voice(self, ctx):
        if not ctx.author.voice:
            raise UserVoiceException

    @leave_command.before_invoke
    @player_command.before_invoke
    @skip_command.before_invoke
    @pause_command.before_invoke
    async def ensure_self_voice(self, ctx):
        if ctx.voice_client is None:
            raise SelfVoiceException

    @playlist_command.before_invoke
    async def ensure_vk_link(self, ctx):
        link = ctx.args["link"]
        if VK_URL_PREFIX not in link:
            raise IncorrectLinkException

    @playlist_command.before_invoke
    @search_command.before_invoke
    async def ensure_voice_channel(self, ctx):
        if ctx.voice_client is None or ctx.voice_client.channel != ctx.author.voice.channel:
            await join_channel(ctx)


def setup(bot):
    bot.add_cog(MusicBot(bot))
