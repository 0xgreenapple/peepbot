"""
logger class for peepbot
~~~~~~~~~~~~~~~~~~~
:copyright: (c) xgreenapple
:license: MIT see LICENSE for more details
"""

import sys
import logging
from logging import handlers

import typing
from typing import (
    Optional,
    Literal,
    TextIO,
    Dict,
    List)


# logger class for the bot
class logger:
    def __init__(self,
                 FileName: str = None,
                 Loggers: Optional[dict] = None,
                 output: Optional[TextIO] = sys.stderr,
                 encoding: str = 'utf-8',
                 maxBytes: int = 32 * 1024 * 1024,
                 backupCount: int = 5,
                 Formatter: logging.Formatter = None,
                 is_consoleHandler: bool = False,
                 Level: int = None):

        self.levelTypes: List[int] = [0, 10, 20, 30, 40, 50]
        self.dt_fmt: str = '%Y-%b:%m-%a:%d %I:%M %p'

        self.logLevel = Level
        self.BackupCount = backupCount
        self.Filename: str = FileName
        self.MaxBytes = maxBytes

        self.log: typing.Optional[logging.Logger] = None
        self.console: Optional[TextIO] = output

        self.encoding: str = encoding
        self.Loggers: Dict[str, int] = Loggers if Loggers else {}
        self.is_consoleHandler: bool = is_consoleHandler
        self.formatter: logging.Formatter = Formatter if Formatter else self.GetFormatter()

        self.StreamedHandler: Optional[logging.StreamHandler] = None
        self.FileHandler: Optional[handlers.RotatingFileHandler] = None

    # destructor clear the logging handlers
    def __del__(self):
        if len(self.log.handlers):
            self.Cleanup()

    # initialize Stream handler and File handlers
    def __GetHandler(self):
        self.FileHandler = handlers.RotatingFileHandler(
                filename=self.Filename, maxBytes=self.MaxBytes, mode='w', backupCount=self.BackupCount,
                encoding='utf-8'
        )
        if self.is_consoleHandler:
            self.StreamedHandler = logging.StreamHandler(self.console)

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
        self.__GetHandler()
        self.setLoggers()
        self.log.setLevel(self.logLevel)
        if self.FileHandler:
            self.FileHandler.setFormatter(fmt=self.formatter)
            self.log.addHandler(self.FileHandler)
        if self.StreamedHandler:
            self.StreamedHandler.setFormatter(fmt=self.formatter)
            self.log.addHandler(self.StreamedHandler)

    def setLoggers(self):
        for Logger, Level in self.Loggers.items():
            logging.getLogger(Logger).setLevel(Level)

    def getLoggers(self, *args, **kwargs):
        for LoggerName in args:
            self.Loggers[LoggerName] = self.logLevel
        for LoggerName, Levels in kwargs.items():
            if Levels in self.levelTypes:
                self.Loggers[LoggerName] = Levels
            else:
                raise f"{Levels} is not a valid level, must be any of {self.levelTypes}"

    def getLevel(self,Level):
        if Level in self.levelTypes:
            return Level
        else:
            raise f"{Level} is not a valid level, must be any of {self.levelTypes}"

    # cleanup the logger
    def Cleanup(self):
        Handlers = self.log.handlers
        for handler in Handlers:
            handler.close()
            self.log.removeHandler(handler)

    # write to the console
    def write(self, *, message: str):
        self.console.write(message)

    @staticmethod
    def out(message: str):
        sys.stdout.write(message)

