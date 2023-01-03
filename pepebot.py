"""
Peepbot main runner
~~~~~~~~~~~~~~~~~~~
starter of the peep bot for discord py
:copyright: (C) 2022-present xgreenapple
:license: MIT.
"""

__title__ = 'Peep-bot'
__author__ = 'xgreenapple'
__copyright__ = 'MIT Copyright xgreenapple'
__version__ = '0.0.2a'

import logging
import os
import time
import asyncio
import datetime
import typing
import aiohttp
import aioredis
import psutil

import discord
from discord.ext import commands, tasks

from collections import Counter
from itertools import cycle
from platform import python_version
from typing import Optional,TYPE_CHECKING

from handler import Context
from handler.utils import emojis, Colour
from handler.logger import logger
from handler.tasks import CheckEconomyItems
from handler.cache import Guild_cache
from handler.database import database

log = logging.getLogger(__name__)


class pepebot(commands.Bot):
    """peep-bot v0.0.2a Interface
    """
    user: discord.ClientUser
    bot_app_info: discord.AppInfo
    owner: 888058231094665266

    # constructor
    def __init__(self):
        self.aiohttp_session = None
        self.ready = False
        self.statues = cycle(
            ["peep"])
        super().__init__(
            command_prefix=self.get_command_prefix,
            case_insensitive=True,
            intents=discord.Intents(
                messages=True,
                bans=True,
                members=True,
                emojis=True,
                guilds=True,
                message_content=True,
                reactions=True
            ),
            application_id=app_ID,
            help_command=None,
        )

        # variables
        self.version = "0.0.1a"
        self.message_prefix_s = "peep bot"
        self.emoji = emojis()
        self.colors = Colour()
        self.spam_count = Counter()
        self.guild_cache: Guild_cache = Guild_cache()
        self._app_info: Optional[discord.AppInfo] = None
        self.taskrunner: Optional[CheckEconomyItems] = None
        self.owner_id = 888058231094665266
        self.logger: typing.Optional[logger] = None
        self.online_time = datetime.datetime.now(datetime.timezone.utc)
        self.spam_cooldown = commands.CooldownMapping.from_cooldown(
            5.0, 6.0, commands.BucketType.user)
        self.user_agent = (
            "peep (Discord Bot: {self.version})/ discord.gg/memesaurus"
            f"Python/{python_version()} "
            f"aiohttp/{aiohttp.__version__}"
            f"discord.py/{discord.__version__}"
        )
        # database variables
        self.db = self.database = self.database_connection_pool = None
        self.Database: Optional[database] = None
        self.connected_to_database = asyncio.Event()
        self.connected_to_database.set()

    def __getattr__(self, item):
        """ called when an attribute called is not exists in class,
        checks if attribute exists in the emojis class
        and returns it else raise the attribute error
        """
        if hasattr(self.emoji, item):
            return getattr(self.emoji, item)
        elif hasattr(self.colors, item):
            return getattr(self.colors, item)
        raise AttributeError(f"'{item}' attribute in {self.__class__.__name__} class does not exists")

    # initialize the bot, connect to the websocket
    async def setup_hook(self) -> None:
        # aiohttp client session we will use it later
        self.aiohttp_session = aiohttp.ClientSession(loop=self.loop)
        self.console_log("session started")
        # initialize the bot app info
        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id
        self.console_log("setting up database >")
        # await self.initialize_database()
        self.Database = database(
            user=USER,
            main_database=DBNAME,
            Password=password,
            Host=host,
        )
        await self.Database.initialize()
        self.db = self.database = self.database_connection_pool = self.Database.database
        await self.initialize_database()
        # connect to redis server

        self.console_log("database setup done")
        # bot startup task
        self.loop.create_task(
            self.startup_tasks(), name="Bot startup tasks"
        )
        # the list of cogs that will being initialize
        COGS = ['duel',
                'setup',
                'help',
                'creation',
                'economy',
                'server',
                'error handler',
                'listeners']

        self.console_log("loading cogs..")
        for cog in COGS:
            await self.load_extension(f"cogs.{cog}")
            self.console_log(f"{cog} loaded ")
        self.console_log("setup hook complete")
        log.info("handling the timer")
        await self.tree.sync()

    async def on_ready(self):
        """ Do startup task when bot successfully connects to database """
        
        self.console_log(f"is shard rate limited? :{self.is_ws_ratelimited()}")
        # add uptime to the bot
        if not hasattr(self, 'uptime'):
            self.startTime = time.time()
        # set self.ready to true and sent the console message 
        if not self.ready:
            self.ready = True
            self.console_log(f"bot is logged as {self.user}")
        else:
            self.console_log(f'{self.user} bot reconnected.')

    async def startup_tasks(self):
        """ startup tasks """
        self.taskrunner = CheckEconomyItems(self)

        await self.wait_until_ready()
        # starts bot status loop
        await self.change_status.start()
        # initialize database event manager

    # Setup every tables :)
    async def initialize_database(self):
        await self.Database.CreateTable(
            table_name="peep.Guilds",
            columns="""
            guild_id              BIGINT NOT NULL,   
            PRIMARY KEY          (guild_id)
            """
        )
        await self.Database.CreateTable(
            table_name="peep.Users",
            columns="""
            user_id      BIGINT NOT NULL,
            guild_id     BIGINT NOT NULL,
            FOREIGN KEY (guild_id) REFERENCES peep.Guilds(guild_id),
            PRIMARY KEY (guild_id,user_id)
            """
        )
        await self.Database.CreateTable(
            table_name="peep.Channels",
            columns="""
            channel_id           BIGINT NOT NULL,
            guild_id             BIGINT,
            is_memeChannel       boolean DEFAULT FALSE,
            is_threadChannel     boolean DEFAULT FALSE,
            is_deadChat          boolean DEFAULT FALSE,
            is_ocChannel         boolean DEFAULT FALSE,
            is_voteChannel       boolean DEFAULT FALSE,
            max_like             INT DEFAULT 5,
            voting_time          INTERVAL DEFAULT NULL,
            thread_msg           TEXT,
            PRIMARY KEY          (guild_id,channel_id),
            FOREIGN KEY (guild_id) REFERENCES peep.Guilds(guild_id)
            """
        )

        # store the settings stats
        await self.Database.CreateTable(
            table_name="peep.guild_settings",
            columns=
            """
            guild_id           BIGINT UNIQUE,
            vote               BIGINT,
            reaction_lstnr     BOOLEAN DEFAULT FALSE,
            thread_lstnr       BOOLEAN DEFAULT FALSE,
            oc_lstnr           BOLEAN DEFAULT FALSE,
            vote_time          BIGINT DEFAULT 60,
            MemeAdmin          BIGINT,
            customization_time BIGINT DEFAULT 5,
            FOREIGN KEY (guild_id) REFERENCES peep.Guilds(guild_id)
            """
        )
        await self.Database.CreateTable(
            table_name="peep.user_details",
            columns=
            """
            guild_id     BIGINT NOT NULL,
            user_id      BIGINT NOT NULL,
            likes        integer DEFAULT 0,
            points       FLOAT DEFAULT 0,
            FOREIGN KEY (user_id,guild_id) REFERENCES peep.Users(user_id,guild_id),
            UNIQUE      (guild_id,user_id)
            """
        )

        # manage shop items
        await self.Database.CreateTable(
            table_name="peep.shop",
            columns=
            """
            items              TEXT,
            cost               INT NOT NULL,
            emoji              TEXT,
            PRIMARY KEY		   (items)
            """
        )
        # user Inventory
        await self.Database.CreateTable(
            table_name="peep.inventory",
            columns=
            """
            guild_id               BIGINT NOT NULL,
            user_id                BIGINT NOT NULL,
            items                  TEXT UNIQUE,
            expired                TIMESTAMP,
            FOREIGN KEY (items)    REFERENCES peep.shop(items)
            ON DELETE CASCADE ON   UPDATE CASCADE,
            FOREIGN KEY (user_id,guild_id)  REFERENCES peep.Users(user_id,guild_id),
            UNIQUE                 (user_id,guild_id)
            """
        )
        await self.Database.CreateTable(
            table_name="peep.booster",
            columns=
            """
            guild_id      BIGINT UNIQUE,
            item_name     TEXT UNIQUE,
            threshold     FLOAT,
            expired       INTERVAL DEFAULT NULL,
            PRIMARY KEY	  (guild_id),
            FOREIGN KEY (guild_id) REFERENCES peep.Guilds(guild_id)
            """
        )

    def console_log(self, message):
        """prints to console"""
        if self.logger:
            self.logger.write(f"{self.user} > {message}")
        else:
            print(f"[{datetime.datetime.now().strftime(r'%D %I:%M %p')}] > {self.user} > {message}")

    @staticmethod
    async def get_command_prefix(bot, message: discord.Message):
        """ Returns bot command prefix """
        prefixes = "%"
        return prefixes if prefixes else "%"

    @property
    async def app_info(self):
        """ returns bot app info """
        if not hasattr(self, "_app_info"):
            self._app_info = await self.application_info()
        return self._app_info

    @property
    def owner(self) -> discord.User:
        """ returns bot owner info """
        return self.bot_app_info.owner

    # change bot status message every 15 minutes
    @tasks.loop(minutes=15)
    async def change_status(self):
        """ change the bot status message every in every 15 minutes """
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=next(self.statues))
        )

    """ Events """

    # do something on guild Join
    async def on_guild_join(self, guild):
        log.warning("joined guild : ", guild)

    async def on_guild_remove(self, guild):
        log.warning("left a guild : ", guild)

    async def start(self) -> None:
        """ super method to run the bot"""
        await super().start(token, reconnect=True)

    async def close(self) -> None:
        """ do closeup task when bot closes """
        try:
            self.console_log(f"closing bot session")
            await self.aiohttp_session.close()
            await self.Database.Cleanup()
        except Exception as e:
            print(e)
        try:
            self.console_log(f"closing the bot")
            await super().close()
        except Exception as e:
            print(e)

    async def on_resumed(self):
        """print when client resumed"""
        self.console_log(f"{self.user} [resumed]")

    async def on_connect(self):
        """print when client connected to discord"""
        self.console_log(f"{self.user} is connected successfully")

    async def on_disconnect(self):
        """print when client disconnected to discord"""
        self.console_log(f"{self.user} is disconnected")

    async def get_context(self, message, /, *, cls=Context.Context) -> Context.Context:
        """ overwrite the new bot context"""
        ctx = await super().get_context(message, cls=cls)
        return ctx

    async def on_message(self, message: discord.Message):
        message.content.startswith("$")
        """ called when the message is received process the commands"""
        process = psutil.Process(os.getpid())
        print(process.memory_info().rss / 1024 ** 2)
        await self.process_commands(message)


# get environment variables
token = os.environ.get('BETATOKEN')
app_ID = os.environ.get('APPLICATION_ID')
password = os.environ.get('DBPASSWORD')
redis_pass = os.environ.get("REDISPASS")
host = os.environ.get('DBHOST')
USER = os.environ.get('DBUSER')
DBNAME = os.environ.get('DBNAME')

