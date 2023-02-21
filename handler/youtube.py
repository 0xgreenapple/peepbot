"""
:Author: 0xgreenapple
:Licence: MIT
:Copyright: (C) 2022-present 0xgreenapple
"""
from __future__ import annotations

import datetime
import os
import re
import logging
import base64
import json
from typing import Optional, Union, List, TYPE_CHECKING

import discord
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from discord.ext import tasks
from handler.database import Database, get_guild_settings
from handler.blocking_code import Executor
if TYPE_CHECKING:
    from pepebot import PepeBot

_log = logging.getLogger("youtube")
from discord.ext.commands import Context


class EnvironmentNotFound(Exception):
    """ raised when tokens not found at given environment variable"""
    pass


class MissingTokens(Exception):
    """ raised when tokens not found at given environment variable"""
    pass


class CredentialsNotReady(Exception):
    """ raised when api tokens is not ready or not is authorised"""
    pass


class YoutubeAuth:
    def __init__(self, dev_key: str = None, public_access: bool = False):
        self.is_authorised = False
        self.is_tokens_ready = False
        self.database: Optional[Database] = None
        self.dev_key = dev_key
        self.__refresh_token: Optional[str] = None
        self.__api_key: Optional[str] = None
        self.__access_token: Optional[str] = None
        self.__client_secret: Optional[str] = None
        self.__client_id: Optional[str] = None
        self.__expiring_on: Optional[str] = None
        self.default_token_file: str = "token.json"
        self.tokens_file: Optional[Union[os.PathLike, str]] = None

        self.__credentials: Optional[Credentials] = None
        self.token_url = "https://oauth2.googleapis.com/token"
        self.default_scope = "https://www.googleapis.com/auth/youtube.readonly"
        self.scopes: list[str] = [self.default_scope]
        self.tokens_environment_key: str = "YOUTUBE_API_TOKENS_B64"

    def authorize(self):
        if not self.is_tokens_ready:
            if self.tokens_file is not None:
                self.get_tokens_from_file()
            else:
                self.get_tokens_from_env()
            if not self.is_tokens_ready:
                raise MissingTokens(
                    "pls provide credentials using ``attach file``")
        self.__credentials = Credentials.from_authorized_user_info(
            self.get_formatted_tokens()
        )
        if not self.__credentials.valid:
            self.renew_credentials()
        self.is_authorised = True

    def renew_credentials(self):
        try:
            self.__credentials.refresh(Request())
            self.attach_tokens(
                **json.loads(self.__credentials.to_json()))
            self.append_tokens_to_file()
        except RefreshError as error:
            if not error.retryable:
                # TODO: log to channel to get new tokens
                return
            self.__credentials.refresh()

    def attach_tokens(
            self, refresh_token: str, token: str, client_secret: str,
            client_id: str, expiry: str = None, token_uri: str = None,
            scopes: List[str] = None
    ) -> dict:
        self.__refresh_token = refresh_token
        self.__access_token = token
        self.__client_id = client_id
        self.__client_secret = client_secret
        if token_uri is not None:
            self.token_url = token_uri
        if expiry is not None:
            print(expiry)
            self.__expiring_on = expiry
        if scopes is not None and len(scopes) > 0:
            self.scopes = scopes
        if all([self.__refresh_token, self.__client_id, self.__client_secret]):
            self.is_tokens_ready = True
        return self.get_formatted_tokens()

    def get_tokens_from_env(self):
        base64_token_string = os.environ.get(self.tokens_environment_key)
        if base64_token_string is None:
            raise EnvironmentNotFound(
                f"the variable at location {self.tokens_environment_key}"
                f"not found")
        decoded_base64_string = json.loads(
            self.decode_b64_tokens(base64_token_string))
        self.attach_tokens(**decoded_base64_string)
        return decoded_base64_string

    def get_tokens_from_file(self):
        with open(file=self.tokens_file, mode="r") as token_file:
            token_json = json.loads(token_file.read())
            self.attach_tokens(**token_json)
            return token_json

    @staticmethod
    def decode_b64_tokens(b64_tokens: str) -> Optional[dict | str]:
        decode_string = base64.b64decode(b64_tokens).decode("utf-8")
        return json.loads(decode_string)

    def get_formatted_tokens(self):
        formatted_tokens = {
            "token": self.__access_token,
            "refresh_token": self.__refresh_token,
            "client_id": self.__client_id,
            "client_secret": self.__client_secret,
            "scopes": self.scopes,
            "token_uri": self.token_url,
            "expiry": self.__expiring_on
        }
        return formatted_tokens

    def append_tokens_to_file(self, filename: str = None):
        token_json_str = json.dumps(self.get_formatted_tokens())
        if filename is not None:
            self.tokens_file = filename
        else:
            self.tokens_file = self.default_token_file
        with open(file=self.tokens_file, mode="w+") as token_file:
            token_file.write(token_json_str)

    def get_credentials(self) -> Credentials:
        if not self.is_authorised or not self.is_tokens_ready:
            raise CredentialsNotReady()
        return self.__credentials


