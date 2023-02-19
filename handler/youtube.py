"""
:Author: 0xgreenapple
:Licence: MIT
:Copyright: (C) 2022-present 0xgreenapple
"""
import datetime
import os
import logging
import base64
import json
from typing import Optional, Union, List

from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError

from handler.database import Database

_log = logging.getLogger("pepebot")


class EnvironmentNotFound(Exception):
    """ raised when tokens not found at given environment variable"""
    pass


class MissingTokens(Exception):
    """ raised when tokens not found at given environment variable"""
    pass


class YoutubeAuth:
    def __init__(self):
        self.is_authorised = False
        self.is_tokens_ready = False
        self.database: Optional[Database] = None
        self.__refresh_token: Optional[str] = None
        self.__access_token: Optional[str] = None
        self.__client_secret: Optional[str] = None
        self.__client_id: Optional[str] = None
        self.__expiring_on: Optional[datetime.datetime] = None
        self.default_token_file: str = "token.json"
        self.tokens_file: Optional[Union[os.PathLike, str]] = None

        self.__credentials: Optional[Credentials] = None
        self.token_url = "https://oauth2.googleapis.com/token"
        self.default_scope = "https://www.googleapis.com/auth/youtube.readonly"
        self.scopes: list[str] = [self.default_scope]
        self.tokens_environment_key: str = "YOUTUBE_API_TOKENS_B64"

    async def authorize(self):
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
            await self.renew_credentials()
        self.is_authorised = True

    async def renew_credentials(self):
        try:
            self.__credentials.refresh()
            self.attach_tokens(
                **json.loads(self.__credentials.to_json()))
        except RefreshError as error:
            if not error.retryable:
                # TODO: log to channel to get new tokens
                return
            self.__credentials.refresh()

    def attach_tokens(
            self, token: str, access_token: str, client_secret: str,
            client_id: str, expiry: str = None, token_uri: str = None,
            scopes: List[str] = None
    ) -> dict:
        self.__refresh_token = token
        self.__access_token = access_token
        self.__client_id = client_id
        self.__client_secret = client_secret
        if token_uri is not None:
            self.token_url = token_uri
        if expiry is not None:
            self.__expiring_on = datetime.datetime.fromisoformat(expiry)
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
        decoded_base64_string = self.decode_b64_tokens(base64_token_string)
        self.attach_tokens(**decoded_base64_string)
        return decoded_base64_string

    def get_tokens_from_file(self):
        with open(file=self.tokens_file, mode="r") as token_file:
            token_json = json.loads(token_file.read())
            self.attach_tokens(**token_json)
            return token_json

    @staticmethod
    def decode_b64_tokens(b64_tokens: str) -> dict:
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
            "expiry": self.__expiring_on.__str__()
        }
        return formatted_tokens

    async def append_tokens_to_file(self, filename: str = None):
        token_json_str = json.dumps(self.get_formatted_tokens())
        if filename is not None:
            self.tokens_file = filename
        with open(file=self.tokens_file, mode="w+") as token_file:
            token_file.write(token_json_str)
