import discord


class PauseButton(discord.ui.Button):
    def __init__(self, voice, storage):
        self.voice = voice
        self.storage = storage
        super().__init__(
            label="Play/Pause",
            style=discord.ButtonStyle.primary,
            custom_id=f"{voice.guild.id}:pause"
        )

    async def callback(self, interaction):
        if self.voice.is_paused():
            self.voice.resume()
        else:
            self.voice.pause()

        embed = self.storage.get_player_embed(guild_id=interaction.guild_id,
                                              voice_client=interaction.guild.voice_client)
        if embed is None:
            print("embed is None")
            return
        await interaction.response.edit_message(embed=embed)


class SkipButton(discord.ui.Button):
    def __init__(self, voice, storage):
        self.voice = voice
        self.storage = storage
        super().__init__(
            label="Skip",
            style=discord.ButtonStyle.primary,
            custom_id=f"{voice.guild.id}:skip"
        )

    async def callback(self, interaction):
        self.voice.stop()
        embed = self.storage.get_player_embed(guild_id=interaction.guild_id,
                                              voice_client=interaction.guild.voice_client)
        if embed is None:
            print("embed is None")
            return
        await interaction.response.edit_message(embed=embed)


class RepeatButton(discord.ui.Button):
    def __init__(self, voice, storage):
        self.voice = voice
        self.storage = storage
        super().__init__(
            label="RepeatMode",
            style=discord.ButtonStyle.primary,
            custom_id=f"{voice.guild.id}:repeat_mode"
        )

    async def callback(self, interaction):
        queue = self.storage.get_queue(self.voice.guild.id)
        queue.switch_repeat_mode()

        embed = self.storage.get_player_embed(guild_id=interaction.guild_id,
                                              voice_client=interaction.guild.voice_client)
        if embed is None:
            print("embed is None")
            return
        await interaction.response.edit_message(embed=embed)