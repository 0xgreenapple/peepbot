
import asyncio
import sys

import discord.errors as discord_errors
from pepebot import pepebot

import logging
from handler.logger import logger

_log = logging.getLogger(__name__)


async def main():
    client = pepebot()
    levels = {
        "discord": logging.INFO,
        "discordHTTP": logging.DEBUG,
        "aiohttp": logging.INFO,
        "aiohttp_server": logging.DEBUG,
        "aiohttp_web": logging.DEBUG,
        "aiohttp_client": logging.DEBUG,
        "aiohttp_access": logging.DEBUG,
        "asyncio": logging.WARNING,
        "asyncpg": logging.DEBUG
    }

    # logger, log into file
    client.logger = logger(
        FileName='botconfig/logs/sussybot.log',
        is_consoleHandler=True,
        output=sys.stderr,
        Level=logging.INFO,
        Loggers=levels
    )

    async with client:
        try:
            client.logger.Setup()
            _log.info("starting up the bot")
            await client.start()
        finally:
            _log.warning("terminating bot tasks")
            _log.warning("closing down the bot")
            await client.close()
            client.logger.Cleanup() # close the logger

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _log.warning(f"task shutdown")
