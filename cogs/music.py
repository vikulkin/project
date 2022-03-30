import discord
from discord.commands import slash_command
from discord.ext import commands

from bot_storage.storage import BotStorage, Queue
from constants import VK_URL_PREFIX, FFMPEG_OPTIONS, REPEAT_MODES_STR
from exceptions.custrom_exceptions import UserVoiceException, SelfVoiceException
from utils.commands_utils import join_channel
from utils.embed_utils import Embeds
from vk_parsing.main import get_request, find_tracks_by_name


class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.storage = BotStorage(self.client)

    @slash_command(name="player", description="Get player for current playlist")
    async def playlist_command(self, ctx):
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
            return

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(next_track["url"],
                                   **FFMPEG_OPTIONS)
        )
        voice.play(
            source=source, after=lambda e: self._play_next(e, ctx)
        )

    @slash_command(name="play", description="Play tracks from VK playlist")
    async def play_command(self, ctx,
                           link: discord.Option(str, "Playlist link", required=True)):
        if VK_URL_PREFIX not in link:
            embed = Embeds.music_embed(description="Incorrect link")
            return await ctx.respond(embed=embed)

        if ctx.voice_client is None or ctx.voice_client.channel != ctx.author.voice.channel:
            voice = await join_channel(ctx)
        else:
            voice = ctx.voice_client

        await ctx.defer()
        parsed_items = await get_request(link)

        # TODO >> вынести в отдельную функцию

        storage_queue = Queue(ctx.guild.id)
        storage_queue.add_tracks(parsed_items)

        self.storage.add_queue(storage_queue, ctx.guild.id)

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(parsed_items[0]["url"], **FFMPEG_OPTIONS)
        )

        voice.play(
            source=source, after=lambda e: self._play_next(e, ctx)
        )

        embed = Embeds.music_embed(title=f"Now playing in {voice.channel}",
                                   description=f"{parsed_items[0]['name']}")

        await ctx.respond(embed=embed)

    @slash_command(name="search", description="Find track by name")
    async def search_command(self, ctx,
                             query: discord.Option(str, "Search query", required=True)):

        if ctx.voice_client is None or ctx.voice_client.channel != ctx.author.voice.channel:
            voice = await join_channel(ctx)
        else:
            voice = ctx.voice_client

        await ctx.defer()
        try:
            tracks = await find_tracks_by_name(query)
        except:  # TODO выяснить что там за ошибки могут быть
            embed = Embeds.error_embed(description=f"Error occurred while parsing your request: {query}")
            return await ctx.respond(embed=embed)

        if tracks is None:
            embed = Embeds.error_embed(title="Tracks can't be found",
                                       description=f"Can't find tracks with request: **{query}**")
            return await ctx.reposnd(embed=embed)
        tracks_str = ""
        for i, track in enumerate(tracks):
            tracks_str += f"**{i}. {track['name']}**\n"

        # TODO delete VVV this VVV
        tracks_str += "Playing first one (choose is coming..)"

        embed = Embeds.music_embed(title=f"Query: {query}",
                                   description=tracks_str)
        await ctx.respond(embed=embed)

        # TODO >> вынести в отдельную функцию
        storage_queue = Queue(ctx.guild.id)
        storage_queue.add_tracks(tracks[0])

        self.storage.add_queue(storage_queue, ctx.guild.id)

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(tracks[0]["url"], **FFMPEG_OPTIONS)
        )

        voice.play(
            source=source, after=lambda e: self._play_next(e, ctx)
        )

        embed = Embeds.music_embed(title=f"Now playing in {voice.channel}",
                                   description=f"{tracks[0]['name']}")

        await ctx.respond(embed=embed)

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
                                   description=f"Volume level changed to {level/100} **({level}%)**")

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

    @play_command.before_invoke
    @join_command.before_invoke
    @search_command.before_invoke
    async def ensure_author_voice(self, ctx):
        if not ctx.author.voice:
            raise UserVoiceException

    @leave_command.before_invoke
    @playlist_command.before_invoke
    @skip_command.before_invoke
    @pause_command.before_invoke
    async def ensure_self_voice(self, ctx):
        if ctx.voice_client is None:
            raise SelfVoiceException


def setup(bot):
    bot.add_cog(MusicBot(bot))
