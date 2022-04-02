import discord

from bot_storage.utils.enums import RepeatModes
from exceptions.custrom_exceptions import EmptyQueueException
from utils.embed_utils import Embeds


class Queue:
    def __init__(self, guild_id):
        self._guild_id = guild_id
        self._tracks = []
        self.current_index = 0
        self._repeat_mode = RepeatModes.NONE

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

    def get_player_embed(self, ctx):

        queue: Queue = self.get_queue(ctx.guild_id)
        if queue is None:
            raise EmptyQueueException

        current_index = queue.current_index

        volume = ctx.voice_client.source.volume * 100

        embed = Embeds.music_embed(
            title=f"Player in {ctx.voice_client.channel.name}",
            description=f"Tracks in queue: {len(queue)}\n"
                        f"Volume: **{volume}%**\n"
        )

        if current_index - 1 >= 0:
            embed.add_field(
                name="Previous track",
                value=f"**{current_index}. {queue.tracks[current_index - 1]['name']}**\n",
                inline=False
            )
        embed.add_field(
            name="Now playing",
            value=f"**{current_index + 1}. {queue.tracks[current_index]['name']}**\n",
            inline=False
        )

        if current_index + 1 < len(queue):
            embed.add_field(
                name="Next track",
                value=f"**{current_index + 2}. {queue.tracks[current_index + 1]['name']}**\n",
                inline=False
            )
        embed.set_thumbnail(url=queue.tracks[current_index]["thumbnail"])

        return embed
