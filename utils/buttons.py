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
        self.voice = interaction.guild.voice_client
        if self.voice.is_paused():
            self.voice.resume()
        else:
            self.voice.pause()

        await self.storage.update_message(interaction.guild.id)


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
        self.voice = interaction.guild.voice_client

        self.voice.stop()
        if self.voice is None:
            return

        await self.storage.update_message(interaction.guild.id)


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
        self.voice = interaction.guild.voice_client

        queue = self.storage.get_queue(self.voice.guild.id)
        queue.switch_repeat_mode()

        await self.storage.update_message(interaction.guild.id)


class VolumeUpButton(discord.ui.Button):
    def __init__(self, voice, storage):
        self.voice = voice
        self.storage = storage
        super().__init__(
            label="VolumeUp",
            style=discord.ButtonStyle.primary,
            custom_id=f"{voice.guild.id}:volume_up"
        )

    async def callback(self, interaction):
        self.voice = interaction.guild.voice_client

        volume_level = self.voice.source.volume * 100
        if volume_level == 100:
            return

        volume_level += 10
        if volume_level > 100:
            volume_level = 100

        self.voice.source.volume = volume_level / 100

        await self.storage.update_message(interaction.guild.id)


class VolumeDownButton(discord.ui.Button):
    def __init__(self, voice, storage):
        self.voice = voice
        self.storage = storage
        super().__init__(
            label="VolumeDown",
            style=discord.ButtonStyle.primary,
            custom_id=f"{voice.guild.id}:volume_down"
        )

    async def callback(self, interaction):
        self.voice = interaction.guild.voice_client

        volume_level = self.voice.source.volume * 100
        if volume_level == 1:
            return

        volume_level -= 10
        if volume_level < 1:
            volume_level = 1

        self.voice.source.volume = volume_level / 100

        await self.storage.update_message(interaction.guild.id)


class StopButton(discord.ui.Button):
    def __init__(self, voice, storage):
        self.voice = voice
        self.storage = storage
        super().__init__(
            label="Stop",
            style=discord.ButtonStyle.primary,
            custom_id=f"{voice.guild.id}:stop"
        )

    async def callback(self, interaction):
        self.voice = interaction.guild.voice_client

        self.storage.delete_queue(self.voice.guild.id)
        self.voice.stop()
