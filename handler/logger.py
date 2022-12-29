"""
logger class for peepbot
~~~~~~~~~~~~~~~~~~~
:copyright: (c) xgreenapple
:license: MIT see LICENSE for more details
"""


import contextlib
import sys
import logging
import typing

from logging import handlers


# logger class for the bot
class logger:
    def __init__(self,
                 FileName: str = None,
                 output: typing.Optional[typing.TextIO] = None,
                 encoding: str = 'utf-8',
                 maxBytes: int = 32 * 1024 * 1024,
                 backupCount: int = 5,
                 Formatter: logging.Formatter = None,
                 outputHandler: bool = False,
                 Level: typing.Literal[0, 10, 20, 30, 40, 50] = None
                 ):

        self.logLevel = Level
        self.BackupCount = backupCount
        self.Filename: str = FileName
        self.MaxBytes = maxBytes
        self.dt_fmt: str = '%Y-%b:%m-%a:%d %I:%M %p'
        self.encoding = encoding
        self.Streamdhandler: bool = outputHandler

        self.console: typing.Optional[typing.TextIO] = output
        self.formatter: logging.Formatter = Formatter if Formatter else self.GetFormatter()
        self.Streamhandler: logging.StreamHandler = self.__GetHandler(True) if outputHandler else None
        self.log: typing.Optional[logging.Logger] = None
        self.Handler = self.__GetHandler()

        # logging levels
        self.discordHTTP_loglevel: int = logging.INFO
        self.discord_loglevel: int = logging.INFO
        self.aiohttp_loglevel: int = logging.DEBUG
        self.aiohttp_client_level: int = logging.DEBUG
        self.aiohttp_server_level: int = logging.DEBUG
        self.aiohttp_web_level: int = logging.DEBUG
        self.aiohttp_access_level: int = logging.DEBUG
        self.asyncio_loglevel: int = logging.INFO
        self.asycpg_loglevel: int = logging.DEBUG

    # destructor clear the logging handlers
    def __del__(self):
        if len(self.log.handlers):
            self.Cleanup()

    # initialize Stream handler and File handlers
    def __GetHandler(self, GetStream_Handler: bool = False):
        if GetStream_Handler:
            return logging.StreamHandler(self.console)

        if self.Filename:
            return handlers.RotatingFileHandler(
                filename=self.Filename, maxBytes=self.MaxBytes, mode='w', backupCount=self.BackupCount,
                encoding='utf-8'
            )
        else:
            return logging.StreamHandler(self.console)

    # initialize logger
    def __initializeLogger(self):
        self.log = logging.getLogger()

    # get formatter
    def GetFormatter(self, dt_fmt: str = None):
        dt_Fmt = dt_fmt if dt_fmt else self.dt_fmt
        return logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_Fmt, style='{')

    # initialize the logger
    def Setup(self):
        self.__initializeLogger()
        logging.getLogger('discord').setLevel(self.discord_loglevel)
        logging.getLogger('asyncio').setLevel(self.asyncio_loglevel)
        logging.getLogger('asyncpg').setLevel(self.asycpg_loglevel)
        logging.getLogger('discord.http').setLevel(self.discordHTTP_loglevel)
        logging.getLogger('aiohttp.client').setLevel(self.aiohttp_client_level)
        logging.getLogger('aiohttp.server').setLevel(self.aiohttp_server_level)
        logging.getLogger('aiohttp').setLevel(self.aiohttp_loglevel)
        logging.getLogger('aiohttp.access').setLevel(self.aiohttp_access_level)
        logging.getLogger("asyncio").setLevel(self.asyncio_loglevel)

        self.log.setLevel(self.logLevel)
        self.Handler.setFormatter(fmt=self.formatter)
        if self.Streamhandler:
            self.Streamhandler.setFormatter(fmt=self.formatter)
            self.log.addHandler(self.Streamhandler)

        self.log.addHandler(self.Handler)

    # setup log levels
    def loglevel(
            self, discord: int = logging.INFO, discordHTTP: int = logging.INFO,
            aiohttp: int = logging.INFO, aiohttp_server: int = logging.DEBUG, aiohttp_web: int = logging.DEBUG,
            aiohttp_client: int = logging.DEBUG, aiohttp_access=logging.DEBUG,
            asyncio: int = logging.WARNING, asyncpg: int = logging.DEBUG
    ):
        # aiohttp log levels , not necessary
        self.aiohttp_loglevel = aiohttp
        self.aiohttp_web_level = aiohttp_web
        self.aiohttp_access_level = aiohttp_access
        self.aiohttp_client_level = aiohttp_client
        self.aiohttp_server_level = aiohttp_server

        self.discord_loglevel = discord
        self.discordHTTP_loglevel = discordHTTP
        self.asyncio_loglevel = asyncio
        self.asycpg_loglevel = asyncpg

    # cleanup the logger
    def Cleanup(self):
        Handlers = self.log.handlers
        for handler in Handlers:
            handler.close()
            self.log.removeHandler(handler)

    # write to the console
    def write(self, *, message: str):
        self.console.write(message)
