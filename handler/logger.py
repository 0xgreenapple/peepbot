"""
:Author: 0xgreenapple(xgreenapple)
:copyright: (c) 0xgreenapple
:license: MIT see LICENSE for more details
"""

import sys

import logging
from logging import StreamHandler, Formatter
from logging.handlers import RotatingFileHandler

import typing
from typing import (
    Optional, Literal,
    TextIO, Dict,
    List)


class LogError(Exception):
    """" base Exception class for log related errors  """
    pass


class InvalidLevelType(LogError):
    """ raises when a level given to logger is invalid"""

    def __init__(self, message, level: int):
        super().__init__(message)
        self.Level = level


class Logger:
    """Base class for logging
    """

    def __init__(self,
                 base_handler: str,
                 fileName: str = None,
                 loggers: Optional[dict] = None,
                 output: Optional[TextIO] = sys.stderr,
                 encoding: str = 'utf-8',
                 max_bytes: int = 32 * 1024 * 1024,
                 backup_count: int = 5,
                 formatter: logging.Formatter = None,
                 is_console_handler: bool = False,
                 level: int = None):

        self.base_handler = base_handler
        self.levelTypes: List[int] = [0, 10, 20, 30, 40, 50]
        self.dt_fmt: str = '%Y-%b:%m-%a:%d %I:%M %p'

        self.log_level = level
        self.backup_count = backup_count
        self.filename: str = fileName
        self.max_bytes = max_bytes

        self.log: typing.Optional[logging.Logger] = None
        self.console: Optional[TextIO] = output

        self.encoding: str = encoding
        self.logger_list: Dict[str, int] = loggers if loggers else {}
        self.loggers: Optional[List[logging.Logger]] = []
        self.is_console_handler: bool = is_console_handler
        self.formatter: logging.Formatter = formatter
        if formatter is None:
            self.formatter = self.get_formatter()

        self.streamed_handler: Optional[StreamHandler] = None
        self.file_handler: Optional[RotatingFileHandler] = None

    def __del__(self):
        # close the logger
        self.close()

    async def __aenter__(self):
        """ add async with support, start the logging session """
        self.setup()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """ exist logging session close up all the loggers running """
        self.close()

    def __initialise_handler(self):
        """ initialise RotatingFileHandler for the specified File
          and also StreamHandler if requested.
        """
        self.file_handler = RotatingFileHandler(
            filename=self.filename,
            maxBytes=self.max_bytes,
            mode='w',
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        if self.is_console_handler:
            self.streamed_handler = StreamHandler(self.console)

    def get_formatter(self, date_formate: str = None) -> Optional[Formatter]:
        """
        returns a logging formatter to the specified date formate if given
        otherwise uses the default date formate.

        Parameters
        ----------
        date_formate: str, optional
            date formate to be used by formatter IF not specified the default
            one will be used.
        Returns
        -------
        logging.Formatter
            a logging Formatter object to be used by logger.
        """
        if date_formate is not None:
            dt_fmt = date_formate
        else:
            dt_fmt = self.dt_fmt
        return logging.Formatter(
            fmt='[{asctime}] [{levelname:<7}] {name}: {message}',
            datefmt=dt_fmt,
            style='{'
        )

    def get_loggers(self, *logger_names, **loggers):
        """ get logger names and levels to the appropriate formate
        to be used by the logger
        """
        # for only logger names given and set the level to global level
        for logger_name in logger_names:
            self.logger_list[logger_name] = self.log_level

        # for logger name and level both given
        for logger_name, level in loggers.items():
            if level in self.levelTypes:
                self.logger_list[logger_name] = level
            else:
                raise InvalidLevelType(
                    f"given level {level} is not valid",
                    level=level
                )

    def set_loggers(self):
        """initialise given loggers for logging module """
        if self.file_handler:
            self.file_handler.setFormatter(fmt=self.formatter)
        if self.streamed_handler:
            self.streamed_handler.setFormatter(fmt=self.formatter)
        for logger_name, level in self.logger_list.items():
            logger = logging.getLogger(logger_name)
            logger.addHandler(self.file_handler)
            logger.addHandler(self.streamed_handler)
            logger.setLevel(level)
            self.loggers.append(logger)
            if logger_name == self.base_handler:
                self.log = logger

    def __initialize_logger(self):
        self.set_loggers()

    def setup(self):
        """ ready everything """
        self.__initialise_handler()
        self.__initialize_logger()
        self.set_loggers()

    def close(self):
        """ close all running handlers for every loggers"""
        for logger in self.loggers:
            if len(logger.handlers) == 0:
                continue
            for handler in logger.handlers:
                handler.close()
                logger.removeHandler(handler)

    def write(self, *, message: str):
        self.console.write(message)

    def out(self, message: str):
        sys.stdout.write(message)
