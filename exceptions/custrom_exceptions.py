from discord import DiscordException


class SelfVoiceException(DiscordException):
    pass


class UserVoiceException(DiscordException):
    pass


class EmptyQueueException(DiscordException):
    pass
