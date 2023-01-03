from __future__ import annotations

"""
database class for peepbot
~~~~~~~~~~~~~~~~~~~
:copyright: (c) xgreenapple
:license: MIT see LICENSE for more details
"""

import json
import asyncio
import asyncpg
import logging

import discord
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pepebot import pepebot

log = logging.getLogger(__name__)


# base class for the database
class Database:

    def __init__(self,
                 user: str,
                 Password: str,
                 main_database: str,
                 Host: str,
                 max_inactive_timeout=0,
                 max_connection: int = 13,
                 min_connection: int = 10,
                 schema: str = "pg_catalog"):

        # meta information
        self.host = Host
        self.dbname = main_database
        self.user = user
        self.schema = schema
        self.__password = Password

        # Limits
        self.max_connection = max_connection
        self.min_connection = min_connection
        self.max_inactive_timeout = max_inactive_timeout

        # will initialize it later
        self.db = self.database = self.database_pool = None
        self.connected_to_database = asyncio.Event()
        self.connected_to_database.set()

    # initialize the database
    async def initialize(self):
        await self.__connect()
        await self.startup_task()

    # create pool and connect to database
    async def __connect(self):
        log.info(f"connecting to database with \n user : {self.user} \n db : {self.dbname} \n host: {self.host}")
        # check if connection is already made
        if self.database_pool:
            return

        # connect to database
        if self.connected_to_database.is_set():
            self.connected_to_database.clear()
            self.db = self.database = \
                self.database_pool = \
                await self.CreateDatabasePool()
            self.connected_to_database.set()
        else:
            await self.connected_to_database.wait()

    # clear everything
    async def Cleanup(self):
        if self.db:
            await self.db.close()
        if self.connected_to_database.is_set():
            self.connected_to_database.clear()

    # will use it while creating the pool
    @staticmethod
    async def __initialize_database_connection(connection):
        log.warning("pool database connection")
        await connection.set_type_codec(
            "jsonb",
            encoder=json.dumps, decoder=json.loads,
            schema="pg_catalog"
        )

    # create database pool and return it
    async def CreateDatabasePool(self):
        log.warning('creating pool')

        return await asyncpg.create_pool(
            user=self.user,
            password=self.__password,
            database=self.dbname,
            host=self.host,
            init=self.__initialize_database_connection,
            max_size=self.max_connection,
            min_size=self.min_connection
        )

    async def startup_task(self):
        """ startup task
        called after initializing the database,
        override it to use
        """
        ...


# child database class
class database(Database):
    """
    child database class of Database
    this contains all the useful methods and attributes that
    will be used most of the time
     """

    def __init__(
            self, user: str,
            Password: str,
            main_database: str,
            Host: str,
            max_inactive_timeout=0,
            max_connection: int = 13,
            min_connection: int = 10,
            schema: str = "pg_catalog"
    ):
        super().__init__(
            user,
            Password,
            main_database,
            Host,
            max_inactive_timeout=max_inactive_timeout,
            max_connection=max_connection,
            min_connection=min_connection,
            schema=schema
        )

    async def CreateTable(self, *args, table_name: str, columns: str):
        query = f"""CREATE TABLE IF NOT EXISTS {table_name}( {columns} );"""
        return await self.db.execute(query, *args)

    async def CreateSchema(self, *args, schema_name: str):
        query = f"""CREATE SCHEMA IF NOT EXISTS {schema_name};"""
        return await self.db.execute(query, *args)

    async def Select(self, *args, table: str, columns: str, condition: str = None,
                     return_everything=False, Filter: str = None, row: bool = False):

        condition = f"WHERE {condition}" if condition else ""
        Filter = Filter if Filter else ""
        query = f"""SELECT {columns} FROM {table} {condition} {Filter}"""

        if return_everything:
            return await self.db.fetch(query, *args)
        elif row:
            return await self.db.fetchrow(query, *args)
        else:
            return await self.db.fetchval(query, *args)

    async def Delete(self, *args, table: str, condition: str):
        query = f"""DELETE FROM {table} WHERE {condition}"""
        return await self.db.execute(query, *args)

    async def Update(self, *args, table: str, SET: str, condition: str):
        query = f"""UPDATE {table} SET {SET} WHERE {condition}"""
        return await self.db.execute(query, *args)

    async def AddColumn(self, *args, table: str, column: str, datatype: str,
                        check_if_exists: bool = False):
        Already_exists = None
        if check_if_exists:
            Already_exists = await self.Select(
                table=table,
                columns=column
            )

        if not Already_exists:
            query = f"""ALTER TABLE {table} ADD {column} {datatype}"""
            return await self.db.execute(query, *args)
        return None

    async def delete_column(self, *args, table: str, column: str):
        query = f"ALTER TABLE {table} DROP COLUMN {column}"
        return await self.db.execute(query, *args)

    async def UpdateColumn(self, *args, table: str, column: str, dataType: str):
        query = f"""ALTER TABLE {table} ALTER COLUMN {column} TYPE {dataType}"""
        return await self.db.execute(query, *args)

    async def Insert(self, *args, table: str, columns: str, values: str, on_Conflicts: str = None):
        if on_Conflicts:
            on_Conflicts = f"ON CONFLICT {on_Conflicts}"
        else:
            on_Conflicts = ""

        query = f"""INSERT INTO {table}({columns})
                VALUES({values}) 
                {on_Conflicts}
                """
        return await self.db.execute(query, *args)


async def Get_Guild_settings(bot: pepebot, guild: discord.Guild):
    """
    return the guild settings stored
    in database and in the cache if exists
    """
    guild_cached_data = bot.guild_cache.get(guild.id)
    # cached guild settings
    cached_guild_settings = None
    # check if column is row or if not get data insert
    if guild_cached_data is not None:
        cached_guild_settings = guild_cached_data["guild_settings"]
    if cached_guild_settings is None:
        settings = await reinitialisedGuild_settings(bot=bot, guild_id=guild.id)
        cached_guild_settings = settings
    return cached_guild_settings


async def Get_channel_settings(bot: pepebot, Channel: discord.TextChannel):
    """
    return channel settings from cached data
    if exist else from the database
    """
    guild_data = bot.guild_cache.get(Channel.guild.id)
    # cached guild settings
    channel_column = guild_data.get(Channel.id) if guild_data else None
    cached_channel_settings = None
    if channel_column is not None:
        cached_channel_settings = channel_column[Channel.id]
    if cached_channel_settings is None:
        data = await reinitialisedChannel_settings(bot=bot, channel=Channel)
        cached_channel_settings = data
    return cached_channel_settings


async def reinitialisedGuild_settings(bot: pepebot, guild_id: int):
    """
    Get the current data from guild settings and append
    to guild cache
    """
    settings = await bot.Database.Select(
        guild_id,
        table="peep.guild_settings",
        columns="*",
        condition="guild_id=$1",
        row=True
    )
    bot.guild_cache.setdefault(guild_id, {})["guild_settings"] = settings
    return settings


async def reinitialisedChannel_settings(bot: pepebot, channel: discord.TextChannel):
    """
    Get the current data from guild settings and append
    to guild cache
    """
    settings = await bot.Database.Select(
        channel.id,
        channel.guild.id,
        table="peep.Channels",
        columns="*",
        condition="guild_id=$2 AND channel_id = $1",
        row=True
    )
    channel_settings = bot.guild_cache.setdefault(channel.guild.id, {})
    channel_settings.setdefault(channel.id, {})["channel_settings"] = settings
    print(bot.guild_cache[channel.guild.id][channel.id]["channel_settings"])
    return settings
