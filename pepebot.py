"""
Peepbot main runner
~~~~~~~~~~~~~~~~~~~
starter of the peep bot for discord py
:copyright: (C) 2022-present xgreenapple
:license: MIT.
"""

__title__ = 'Peep-bot'
__author__ = '0xgreenapple'
__copyright__ = 'MIT Copyright xgreenapple'
__version__ = '2.0.0'

import logging
import os
import time
import asyncio
import datetime
import typing
import aiohttp
import asyncpg

import discord
from discord.ext import commands, tasks

from collections import Counter
from itertools import cycle
from platform import python_version
from typing import Optional

from handler import Context
from handler.utils import Emojis, Colour
from handler.logger import Logger
from handler.tasks import CheckEconomyItems
from handler.guild_cache import guild_cache
from handler.database import Database

_log = logging.getLogger("pepebot")


class PepeBot(commands.Bot):
    """PepeBot 2.0 interface"""
    user: discord.ClientUser
    bot_app_info: discord.AppInfo
    owner: 888058231094665266

    # constructor
    def __init__(self):
        self.aiohttp_session = None
        self.ready = False
        self.statues = cycle(
            ["peep"])
        self.start_time: time = None
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
            application_id=APP_ID,
            help_command=None,
        )
        # variables
        self.version = "2.0.0"
        self.message_prefix_s = "peep bot"
        self.emoji: Optional[Emojis] = None
        self.colors = Colour()
        self.spam_count = Counter()
        self.cache: guild_cache = guild_cache()
        self._app_info: Optional[discord.AppInfo] = None
        self.taskrunner: Optional[CheckEconomyItems] = None
        self.owner_id = 888058231094665266
        self.logger: typing.Optional[Logger] = None
        self.online_time = datetime.datetime.now(datetime.timezone.utc)
        self.aiohttp_session: Optional[aiohttp.ClientSession] = None
        self.spam_cooldown = commands.CooldownMapping.from_cooldown(
            5.0, 6.0, commands.BucketType.user)
        self.user_agent = (
            "peep (Discord Bot: {self.version})/ discord.gg/memesaurus"
            f"Python/{python_version()} "
            f"aiohttp/{aiohttp.__version__}"
            f"discord.py/{discord.__version__}"
        )
        # database variables
        self.db = self.pool = self.database_connection_pool = None
        self.database: Optional[Database] = None
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
        raise AttributeError(
            f"'{item}' attribute in {self.__class__.__name__}"
            f" class does not exists")

    # initialize the bot, called when bot logged to discord
    async def setup_hook(self) -> None:
        _log.info("setting up hook")
        # initialise new client session
        self.aiohttp_session = aiohttp.ClientSession(loop=self.loop)
        # initialize the bot app info
        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id
        self.console_log("setting up database >")
        # initialise database
        await self.initialise_database()
        # bot startup task
        self.loop.create_task(
            self.startup_tasks(), name="Bot startup tasks")
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
        await self.tree.sync()

    async def on_ready(self):
        """ Do startup task when bot successfully connects to database """

        await self.wait_until_ready()
        # starts bot status loop
        await self.change_status.start()
        self.console_log(
            f"is shard rate limited? :{self.is_ws_ratelimited()}")
        # add uptime to the bot
        self.start_time = time.time()

        # set self.ready to true and sent the console message 
        if not self.ready:
            self.ready = True
            self.console_log(
                f"bot is logged as {self.user}, with latency: {self.latency}")
        else:
            _log.info(f'{self.user} bot reconnected.')

    async def startup_tasks(self):
        """ startup tasks """
        self.taskrunner = CheckEconomyItems(self)
        _log.info("handling timers")
        self.emoji = Emojis(self)
        await self.emoji.initialise()

    async def initialise_database(self):
        """ make a database connection and run startup query"""
        self.database = Database(
            bot=self,
            user=USER,
            main_database=DBNAME,
            password=DB_PASSWORD,
            host=HOST,
        )
        self.database.startup_task = self.database_startup_tasks
        await self.database.initialize()
        self.db = self.pool = self.database_connection_pool \
            = self.database.database
        _log.info("database initialised")
    # Setup every tables :)

    async def database_startup_tasks(self):
        await self.database.create_table(
            table_name="peep.Guilds",
            columns="""
            guild_id              BIGINT NOT NULL,   
            PRIMARY KEY          (guild_id)
            """
        )
        await self.database.create_table(
            table_name="peep.Users",
            columns="""
            user_id      BIGINT NOT NULL,
            guild_id     BIGINT NOT NULL,
            FOREIGN KEY (guild_id) REFERENCES
            peep.Guilds(guild_id),
            PRIMARY KEY (guild_id,user_id)
            """
        )
        await self.database.create_table(
            table_name="peep.Channels",
            columns="""
            channel_id           BIGINT NOT NULL,
            guild_id             BIGINT NOT NULL,
            PRIMARY KEY          (guild_id,channel_id),
            FOREIGN KEY (guild_id) REFERENCES 
            peep.Guilds(guild_id)
            """
        )
        await self.database.create_table(
            table_name="peep.Gallery",
            columns=
            """
            channel_id           BIGINT NOT NULL,
            guild_id             BIGINT,
            FOREIGN KEY (channel_id,guild_id) REFERENCES 
            peep.Channels(channel_id,guild_id)
            """
        )
        # store the settings stats
        await self.database.create_table(
            table_name="peep.guild_settings",
            columns=
            """
            guild_id           BIGINT UNIQUE,
            prefix             varchar(20),
            vote               BIGINT,
            reaction_lstnr     BOOLEAN DEFAULT FALSE,
            thread_lstnr       BOOLEAN DEFAULT FALSE,
            oc_lstnr           BOOLEAN DEFAULT FALSE,
            vote_time          INTERVAL DEFAULT '1 hour',
            shoplog            BIGINT,
            MemeAdmin          BIGINT,
            customization_time BIGINT DEFAULT 5,
            economy            BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (guild_id) REFERENCES
            peep.Guilds(guild_id)
            """
        )
        await self.database.create_table(
            table_name="peep.channel_settings",
            columns=
            f"""
            guild_id             BIGINT NOT NULL,
            channel_id           BIGINT NOT NULL,
            like_emoji           varchar(256),
            dislike_emoji        varchar(256),
            is_memeChannel       boolean DEFAULT FALSE,
            is_threadChannel     boolean DEFAULT FALSE,
            is_deadChat          boolean DEFAULT FALSE,
            is_Gallery           boolean DEFAULT FALSE,
            is_ocChannel         boolean DEFAULT FALSE,
            is_voteChannel       boolean DEFAULT FALSE,
            NextLvl              BIGINT,
            max_like             INT DEFAULT 5,
            voting_time          INTERVAL DEFAULT NULL,
            thread_msg           varchar(500),
            UNIQUE               (guild_id,channel_id),
            FOREIGN KEY (guild_id) REFERENCES
            peep.Guilds(guild_id) ON DELETE CASCADE
            """
        )
        await self.database.create_table(
            table_name="peep.user_details",
            columns=
            """
            guild_id     BIGINT NOT NULL,
            user_id      BIGINT NOT NULL,
            likes        integer DEFAULT 0,
            points       FLOAT DEFAULT 0,
            FOREIGN KEY (user_id,guild_id) REFERENCES
            peep.Users(user_id,guild_id),
            UNIQUE      (guild_id,user_id)
            """
        )

        # manage shop items
        await self.database.create_table(
            table_name="peep.shop",
            columns=
            """
            guild_id           BIGINT NOT NULL,
            items              varchar(256),
            cost               FLOAT NOT NULL,
            emoji              varchar(256),
            expired            INTERVAL,
            FOREIGN KEY (guild_id) REFERENCES 
            peep.Guilds(guild_id) ON DELETE CASCADE,
            PRIMARY KEY		   (items)
            """
        )
        # user Inventory
        await self.database.create_table(
            table_name="peep.inventory",
            columns=
            """
            guild_id               BIGINT NOT NULL,
            user_id                BIGINT NOT NULL,
            items                  varchar(256) UNIQUE,
            expired                TIMESTAMP,
            FOREIGN KEY (items)    REFERENCES peep.shop(items)
            ON DELETE CASCADE ON   UPDATE CASCADE,
            FOREIGN KEY (user_id,guild_id)  
            REFERENCES peep.Users(user_id,guild_id)
            """
        )
        await self.database.create_table(
            table_name="peep.booster",
            columns=
            """
            guild_id      BIGINT UNIQUE,
            item_name     varchar(256),
            threshold     FLOAT,
            FOREIGN KEY (item_name) REFERENCES 
            peep.Shop(items) ON UPDATE CASCADE
            ON DELETE CASCADE,
            FOREIGN KEY (guild_id) REFERENCES
             peep.Guilds(guild_id) ON DELETE CASCADE
            """
        )
        await self.database.create_table(
            table_name="peep.shoplog",
            columns=
            """
            id           SERIAL PRIMARY KEY,
            guild_id     BIGINT NOT NULL,
            user_id      BIGINT NOT NULL,
            item_name    varchar(256),
            cost         FLOAT,
            expired_on   INTERVAL,
            purchased_at TIMESTAMP DEFAULT NOW(),
            FOREIGN KEY  (user_id,guild_id) REFERENCES
            peep.Users(user_id,guild_id)
            """
        )
        await self.database.create_table(
            table_name="peep.rolerewards",
            columns=
            """
            guild_id          BIGINT NOT NULL,
            likes             integer NOT NULL,
            role_id           BIGINT,
            FOREIGN KEY (guild_id) REFERENCES
            peep.Guilds(guild_id) ON DELETE CASCADE,
            UNIQUE            (guild_id,likes)
            """
        )
        with open(file="botconfig/database/triggers.sql", mode="r") as triggers:
            await self.database.db.execute(triggers.read())

    def console_log(self, message):
        """ prints to console """
        if self.logger:
            return self.logger.out(message=f"{self.user} > {message} \n")
        print(f"[{datetime.datetime.now().strftime(r'%D %I:%M %p')}]"
              f" > {self.user} > {message}")

    @staticmethod
    async def get_command_prefix(bot, message: discord.Message):
        """ Returns bot command prefix """
        prefixes = "%"
        print(bot)
        print(message)
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

    async def start(self) -> None:
        """ super method to run the bot"""
        await super().start(TOKEN, reconnect=True)

    async def close(self) -> None:
        """ do closeup task when bot closes """
        try:
            self.console_log(f"closing bot session")
            await self.aiohttp_session.close()
            await self.database.Cleanup()
        except Exception as e:
            print(e)
        try:
            self.console_log(f"closing the bot")
            await super().close()
        except Exception as e:
            print(e)

    """ Events """

    # do something on guild Join
    async def on_guild_join(self, guild):
        _log.info("joined guild : ", guild)

    async def on_guild_remove(self, guild):
        _log.info("left a guild : ", guild)

    async def on_resumed(self):
        """print when client resumed"""
        _log.info(f"{self.user} [resumed] with latency:{self.latency}")

    async def on_connect(self):
        """print when client connected to discord"""
        _log.info(
            f"{self.user} is connected successfully! latency: {self.latency}")

    async def on_disconnect(self):
        """print when client disconnected to discord"""
        self.console_log(
            f"{self.user} is disconnected! latency: {self.latency}")

    async def get_context(
            self, message, /, *, cls=Context.Context) -> Context.Context:
        """ overwrite the new bot context"""
        ctx = await super().get_context(message, cls=cls)
        return ctx

    async def on_message(self, message: discord.Message):
        """ called when the message is received process the commands"""
        await self.process_commands(message)


# get environment variables
TOKEN = os.environ.get('BETATOKEN')
APP_ID = os.environ.get('APPLICATION_ID')
DB_PASSWORD = os.environ.get('DBPASSWORD')
HOST = os.environ.get('DBHOST')
USER = os.environ.get('DBUSER')
DBNAME = os.environ.get('DBNAME')

