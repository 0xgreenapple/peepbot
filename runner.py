import asyncio
import sys
import os

import aiohttp
import discord
from pepebot import PepeBot

import logging
from handler.logger import Logger
from discord.ext import commands
from handler.context import Context

_log = logging.getLogger("pepebot")


@commands.group(name='cog', invoke_without_command=True)
@commands.is_owner()
async def cog(ctx: Context):
    embed = discord.Embed(title="Cogs")
    embed.description = ""
    for index, ext in enumerate(ctx.bot.extensions, start=1):
        embed.description += f"{index}{ext} \n"
    await ctx.send(embed=embed)


@cog.command()
@commands.is_owner()
async def load(ctx: Context, Cog: str):
    failed_extensions = []
    loaded_extensions = []
    embed = discord.Embed(title="``cog loaded``")
    if Cog == '*':
        for ext in ctx.bot.COGS:
            try:
                await ctx.bot.load_extension(name="cogs." + ext)
            except (commands.ExtensionFailed, commands.ExtensionNotFound):
                failed_extensions.append(ext)
            except commands.ExtensionAlreadyLoaded:
                loaded_extensions.append(ext)
            else:
                loaded_extensions.append(ext)

        embed.description = (
            f"loaded extension: {loaded_extensions} "
            f"{len(loaded_extensions)}/{len(ctx.bot.COGS)} \n"
            f"failed extensions: {failed_extensions}"
        )
        await ctx.send(embed=embed)
        return
    try:
        embed.description = f"{Cog} has been successfully loaded"
    except commands.ExtensionAlreadyLoaded:
        await ctx.error_embed(description="cog is already loaded")
    except commands.ExtensionNotLoaded:
        await ctx.error_embed(description=f"{Cog} is not a valid cog")
    except commands.ExtensionFailed:
        await ctx.error_embed(description="cog failed to load")
    await ctx.send(embed=embed)


@cog.command()
@commands.is_owner()
async def remove(ctx: Context, Cog: str):
    removed_extensions = []
    failed_extensions = []
    embed = discord.Embed(title="``removed cog``")
    if Cog == "*":
        for ext in ctx.bot.COGS:
            try:
                await ctx.bot.unload_extension(name="cogs." + ext)
            except (commands.ExtensionNotLoaded, commands.ExtensionNotFound):
                failed_extensions.append(ext)
            else:
                removed_extensions.append(ext)
        embed.description = (
            f"removed extensions: {removed_extensions} "
            f"{len(removed_extensions)}/{len(ctx.bot.COGS)} \n"
            f"failed extensions: {failed_extensions}"
        )
        await ctx.send(embed=embed)
        return
    try:
        await ctx.bot.unload_extension(name="cogs." + Cog)
    except commands.ExtensionNotFound:
        await ctx.error_embed("given cog is not valid")
    except commands.ExtensionNotLoaded:
        await ctx.error_embed("the cog is already not loaded")
    embed.description = f"{Cog} cog has been removed successfully"
    await ctx.send(embed=embed)


@cog.command()
@commands.is_owner()
async def reload(ctx: Context, Cog: str):
    failed_extensions = []
    reloaded_extensions = []
    embed = discord.Embed(title="``reloaded cogs``")
    if Cog == "*":
        for cogs in ctx.bot.COGS:
            try:
                await ctx.bot.reload_extension(name="cogs." + cogs)
            except (commands.ExtensionFailed, commands.ExtensionNotLoaded,
                    commands.ExtensionNotFound):
                failed_extensions.append(cogs)
            else:
                reloaded_extensions.append(cogs)
        embed.description = (
            f"reloaded cogs: {reloaded_extensions} "
            f"``{len(reloaded_extensions)}/{len(ctx.bot.COGS)}``\n"
            f"failed to reload: {failed_extensions}"
        )
        await ctx.send(embed=embed)
        return
    else:
        try:
            await ctx.bot.reload_extension(name="cogs." + Cog)
        except commands.ExtensionFailed:
            await ctx.error_embed(description="failed to load cog")
        except commands.ExtensionNotFound:
            await ctx.error_embed(description="the extension is not valid")
        except commands.ExtensionNotLoaded:
            await ctx.error_embed(description="extension is already not loaded")
        except commands.ExtensionError:
            await ctx.error_embed(description="something went wrong")
        embed.title = "``loaded cog``"
        embed.description = f"{Cog} successfully loaded!"
        await ctx.send(embed=embed)


@commands.is_owner()
@commands.command(name="sync")
async def sync_commands(ctx: Context):
    await ctx.bot.tree.sync()
    await ctx.send("Done")


async def main():
    client = PepeBot()
    levels = {
        "pepebot": logging.INFO,
        "youtube": logging.INFO,
        "discord": logging.INFO,
        "discord.http": logging.WARNING,
        'discord.state': logging.WARNING,
        'discord.gateway': logging.WARNING,
        "discord.bot": logging.WARNING,
        "discord.client": logging.WARNING,
        "aiohttp": logging.DEBUG,
        "asyncio": logging.DEBUG,
        "asyncpg": logging.DEBUG,
        "asyncpg.pool": logging.DEBUG

    }

    # logger, log into file
    client.logger = Logger(
        base_handler=f"pepebot",
        fileName='botconfig/logs/pepebot.log',
        is_console_handler=True,
        output=sys.stderr,
        level=logging.INFO,
        loggers=levels
    )
    client.add_command(cog)



    async with client, client.logger:
        try:
            _log.info("starting up the bot")
            await client.start()
        except aiohttp.ClientConnectorError:
            _log.info("unable to connect to gateway, maybe offline")
        except discord.ConnectionClosed as error:
            _log.info(
                f"connection closed reason:{error.reason} code: {error.code}")
        finally:
            _log.warning("terminating bot tasks")
            _log.warning("closing down the bot")
            await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _log.warning(f"task shutdown")
