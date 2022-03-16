import discord
from discord.commands import slash_command
from discord.ext import commands

from constants import VK_URL_PREFIX, FFMPEG_OPTIONS
from exceptions.custrom_exceptions import UserVoiceException, SelfVoiceException
from utils.commands_utils import join_channel
from utils.embed_utils import Embeds
from vk_parsing.main import get_request


class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="join", description="Joins your voice channel")
    async def join_command(self, ctx):
        voice = await join_channel(ctx)

        embed = Embeds.info_embed(description=f"Connected to channel {voice.channel}")
        await ctx.respond(embed=embed)

    @slash_command(name="leave", description="Make bot leave voice channel")
    async def leave_command(self, ctx):

        voice: discord.VoiceClient = ctx.voice_client

        if voice.is_connected():
            await voice.disconnect()
        embed = Embeds.info_embed(description=f"Left from channel **{voice.channel}**")

        await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(name="play", description="Play tracks from VK playlist")
    async def play_command(self, ctx,
                           request: discord.Option(str, "Playlist link", required=True)):
        if VK_URL_PREFIX not in request:
            embed = Embeds.music_embed(description="Incorrect link")
            return await ctx.respond(embed=embed)

        if ctx.voice_client is None or ctx.voice_client.channel != ctx.author.voice.channel:
            voice = await join_channel(ctx)
        else:
            voice = ctx.voice_client

        await ctx.defer()
        parsed_items = await get_request(request)
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(parsed_items[0]["url"], **FFMPEG_OPTIONS))
        # source = await discord.FFmpegOpusAudio.from_probe(
        #     parsed_items[0]["url"], **FFMPEG_OPTIONS
        # )
        voice.play(
            source=source
        )
        # voice.play(source=source, after=lambda e: ...)

        embed = Embeds.music_embed(title=f"Now playing in {voice.channel}",
                                   description=f"{parsed_items[0]['name']}")

        await ctx.respond(embed=embed)

    @play_command.before_invoke
    @join_command.before_invoke
    async def ensure_author_voice(self, ctx):
        if not ctx.author.voice:
            raise UserVoiceException

    @leave_command.before_invoke
    async def ensure_self_voice(self, ctx):
        if ctx.voice_client is None:
            raise SelfVoiceException


def setup(bot):
    bot.add_cog(MusicBot(bot))