class Youtube:
    def __init__(self, bot: PepeBot, public_access: bool = False,
                 dev_key: str = None):
        self.auth = YoutubeAuth(
            public_access=public_access, dev_key=dev_key)
        self.operational_api = "https://yt.lemnoslife.com/"
        self.public_access = public_access
        self.bot = bot
        self.executor = self.bot.executor
        self.name = "youtube"
        self.api_version_name = "v3"
        self.app = None
        self.channel_custom_url_regex = re.compile(
            "(?:https?:\/\/)?(?:www\.)?youtube\.com\/(""?:@|c\/|user\/)?(\w+)(?:\/.*)?$")
        self.channel_id_url_regex = re.compile(
            "^https?://(?:www\.)?youtube\.com/channel/([\w-]+)$")

    @staticmethod
    def get_valid_iso_formate(iso_string: str):
        if iso_string.endswith("Z"):
            slice_obj = slice(-1)
            iso_string = iso_string[slice_obj]
        return datetime.datetime.fromisoformat(iso_string)

    async def initialise(self):
        if self.public_access and self.auth.dev_key is not None:
            self.app = await self.executor.execute(
                build, self.name, self.api_version_name,
                developerKey=self.auth.dev_key)
            return
        if not self.auth.is_authorised:
            await self.executor.execute(self.auth.authorize)
        self.app = await self.executor.execute(
            build, self.name, self.api_version_name,
            credentials=self.auth.get_credentials())

    async def get_playlist(self, playlist_id: str):
        playlist = await self.executor.execute(
            self.app.playlistItems().list(
                playlistId=playlist_id,
                part="snippet, contentDetails"
            ).execute)
        return playlist["items"][0]

    async def get_channel_by_name(self, channel_name: str):
        channel_response = await self.executor.execute(
            self.app.channels().list(
                part="snippet,contentDetails",
                forUsername=channel_name
            ).execute)
        return channel_response["items"][0]

    async def get_channel_by_id(self, channel_id: str):
        channel_response = await self.executor.execute(
            self.app.channels().list(
                part="snippet,contentDetails",
                id=channel_id
            ).execute)
        return channel_response["items"][0]

    async def get_channel_id(self, channel_user_name: str):
        if not channel_user_name.startswith("@"):
            channel_user_name = "@"+channel_user_name
        params = {"handle": channel_user_name}
        response = await self.bot.aiohttp_session.get(
            url=self.operational_api + "channels",
            params=params
        )
        json_obj = await response.json()
        print(json_obj)
        return json_obj["items"][0]["id"]

    async def get_recent_upload(self, channel_name: str,
                                channel_id: str = None):
        if channel_id is not None:
            channel = await self.get_channel_by_id(channel_id=channel_id)
        else:
            channel = await self.get_channel_by_name(channel_name)
        upload_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        return await self.get_playlist(upload_id)

    async def get_video(self, video_id: str):
        video = await self.executor.execute(
            self.app.videos().list(
                part="contentDetails,snippet",
                id=video_id
            ).execute)
        return video["items"][0]

    async def append_new_video(self, channel_id, guild_id, upload_id):
        await self.bot.database.update(
            channel_id,
            guild_id,
            upload_id,
            table="peep.youtube_uploads",
            condition="channel_id=$1 AND guild_id = $2",
            update_set="recent_upload_id=$3"
        )

    async def subscribe_to_channel(self, channel_id, guild_id, upload_id):
        await self.bot.database.insert(
            channel_id,
            guild_id,
            upload_id,
            table="peep.youtube_uploads",
            columns="channel_id,guild_id,recent_upload_id",
            values="$1,$2,$3",
            on_conflicts=
            "(guild_id) DO UPDATE SET "
            "channel_id = $1,recent_upload_id =$3"
        )

    async def unsubscribe_to_channel(self, guild_id):
        await self.bot.database.delete(
            guild_id,
            table="peep.youtube_uploads",
            condition="guild_id = $1"
        )

    async def get_subscribed_channel(self, chanel_id, guild_id):
        return await self.bot.database.select(
            chanel_id,
            guild_id,
            table_name="peep.youtube_uploads",
            columns="*",
            conditions="channel_id = $1 AND guild_id = $2"
        )

    async def get_subscribed_for_guilds(self, guild_id: str):
        return await self.bot.database.select(
            guild_id,
            table_name="peep.youtube_uploads",
            columns="channel_id",
            conditions="guild_id=$1",
        )

    def get_id_from_url(self, url: str):
        url = url.replace(" ", "")
        all_ids = self.channel_id_url_regex.findall(url)
        if len(all_ids) >= 1:
            return all_ids[0]
        return None

    def get_username_from_url(self, url: str):
        url = url.replace(" ", "")
        all_usernames = self.channel_custom_url_regex.findall(url)
        if len(all_usernames) >= 1:
            return all_usernames[0]
        return None

    @tasks.loop(seconds=60)
    async def watch_for_uploads(self):
        print(1)
        """ watch for new uploads from channels containing in the database """

        channels = self.bot.cache["uploads"] = (
            await self.bot.database.select(
                table_name="peep.youtube_uploads", columns="*",
                return_all_rows=True
            )
        )
        # check again for the data returned from database
        if channels is None or len(channels) == 0:
            return

        for channel_data in channels:
            # get channel metadata
            channel_id = channel_data["channel_id"]
            channel_name = channel_data["channel_name"]
            channel_guild = channel_data["guild_id"]
            last_uploaded_video_id = channel_data["recent_upload_id"]

            # get recent uploads from the channel and get id
            recent_uploads = await self.get_recent_upload(
                channel_name=channel_name, channel_id=channel_id)
            recent_upload_id = recent_uploads["contentDetails"]["videoId"]

            if last_uploaded_video_id is None:
                print("appending")
                await self.append_new_video(
                    channel_id=channel_id,
                    guild_id=channel_guild,
                    upload_id=recent_upload_id
                )
                return
            if last_uploaded_video_id == recent_upload_id:
                return
            await self.append_new_video(
                channel_id=channel_id, guild_id=channel_guild,
                upload_id=recent_upload_id
            )
            # add get and set algorithm, to prevent from making everytime
            cached_channels = self.bot.cache.get(key="youtube_channels")
            cache_channel = cached_channels.get(channel_id)
            if cache_channel is None:
                cache_channel = await self.get_channel_by_id(channel_id)
                cached_channels[channel_id] = cache_channel
            self.bot.dispatch(
                "new_video_upload", channel_guild, cache_channel,
                recent_uploads
            )
