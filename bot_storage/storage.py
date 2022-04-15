from bot_storage.utils.enums import RepeatModes
from exceptions.custrom_exceptions import EmptyQueueException
from utils.embed_utils import Embeds
from utils.views import PlayerView
from vk_parsing.utils import time_format


class Queue:
    def __init__(self, guild_id):
        self._guild_id = guild_id
        self._tracks = []
        self.current_index = 0
        self._repeat_mode = RepeatModes.NONE
        self.player_message = None

    def __bool__(self):
        return bool(self._tracks)

    def __len__(self):
        return len(self._tracks)

    @property
    def tracks(self):
        return self._tracks

    @property
    def guild_id(self):
        return self.guild_id

    @property
    def repeat_mode(self):
        return self._repeat_mode

    @property
    def current_track(self):
        return self._tracks[self.current_index]

    async def update_message(self, message):
        if self.player_message is not None:
            try:
                await self.player_message.delete()
            except:
                pass
        self.player_message = message

    def add_tracks(self, tracks):
        if isinstance(tracks, dict):
            self._tracks.append(tracks)
        else:
            self._tracks.extend(tracks)

    def get_next_track(self, reverse=False):
        if self._repeat_mode == RepeatModes.ONE:
            return self._tracks[self.current_index]

        if reverse:
            self.current_index -= 1
        else:
            self.current_index += 1

        if self.current_index >= len(self):

            if self.repeat_mode == RepeatModes.NONE:
                self._tracks.clear()
                return
            elif self.repeat_mode == RepeatModes.ALL:
                self.current_index = 0

        elif self.current_index < 0:
            if self.repeat_mode == RepeatModes.ALL:
                self.current_index = len(self) - 1
            elif self.repeat_mode == RepeatModes.NONE:
                self._tracks.clear()
                return

        return self._tracks[self.current_index]

    def switch_repeat_mode(self):
        current_mode = self._repeat_mode.value
        current_mode += 1
        if current_mode > 2:
            current_mode = 0
        self._repeat_mode = RepeatModes(current_mode)
        return self._repeat_mode


class BotStorage:
    def __init__(self, client):
        self.client = client
        self.queues = dict()

    def add_tracks(self, guild_id, tracks):
        queue = self.queues.get(guild_id)
        if queue is None:
            return
        queue.add_tracks(tracks)

    def add_queue(self, queue, guild_id):
        self.queues[guild_id] = queue

    def get_queue(self, guild_id):
        return self.queues.get(guild_id)

    def delete_queue(self, guild_id):
        if guild_id in self.queues:
            del self.queues[guild_id]

    def get_player_embed(self, guild_id, voice_client):

        queue = self.get_queue(guild_id)
        if queue is None:
            raise EmptyQueueException

        current_index = queue.current_index

        volume = voice_client.source.volume * 100

        paused_str = f"```{'⏸ Paused' if voice_client.is_paused() else '▶ Playing'}```"

        embed = Embeds.music_embed(
            title=f"🎧 Player in {voice_client.channel.name}",
            description=f"📃 Tracks in queue: **{len(queue)}**\n"
                        f"🔊 Volume: **{volume}%**\n"
                        f"{paused_str}\n"
        )

        if current_index - 1 >= 0:
            previous_track = queue.tracks[current_index - 1]
            previous_track_duration = time_format(previous_track["duration"])

            embed.add_field(
                name="Previous track",
                value=f"**{current_index}. {previous_track['name']}** {previous_track_duration}\n",
                inline=False
            )

        current_track = queue.tracks[current_index]
        current_track_duration = time_format(current_track["duration"])
        embed.add_field(
            name="Current track",
            value=f"**{current_index + 1}. {current_track['name']}** {current_track_duration}\n",
            inline=False
        )

        if current_index + 1 < len(queue):
            next_track = queue.tracks[current_index + 1]
            next_track_duration = time_format(next_track["duration"])

            embed.add_field(
                name="Next track",
                value=f"**{current_index + 2}. {next_track['name']}** {next_track_duration}\n",
                inline=False
            )
        embed.set_thumbnail(url=queue.tracks[current_index]["thumbnail"])

        return embed

    async def send_message(self, ctx):
        embed = self.get_player_embed(ctx.guild_id, ctx.voice_client)
        if embed is None:
            return
        view = PlayerView(ctx.voice_client, self)
        message = await ctx.respond(embed=embed, view=view)
        queue = self.get_queue(ctx.guild_id)

        await queue.update_message(message)

    async def update_message(self, guild_id):
        queue = self.get_queue(guild_id)
        if queue is None:
            return
        voice = self.client.get_guild(guild_id).voice_client
        embed = self.get_player_embed(guild_id, voice)
        if embed is None:
            return
        await queue.player_message.edit(embed=embed)
