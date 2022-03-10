from discord import ApplicationContext, DiscordException

from __main__ import client


@client.listen("on_application_command_error")
async def command_error_handler(ctx: ApplicationContext, error: DiscordException):
    await ctx.respond(error)
