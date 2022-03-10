import traceback

from discord import ApplicationContext, DiscordException

from __main__ import client
from exceptions.custrom_exceptions import SelfVoiceException, UserVoiceException
from utils.embed_utils import Embeds


@client.listen("on_application_command_error")
async def command_error_handler(ctx: ApplicationContext, error: DiscordException):

    if isinstance(error, SelfVoiceException):
        embed = Embeds.error_embed(description="Voice is not connected")
        return await ctx.respond(embed=embed, ephemeral=True)

    if isinstance(error, UserVoiceException):
        embed = Embeds.error_embed(description="You are not connected to the voice channel")
        return await ctx.respond(embed=embed, ephemeral=True)

    print(traceback.print_tb(error.__traceback__))  # TODO нормальный вывод
