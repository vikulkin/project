import sys
import traceback

from discord import ApplicationContext, DiscordException

from __main__ import client
from exceptions.custrom_exceptions import SelfVoiceException, UserVoiceException, EmptyQueueException
from utils.embed_utils import Embeds


@client.listen("on_application_command_error")
async def command_error_handler(ctx: ApplicationContext, error: DiscordException):

    if isinstance(error, SelfVoiceException):
        embed = Embeds.error_embed(description="Voice is not connected")
        await ctx.respond(embed=embed, ephemeral=True)

    elif isinstance(error, UserVoiceException):
        embed = Embeds.error_embed(description="You are not connected to the voice channel")
        await ctx.respond(embed=embed, ephemeral=True)

    elif isinstance(error, EmptyQueueException):
        embed = Embeds.error_embed(description="Queue is empty. Nothing is playing")
        await ctx.respond(embed=embed, ephemeral=True)

    else:
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

