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
import collections
from collections import defaultdict

import discord
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from pepebot import PepeBot

log = logging.getLogger(__name__)


# base class for the database
class BaseDatabase:

    def __init__(self,
                 bot: PepeBot,
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

        # cache system

    # initialize the database
    async def initialize(self):
        await self.__connect()
        await self.startup_task()

    # create pool and connect to database
    async def __connect(self):
        log.info(
            f"connecting to database with \n user : {self.user} \n db : {self.dbname} \n host: {self.host}")
        # check if connection is already made
        if self.database_pool:
            return

        # connect to database
        if self.connected_to_database.is_set():
            self.connected_to_database.clear()
            self.db = self.database = \
                self.database_pool = \
                await self.create_database_pool()
            self.connected_to_database.set()
        else:
            await self.connected_to_database.wait()

    # clear everything
    async def close(self):
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
    async def create_database_pool(self):
        log.info("creating connection pool")
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
        pass


# child database class
class Database(BaseDatabase):
    """
    child database class of Database
    this contains all the useful methods and attributes that
    will be used most of the time
     """

    def __init__(
            self, bot: PepeBot,
            user: str,
            password: str,
            main_database: str,
            host: str,
            max_inactive_timeout=0,
            max_connection: int = 13,
            min_connection: int = 10,
            schema: str = "pg_catalog"
    ):
        super().__init__(
            bot,
            user,
            password,
            main_database,
            host,
            max_inactive_timeout=max_inactive_timeout,
            max_connection=max_connection,
            min_connection=min_connection,
            schema=schema
        )

    async def create_table(self, *args, table_name: str, columns: str):
        query = f"""CREATE TABLE IF NOT EXISTS {table_name}( {columns} );"""
        return await self.db.execute(query, *args)

    async def create_schema(self, *args, schema_name: str):
        query = f"""CREATE SCHEMA IF NOT EXISTS {schema_name};"""
        return await self.db.execute(query, *args)

    async def select(
            self, *args, table_name: str, columns: str, conditions: str = None,
            filter_by: str = None, return_all_rows: bool = False,
            return_row: bool = False
    ):

        conditions_clause = f"WHERE {conditions}" if conditions else ""
        filters = filter_by if filter_by else ""
        query = f"""SELECT {columns} FROM
                {table_name} {conditions_clause} {filters}"""

        if return_all_rows:
            return await self.db.fetch(query, *args)
        elif return_row:
            return await self.db.fetchrow(query, *args)
        else:
            return await self.db.fetchval(query, *args)

    async def insert(
            self, *args, table: str, columns: str, values: str,
            on_conflicts: str = None,
            returning_columns: Optional[List[str]] = None
    ):

        if on_conflicts is not None:
            on_conflicts = f"ON CONFLICT {on_conflicts}"
        else:
            on_conflicts = ""
        returning = "RETURNING "
        if returning_columns and len(returning_columns) != 0:
            str_returning_column = ",".join(returning_columns)
            returning += str_returning_column
        else:
            returning = ""
        query = f"""
        INSERT INTO {table}({columns}) VALUES({values}) {on_conflicts}
        {returning}
        """
        if returning and returning_columns and len(returning_columns) > 0:
            if len(returning_columns) > 1:
                return await self.db.fetchrow(query, *args)
            else:
                return await self.db.fetchval(query, *args)
        else:
            return await self.db.execute(query, *args)

    async def delete(self, *args, table: str, condition: str):
        query = f"""DELETE FROM {table} WHERE {condition}"""
        return await self.db.execute(query, *args)

    async def update(self, *args, table: str, update_set: str, condition: str):
        query = f"""UPDATE {table} SET {update_set} WHERE {condition}"""
        return await self.db.execute(query, *args)

    async def add_column(
        self, *args, table: str, column: str, datatype: str,
        check_if_exists: bool = False
    ):

        Already_exists = None
        if check_if_exists:
            Already_exists = await self.select(table_name=table, columns=column)
        if not Already_exists:
            query = f"""ALTER TABLE {table} ADD {column} {datatype}"""
            return await self.db.execute(query, *args)
        return None

    async def delete_column(self, *args, table: str, column: str):
        query = f"ALTER TABLE {table} DROP COLUMN {column}"
        return await self.db.execute(query, *args)

    async def update_column(
            self, *args, table: str, column: str, dataType: str):
        query = f"""ALTER TABLE {table} ALTER COLUMN {column} TYPE {dataType}"""
        return await self.db.execute(query, *args)


async def get_guild_settings(bot: PepeBot, guild_id: int):
    """
    return the guild settings stored
    in database and in the cache if exists
    """
    guild_cached_data = bot.cache.get(guild_id)
    # cached guild settings
    cached_guild_settings = None
    # check if column is row or if not get data insert
    if guild_cached_data is not None:
        cached_guild_settings = guild_cached_data.get("guild_settings")
    if cached_guild_settings is None:
        settings = await reinitialise_guild_settings(
            bot=bot, guild_id=guild_id)
        cached_guild_settings = settings
    return cached_guild_settings


async def get_channel_settings(bot: PepeBot, channel: discord.TextChannel):
    """
    return channel settings from cached data
    if exist else from the database
    """
    guild_data = bot.cache.get(channel.guild.id)
    # cached guild settings
    channel_column = guild_data.get(channel.id) if guild_data else None
    cached_channel_settings = None
    if channel_column is not None:
        cached_channel_settings = channel_column.get(channel.id)
    if cached_channel_settings is None:
        data = await reinitialise_channel_settings(
            bot=bot, channel_id=channel.id, guild_id=channel.guild.id)
        cached_channel_settings = data
    return cached_channel_settings


async def reinitialise_guild_settings(bot: PepeBot, guild_id: int):
    """
    Get the current data from guild settings and append
    to guild cache
    """
    settings = await bot.database.select(
        guild_id,
        table_name="peep.guild_settings",
        columns="*",
        conditions="guild_id=$1",
        return_row=True
    )
    bot.cache.setdefault(guild_id, {})["guild_settings"] = settings
    return settings


async def reinitialise_channel_settings(
    bot: PepeBot, channel_id: int, guild_id: int
):
    """
    Get the current data from guild settings and append
    to guild cache
    """
    settings = await bot.database.select(
        channel_id,
        guild_id,
        table_name="peep.channel_settings",
        columns="*",
        conditions="guild_id=$2 AND channel_id = $1",
        return_row=True
    )
    channel_settings = bot.cache.setdefault(guild_id, {})
    channel_settings.setdefault(channel_id, {})["channel_settings"] = settings
    return settings
