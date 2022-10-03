"""
database class for peepbot
~~~~~~~~~~~~~~~~~~~
:copyright: (c) xgreenapple
:license: MIT see LICENSE for more details
"""

import asyncio
import contextlib
import json
import os
# database
import asyncpg
import dotenv
import logging

log = logging.getLogger(__name__)


# Main class for the database
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
        self.database = main_database
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

    # destructor, close the pool and clear everything
    def __del__(self):
        self.Cleanup()

    async def __connect(self):
        # check if connection is already made
        if self.database_pool:
            return

        # connect to database
        if self.connected_to_database.is_set():
            self.connected_to_database.clear()
            self.db = self.database = \
                self.database_connection_pool = \
                await self.CreateDatabasePool()
            self.connected_to_database.set()
        else:
            await self.connected_to_database.wait()

    # clear everything
    def Cleanup(self):
        if self.db.close():
            self.db.close()

        if self.connected_to_database.is_set():
            self.connected_to_database.clear()

    # initialize and Set up the attributes
    async def initialize(self):
        await self.__connect()
        await self.startup_task()

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
            database=self.database,
            host=self.host,
            init=self.__initialize_database_connection,
            max_size=self.max_connection,
            min_size=self.min_connection
        )

    async def startup_task(self):
        """startup task called after initializing the database
        , override it to use"""
        ...


# child database of Database we will use it
class database(Database):
    def __init__(self, user: str,
                 Password: str,
                 main_database: str,
                 Host: str,
                 max_inactive_timeout=0,
                 max_connection: int = 13,
                 min_connection: int = 10,
                 schema: str = "pg_catalog"):
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
        print(args)
        query = f"""CREATE TABLE IF NOT EXISTS {table_name}( {columns} );"""
        return await self.db.execute(query, *args)

    async def CreateSchema(self, *args, schema_name: str):
        query = f"""CREATE SCHEMA IF NOT EXISTS {schema_name}"""
        return await self.db.execute(query, *args)

    async def Select(self, *args, table: str, columns: str, condition: str, return_column=False):
        query = f"""SELECT {columns} FROM {table} WHERE {condition}"""
        if return_column:
            return await self.db.fetch(query, *args)
        else:
            return await self.db.fetchval(query, *args)

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

    async def Delete(self, *args, table: str, condition: str):
        query = f"""DELETE FROM {table} WHERE {condition}"""
        return await self.db.execute(query, *args)

    async def Update(self, *args, table: str, SET: str, condition: str):
        query = f"""UPDATE {table} SET {SET} WHERE {condition}"""
        return await self.db.execute(query, *args)

    async def AlterTableColumn(self, *args, table: str, SET: str, condition: str):
        query = f"""ALTER TABLE {table} SET {SET} WHERE {condition}"""
        return await self.db.execute(query, *args)
