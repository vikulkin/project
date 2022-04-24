import os

import discord

from constants import DEBUG_GUILDS
from utils.config import TokenConfig

import sqlite3


class Client(discord.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(debug_guilds=DEBUG_GUILDS, intents=intents, auto_sync_commands=True)
        self.db = None
        self.cursor = None

    def connect_db(self):
        db = sqlite3.connect("player.db")
        cursor = db.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS guild (
            id BIGINT,
            repeatMode INTEGER,
            volume INTEGER
            )""")
        db.commit()
        self.db = db
        self.cursor = cursor

    async def on_ready(self):
        self.connect_db()
        print("-" * 50)
        print(f"We have logged in as {self.user} with ID: {self.user.id}")
        print("-"*50)

    async def on_guild_join(self, guild):
        self.cursor.execute(f"SELECT id FROM guild WHERE id = {guild.id}")
        if self.cursor.fetchone() is not None:
            return
        self.cursor.execute(f"INSERT INTO guild VALUES ({guild.id}, 0, 50)")
        self.db.commit()

    async def on_guild_remove(self, guild):
        self.cursor.execute(f"SELECT id FROM guild WHERE id = {guild.id}")
        if self.cursor.fetchone() is None:
            return
        self.cursor.execute(f"DELETE FROM guild WHERE id = {guild.id}")
        self.db.commit()


client = Client()


if __name__ == "__main__":
    from handlers import client
    cogs_path = "cogs"
    for filename in os.listdir(cogs_path):
        if filename.endswith(".py"):
            client.load_extension(f"{cogs_path}.{filename[:-3]}")
    client.run(TokenConfig.DC_TOKEN)
