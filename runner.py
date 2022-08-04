from enum import Enum

import aiohttp.client_exceptions
import discord
import subprocess
import ssl
from pepebot import pepebot
import os
from discord.app_commands import checks, Choice
from discord.ext import commands
import contextlib


if __name__ == "__main__":
    import logging
    import typing
    import sys
    from discord import app_commands
    import asyncio

    client = pepebot()

    @contextlib.contextmanager
    def setup_logging():
        log = logging.getLogger()

        try:
            # __enter__
            max_bytes = 32 * 1024 * 1024  # 32 MiB
            logging.getLogger('discord').setLevel(logging.INFO)
            logging.getLogger('asyncio').setLevel(logging.INFO)

            logging.getLogger('asyncpg').setLevel(logging.DEBUG)
            logging.getLogger('asyncpg').setLevel(logging.INFO)
            logging.getLogger('discord.http').setLevel(logging.INFO)
            logging.getLogger('aiohttp.client').setLevel(logging.WARNING)
            logging.getLogger('aiohttp.server').setLevel(logging.WARNING)
            logging.getLogger('aiohttp').setLevel(logging.INFO)
            logging.getLogger('aiohttp.access').setLevel(logging.INFO)
            logging.getLogger("asyncio").setLevel(logging.INFO)

            log.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stderr)
            # (filename='sussybot.log', encoding='utf-8', mode='w', maxBytes=max_bytes,
            # backupCount=5)
            dt_fmt = '%Y-%m-%d %H:%M:%S'
            fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
            handler.setFormatter(fmt)
            log.addHandler(handler)

            yield
        finally:
            # __exit__
            handlers = log.handlers[:]
            for hdlr in handlers:
                hdlr.close()
                log.removeHandler(hdlr)


    async def main():
        async with client:
            try:
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
                print(" done ")





    try:
        with setup_logging():
            asyncio.run(main())

    except KeyboardInterrupt:
        print(f"task shutdown with ")
