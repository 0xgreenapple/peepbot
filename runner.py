from enum import Enum

import discord
import subprocess
import ssl
import os
import contextlib
import logging
import sys
import asyncio
import typing
import aiohttp.client_exceptions

from pepebot import pepebot
from handler.logger import logger
from discord import app_commands
from discord.ext import commands
from discord.app_commands import checks, Choice


if __name__ == "__main__":

    client = pepebot()
    # logger
    log = logger(
        FileName='botconfig/logs/sussybot.log',output=sys.stderr, outputHandler=True,Level=logging.INFO)

    async def main():
        async with client:
            try:
                log.Setup()
                client.console_log("starting up the bot")
                await client.start()
                await client.change_status.start()
            except aiohttp.client_exceptions.ClientConnectionError:
                print('connection error')
            finally:
                client.console_log("shutting down the bot tasks")
                await client.shutdown_tasks()
                client.console_log("closing down the bot")
                await client.close()
                log.Cleanup()
                print(" done ")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"task shutdown")
