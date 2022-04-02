import os

import discord

from constants import DEBUG_GUILDS
from utils.config import TokenConfig


class Client(discord.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(debug_guilds=DEBUG_GUILDS, intents=intents, auto_sync_commands=True)

    async def on_ready(self):
        print("-" * 50)
        print(f"We have logged in as {self.user} with ID: {self.user.id}")
        print("-"*50)


client = Client()


if __name__ == "__main__":
    from handlers import client
    cogs_path = "cogs"
    for filename in os.listdir(cogs_path):
        if filename.endswith(".py"):
            client.load_extension(f"{cogs_path}.{filename[:-3]}")
    client.run(TokenConfig.DC_TOKEN)
