"""
:Author: 0xgreenapple
:Licence: MIT
:Copyright: (C) 2022-present 0xgreenapple
"""
from __future__ import annotations

import datetime
import os
import logging
import base64
import json
from typing import Optional, Union, List, TYPE_CHECKING

from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from discord.ext import tasks
from handler.database import Database
from handler.blocking_code import Executor

if TYPE_CHECKING:
    from pepebot import PepeBot

_log = logging.getLogger("pepebot")


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
        self.public_access = public_access
        self.bot = bot
        self.executor = self.bot.executor
        self.name = "youtube"
        self.api_version_name = "v3"
        self.app = None

    def _run_in_executor(self, func):
        async def wrapper(*args, **kwargs):
            return await self.executor.loop.run_in_executor(
                self.executor.thread_pool_executor,
                lambda: func(*args, **kwargs)
            )

        return wrapper

    @staticmethod
    def _get_valid_iso_formate(iso_string: str):
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
        print(channel_response)
        return channel_response["items"][0]

    async def get_channel_by_id(self, channel_id: str):
        channel_response = await self.executor.execute(
            self.app.channels().list(
                part="snippet,contentDetails",
                id=channel_id
            ).execute)
        return channel_response["items"][0]

    async def get_channel_id(self, channel_id: str):
        channel = await self.get_channel_by_name(
            channel_name=channel_id)
        return channel[0]["id"]

    async def get_recent_upload(self, channel_name: str,
                                channel_id: str = None):
        if channel_id is not None:
            channel = await self.get_channel_id(channel_id=channel_id)
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

    @tasks.loop(seconds=30)
    async def watch_for_uploads(self):
        # channels_from_database = self.bot.cache.get("uploads")
        # if channels_from_database is None:
        #     channels_from_database = await self.bot.database.select(
        #         table_name="peep.youtube_uploads",
        #         columns="*"
        #     )
        #     if channels_from_database is None or len(
        #             channels_from_database) == 0:
        #         return
        channel_recent_upload = await self.get_recent_upload(channel_name="MemesByMemesaurus")
        print(channel_recent_upload)
        print(await self.get_video(channel_recent_upload["contentDetails"]["videoId"]))
        # for channel_data in channels_from_database:
        #     channel_id = channel_data["channel_id"]
        #     channel_name = channel_data["channel_name"]
        #     channel_last_upload = await self.get_video(
        #         channel_data["recent_upload_id"])
        #     channel_last_upload_datetime = self._get_valid_iso_formate(
        #         channel_last_upload["contentDetails"]["videoPublishedAt"])
        #     recent_uploads = self.get_recent_upload(channel_name=channel_name)
        #     recent_uploads_datetime = self._get_valid_iso_formate(
        #         recent_uploads["contentDetails"]["videoPublishedAt"]
        #     )
        #     if cha
