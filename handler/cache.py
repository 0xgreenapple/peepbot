"""
:Author: 0xgreenapple(xgreenpple)
:Copyright: (c) 2022-present 0xgreenapple
:Licence: MIT.
"""
from collections import UserDict, defaultdict
from datetime import timedelta
from typing import Optional


class Max_item_reached(Exception):
    def __str__(self):
        return f'maximum number of values has been reached'


class Cache(defaultdict):

    def __init__(
            self,
            max_values: int = 2000):
        super().__init__(dict)
        self.max_values = max_values
        self.recent_value = None
        self.max_time = None

    def __setitem__(self, key, value):
        if len(self.items()) > self.max_values:
            raise Max_item_reached()
        self.recent_value = {key: value}
        return super().__setitem__(key, value)

    def get(self, key):
        return self.__getitem__(key)

    def set(self, key, value):
        return self.__setitem__(key, value)

    def get_item_named(self, name: str):
        return self.get(name)

    @property
    def size(self):
        return len(self.items())

    def clean_up(self):
        return self.clear()


class GuildCache(Cache):
    """ subclass of dict object """

    def __init__(self):
        super().__init__()
        super().__setitem__('guilds', value={})
        self.guilds: dict = super().get("guilds")

    def set_guild(self, guild_id: int):
        return self.guilds.setdefault(guild_id, {})

    def get_guild(self, guild_id) -> Optional[dict]:
        cached_guild = self.guilds.get(guild_id)
        if cached_guild is None:
            self.set_guild(guild_id=guild_id)
            return self.guilds.get(guild_id)
        return cached_guild

    def get_from_guild(self, guild_id: int, key) -> Optional[any]:
        cache_guild = self.get_guild(guild_id=guild_id)
        if cache_guild is None:
            self.set_guild(guild_id=guild_id)
            return None
        return cache_guild.get(key)

    def insert_into_guild(self, guild_id: int, key: any, value: any):
        cached_guild = self.get_guild(guild_id=guild_id)
        cached_guild[key] = value

    def get_channels(self, guild_id) -> dict:
        channels = self.get_from_guild(guild_id=guild_id, key="channels")
        if channels is None:
            guild = self.get_guild(guild_id=guild_id)
            channels = guild['channels'] = {}
        return channels

    def get_channel(self, channel_id: int, guild_id: int) -> dict:
        channels = self.get_channels(guild_id=guild_id)
        channel = channels.get(channel_id)
        if channel is None:
            channel = channels[channel_id] = {}
        return channel

    def get_completed_messages(self, channel_id: int, guild_id: int):
        channel = self.get_channel(guild_id=guild_id, channel_id=channel_id)
        meme_messages = channel.get("meme_completed_messages")
        return meme_messages

    def append_completed_message(
        self, message_id: int, channel_id: int, guild_id: int
    ):
        completed_messages = self.get_completed_messages(
            channel_id=channel_id, guild_id=guild_id)
        completed_messages.append(message_id)
