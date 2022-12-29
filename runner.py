from enum import Enum

import logging
import sys
import asyncio

import aiohttp
from aiohttp import ClientConnectionError

from pepebot import pepebot
from handler.logger import logger

_log = logging.getLogger(__name__)
if __name__ == "__main__":

    client = pepebot()
    # logger, log into file   
    log = logger(
        FileName='botconfig/logs/sussybot.log',
        output=sys.stderr,
        outputHandler=True,
        Level = logging.INFO)

    async def main():
        async with client:
            
            try:
                log.Setup()
                client.console_log("starting up the bot")
                await client.start()
            except ClientConnectionError:
                _log.warning(ClientConnectionError)
            finally:
                client.console_log("shutting down the bot tasks")
                client.console_log("closing down the bot")
                await client.close()
                log.Cleanup()
                print(" done ")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"task shutdown")
