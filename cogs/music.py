import discord
from discord.commands import slash_command
from discord.ext import commands


class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="join", description="Joins your voice channel")
    async def join_command(self, ctx):
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to()
        else:
            await channel.connect()
        await ctx.respond(f"Connected to {channel}")

    @join_command.before_invoke
    async def ensure_author_voice(self, ctx):
        if not ctx.author.voice:
            raise discord.DiscordException("You are not connected to the voice channel!")


def setup(bot):
    bot.add_cog(MusicBot(bot))
