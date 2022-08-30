import asyncio

import contextlib
import json
import os
# database
import asyncpg
import dotenv

dotenv.load_dotenv()

password = os.environ.get('DBPASSWORD')
host = os.environ.get('DBHOST')


@contextlib.asynccontextmanager
async def create_database_connection():
    connection = await asyncpg.connect(
        user="postgres",
        password=password,
        database="peepserver",
        host=host
    )
    await initialize_database_connection(connection)
    try:
        print('postgres')
        yield connection
    finally:
        await connection.close()


async def create_database_pool():
    print('pool')
    return await asyncpg.create_pool(
        user="postgres",
        password=password,
        database="peepserver",

        host=host,
        init=initialize_database_connection
    )


async def initialize_database_connection(connection):
    print('intigggh da')
    await connection.set_type_codec(
        "jsonb",
        encoder=json.dumps, decoder=json.loads,
        schema="pg_catalog"
    )
