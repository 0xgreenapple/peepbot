"""
Peepbot main runner
~~~~~~~~~~~~~~~~~~~
starter of the peep bot for discord py
:copyright: ©xgreenapple
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
import psutil

import discord
from discord.ext import commands, tasks

from collections import Counter
from itertools import cycle
from platform import python_version
from typing import Optional

from handler import Context
from handler.utils import emojis, Colour
from handler.database import database
from handler.logger import logger
from handler.tasks import CheckEconomyItems

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
        self.spam_count = Counter()
        self.taskrunner: Optional[CheckEconomyItems] = None
        self.version = "0.0.1a"
        self.owner_id = 888058231094665266
        self.message_prefix_s = "peep bot"
        self.bot_user_agent = "peep (Discord Bot)"
        self.logger: typing.Optional[logger] = None
        self.emoji = emojis()
        self.online_time = datetime.datetime.now(datetime.timezone.utc)
        self.spam_cooldown = commands.CooldownMapping.from_cooldown(
            5.0, 6.0, commands.BucketType.user)
        self.user_agent = (
            "peep "
            f"Python/{python_version()} "
            f"aiohttp/{aiohttp.__version__}"
            f"discord.py/{discord.__version__}"
        )
        self.colors = Colour()

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
        # while making the request ot other apis
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
        self.Database.startup_task = self.initialize_database
        await self.Database.initialize()
        self.db = self.database = self.database_connection_pool = self.Database.db
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
        """ Do startup task when bot successfully connects to database"""
        self.console_log(f"is shard rate limited? :{self.is_ws_ratelimited()}")
        if not hasattr(self, 'uptime'):
            self.startTime = time.time()
        if not self.ready:
            self.ready = True
            self.console_log(f"bot is logged as {self.user}")
        else:
            self.console_log(f'{self.user} bot reconnected.')

    async def startup_tasks(self):
        """ startup tasks """
        await self.wait_until_ready()
        # starts bot status loop
        await self.change_status.start()
        # initialize database event manager
        self.taskrunner = CheckEconomyItems(self)

    # Setup every tables :)
    async def initialize_database(self):
        await self.Database.CreateSchema(schema_name="test")
        # database for duel commands
        await self.Database.CreateTable(
            table_name="test.duel", columns=
            """
            user_id1      BIGINT NOT NULL,
            user_id2      BIGINT NOT NULL,
            user_ready    boolean DEFAULT FALSE,
            member_ready  boolean DEFAULT FALSE,
            message_id    BIGINT NOT NULL,
            PRIMARY KEY	  (message_id),
            r_user_ready       boolean DEFAULT FALSE,
            r_member_ready      boolean DEFAULT FALSE,
            img2_id       BIGINT,
            meme_id       TEXT
            """
        )
        # leaderboard for memes based on likes
        await self.Database.CreateTable(
            table_name="test.leaderboard",
            columns=
            """
            guild_id1      BIGINT NOT NULL,
            channel        BIGINT,
            likes          BIGINT DEFAULT 5,
            PRIMARY KEY (guild_id1,channel)
            """
        )

        # store all the likes
        await self.Database.CreateTable(
            table_name="test.likes",
            columns=
            """
            guild_id1   BIGINT NOT NULL,
            channel     BIGINT,
            likes       BIGINT DEFAULT 5,
            PRIMARY KEY (guild_id1,channel)
            """
        )

        # basically its store the role ids to be used later
        await self.Database.CreateTable(
            table_name="test.utils",
            columns=
            """
            guild_id1     BIGINT NOT NULL,
            role_id1      BIGINT,
            active        BOOLEAN DEFAULT FALSE,
            PRIMARY KEY   (guild_id1)
            """
        )
        # setup rewards roles
        await self.Database.CreateTable(
            table_name="test.rewards",
            columns=
            """
            guild_id1     BIGINT NOT NULL,
            channel_id1      BIGINT NOT NULL,
            limit_1      BIGINT,
            limit_2      BIGINT,
            limit_3      BIGINT,
            role_1       BIGINT,
            role_2       BIGINT,
            role_3       BIGINT,
            PRIMARY KEY (guild_id1,channel_id1)
            """
        )
        # store the settings stats
        await self.Database.CreateTable(
            table_name="test.setup",
            columns=
            """
            guild_id1     BIGINT NOT NULL,
            vote               BIGINT,
            reaction_ls        BOOLEAN DEFAULT FALSE,
            thread_ls          BOOLEAN DEFAULT FALSE,
            listener           BOOLEAN DEFAULT FALSE,
            thread_message     TEXT,
            rewards            BOOLEAN DEFAULT FALSE,      
            vote_time          BIGINT DEFAULT 60,
            mememanager_role   BIGINT,
            customization_time BIGINT DEFAULT 5,
            PRIMARY KEY (guild_id1)
            """
        )
        # store gallery channels ids
        await self.Database.CreateTable(
            table_name="test.channels",
            columns=
            """
            guild_id1         BIGINT NOT NULL,
            gallery_l1        BIGINT,
            gallery_l2        BIGINT,
            gallery_l3        BIGINT,
            gallery_l4        BIGINT,
            gallery_l5        BIGINT,
            gallery_l6        BIGINT,
            vote              BIGINT,
            meme_channel      BIGINT[],
            thread_channel    BIGINT[],
            reaction_channel  BIGINT[],
            shop_log          BIGINT,
            PRIMARY KEY (guild_id1)
            """
        )
        # I forgot what it does
        await self.Database.CreateTable(
            table_name="test.msg",
            columns=
            """
            guild_id1         BIGINT NOT NULL,
            channel_id        BIGINT NOT NULL,
            user_id           BIGINT NOT NULL,
            limit1             BIGINT DEFAULT 0,
            PRIMARY KEY (guild_id1,channel_id,user_id)
            """
        )
        # store thread listener channel ids
        await self.Database.CreateTable(
            table_name="test.thread_channel",
            columns=
            """
            guild_id          BIGINT NOT NULL,
            channel_id        BIGINT NOT NULL,
            msg               TEXT,
            PRIMARY KEY (guild_id,channel_id)
            """
        )
        # store economy related stuffs, most valuable one
        await self.Database.CreateTable(
            table_name="test.economy",
            columns=
            """
            guild_id          BIGINT NOT NULL,
            user_id           BIGINT NOT NULL,
            points            FLOAT DEFAULT 0,
            PRIMARY KEY (guild_id,user_id)
            """
        )
        # manage shop items
        await self.Database.CreateTable(
            table_name="test.shop",
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
            table_name="test.inv",
            columns=
            """
            guild_id           BIGINT,
            user_id            BIGINT,
            items              TEXT,
            PRIMARY KEY		   (items),
            expired            TIMESTAMP,
            FOREIGN KEY (items) REFERENCES test.shop(items) 
            ON DELETE CASCADE ON UPDATE CASCADE
            """
        )
        # await self.Database.CreateTable(
        #     table_name="test.booster",
        #     columns=
        #     """
        #     guild_id      BIGINT,
        #     item_name     TEXT,
        #     threshold     FLOAT,
        #     expired       INTERVAL DEFAULT NULL,
        #     PRIMARY KEY	  (guild_id)
        #     """
        # )
        #
        # await self.Database.delete_column(table='test.shop', column='expired')
        # await self.Database.AddColumn(
        #     table='test.shop',
        #     column='expired',
        #     datatype='INTERVAL DEFAULT NULL'
        # )
        # await self.Database.AddColumn(
        #     table="test.shop",
        #     column="expired",
        #     datatype="TIMESTAMP DEFAULT NULL",
        #     check_if_exists=True
        # )
        # await self.Database.AddColumn(
        #     table="test.inv",
        #     column="expired",
        #     datatype="TIMESTAMP DEFAULT NULL",
        #     check_if_exists=True
        # )

    def console_log(self, message):
        """prints to console"""
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

    async def on_message(self, message):
        """ called when the message is received process the commands"""
        process = psutil.Process(os.getpid())
        print(process.memory_info().rss / 1024 ** 2)
        await self.process_commands(message)


# get environment variables
token = os.environ.get('BETATOKEN')
app_ID = os.environ.get('APPLICATION_ID')
password = os.environ.get('DBPASSWORD')
host = os.environ.get('DBHOST')
USER = os.environ.get('DBUSER')
DBNAME = os.environ.get('DBNAME')
