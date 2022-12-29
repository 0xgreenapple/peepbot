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

    # create table
    async def CreateTable(self, *args, table_name: str, columns: str):
        query = f"""CREATE TABLE IF NOT EXISTS {table_name}( {columns} );"""
        return await self.db.execute(query, *args)

    # create schema
    async def CreateSchema(self, *args, schema_name: str):
        query = f"""CREATE SCHEMA IF NOT EXISTS {schema_name};"""
        return await self.db.execute(query, *args)

    # fetch-value from database
    async def Select(self, *args, table: str, columns: str, condition: str = None,
                     return_everything=False, Filter: str = None, row: bool= False):

        condition = f"WHERE {condition}" if condition else ""
        Filter = Filter if Filter else ""
        query = f"""SELECT {columns} FROM {table} {condition} {Filter}"""

        if return_everything:
            return await self.db.fetch(query, *args)
        elif row:
            return await self.db.fetchrow(query, *args)
        else:
            return await self.db.fetchval(query, *args)

    # delete row
    async def Delete(self, *args, table: str, condition: str):
        query = f"""DELETE FROM {table} WHERE {condition}"""
        return await self.db.execute(query, *args)

    # update row
    async def Update(self, *args, table: str, SET: str, condition: str):
        query = f"""UPDATE {table} SET {SET} WHERE {condition}"""
        return await self.db.execute(query, *args)

    # add column to a table
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

    # drop column from the list
    async def delete_column(self, *args, table: str, column: str):
        query = f"ALTER TABLE {table} DROP COLUMN {column}"
        return await self.db.execute(query, *args)

    # update column from the list
    async def UpdateColumn(self, *args, table: str, column: str, dataType: str):
        query = f"""ALTER TABLE {table} ALTER COLUMN {column} TYPE {dataType}"""
        return await self.db.execute(query, *args)

    # insert row
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
