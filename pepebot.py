"""
:author: 0xgreenapple
:copyright: (c) 0xgreenapple(xgreenapple)
:licence: MIt.
"""

__title__ = 'Peep-bot'
__author__ = '0xgreenapple'
__copyright__ = 'MIT Copyright 0xgreenapple'
__version__ = '2.0.0'

import json
import logging
import time
import asyncio
import datetime
import typing
import aiohttp

import discord
from discord.ext import commands, tasks

import os
from collections import Counter
from itertools import cycle
from platform import python_version
from typing import Optional, Union

from handler import context
from handler.blocking_code import Executor
from handler.economy import Economy
from handler.utils import Emojis, Colour
from handler.logger import Logger
from handler.tasks import CheckEconomyItems
from handler.cache import GuildCache
from handler.database import Database, get_guild_settings
from handler.view import ItemLogMessage
from handler.youtube import Youtube

_log = logging.getLogger("pepebot")


class PepeBot(commands.Bot):
    """PepeBot 2.0 interface"""
    user: discord.ClientUser
    bot_app_info: discord.AppInfo
    owner: 888058231094665266
    session: aiohttp.ClientSession

    def __init__(self):
        self.COGS = [
            'duel',
            'help',
            'economy',
            'error_handler',
            'listeners',
            "memes",
            'setup'
        ]
        self.ready = False
        self.statues = cycle(
            ["peep"])
        self.online_time = datetime.datetime.utcnow()
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
            max_messages=10000
        )
        self.reconnected_at: time = None
        # variables
        self.version = "2.0.0"
        self.emoji: Optional[Emojis] = None
        self.colors = Colour()
        self.spam_count = Counter()
        self.cache: GuildCache = GuildCache()
        self._app_info: Optional[discord.AppInfo] = None
        self.taskrunner: Optional[CheckEconomyItems] = None
        self.executor: Optional[Executor] = None
        self.owner_id = 888058231094665266
        self.logger: typing.Optional[Logger] = None
        self.aiohttp_session: Optional[aiohttp.ClientSession] = None
        self.spam_cooldown = commands.CooldownMapping.from_cooldown(
            5.0, 6.0, commands.BucketType.user)
        self.youtube = Youtube(bot=self, public_access=True)
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
        self.economy = Economy(bot=self)



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
        self.session = self.aiohttp_session = aiohttp.ClientSession(
            loop=self.loop)
        # initialise bot application info
        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id
        self.executor = Executor(self.loop)
        # initialise database
        await self.initialise_database()
        self.loop.create_task(
            self.initialise_youtube_api(), name="Initialise youtube api")
        self.loop.create_task(
            self.startup_tasks(), name="Bot startup tasks")
        self.console_log("loading cogs..")
        for cog in self.COGS:
            await self.load_extension(f"cogs.{cog}")
            self.console_log(f"{cog} loaded ")
        # add views
        self.add_view(ItemLogMessage(bot=self))
        self.console_log("bot initialised")

    async def on_ready(self):
        self.change_status.start()
        _log.info(
            f"is shard rate limited? :{self.is_ws_ratelimited()}")
        # set self.ready to true and sent the console message
        if not self.ready:
            self.ready = True
            _log.info(
                f"bot logged as {self.user} "
                f"took {(datetime.datetime.utcnow() - self.online_time).seconds}"
                f" seconds")
        else:
            self.reconnected_at = time.time()
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
        self.economy.database = self.database
        _log.info("database initialised")

    async def initialise_youtube_api(self):
        self.youtube.executor = self.executor
        apikey = os.environ.get("YOUTUBE_API_KEY")
        self.youtube.auth.dev_key = apikey
        await self.youtube.initialise()
        self.youtube.watch_for_uploads.start()

    async def database_startup_tasks(self):
        await self.database.create_schema(schema_name="peep")
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
            prefix             varchar(20) DEFAULT '$',
            vote               BIGINT,
            reaction_lstnr     BOOLEAN DEFAULT FALSE,
            thread_lstnr       BOOLEAN DEFAULT FALSE,
            oc_lstnr           BOOLEAN DEFAULT FALSE,
            vote_time          INTERVAL DEFAULT '1 hour',
            shoplog            BIGINT,
            MemeAdmin          BIGINT,
            customization_time BIGINT DEFAULT 5,
            economy            BOOLEAN DEFAULT FALSE,
            dm_on_accept       BOOLEAN DEFAULT FALSE,
            upload_channel     BIGINT,
            upload_ping        BIGINT,
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
            id                 SERIAL PRIMARY KEY,
            guild_id           BIGINT NOT NULL,
            user_id            BIGINT NOT NULL,
            item_name          varchar(256),
            cost               FLOAT,
            expired_on         TIMESTAMP,
            is_accepted        BOOLEAN DEFAULT FALSE,
            log_message_id     varchar(256),
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
        await self.database.create_table(
            table_name="peep.meme_completed_messages",
            columns=
            """
            guild_id             BIGINT,
            channel_id           BIGINT,
            message_id           BIGINT UNIQUE,
            expiry               TIMESTAMP,
            FOREIGN KEY (guild_id,channel_id) REFERENCES
            peep.Channels(guild_id,channel_id) ON DELETE CASCADE
            """
        )
        await self.database.create_table(
            table_name="peep.youtube_uploads",
            columns=
            """
            guild_id              BIGINT UNIQUE,
            channel_id            varchar(256),
            channel_name          TEXT,
            recent_upload_id      varchar(500)
            """
        )
        await self.database.create_table(
            table_name="peep.bot_config",
            columns=
            """
            log_channel      BIGINT,
            status_channel   BIGINT
            """
        )

    def console_log(self, message):
        """ prints to console """
        if self.logger:
            return self.logger.out(message=f"{self.user} > {message} \n")
        print(f"[{datetime.datetime.now().strftime(r'%D %I:%M %p')}]"
              f" > {self.user} > {message}")

    @staticmethod
    async def get_command_prefix(bot, message: discord.Message):
        guild = message.guild
        guild_settings = await get_guild_settings(bot=bot, guild_id=guild.id)
        prefix = guild_settings['prefix'] if guild_settings else None
        return prefix if prefix else "$"

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
            await self.database.close()
            await self.taskrunner.CleanUp()
            await self.executor.shutdown()
        except Exception as e:
            _log.info(e)
        try:
            await super().close()
        except Exception as e:
            print(e)

    async def on_guild_join(self, guild: discord.Guild):
        _log.info("joined guild : " + guild.name)

    async def on_guild_remove(self, guild: discord.Guild):
        _log.info("left a guild : " + guild.name)

    async def on_resumed(self):
        _log.info(f"{self.user} [resumed]")

    async def on_connect(self):
        _log.info(
            f"{self.user} is connected successfully!")

    async def on_disconnect(self):
        _log.warning(
            f"{self.user} is disconnected!")

    async def get_context(
            self, message, /, *, cls=context.Context) -> context.Context:
        ctx = await super().get_context(message, cls=cls)
        return ctx

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        await self.process_commands(message)


# get environment variables
TOKEN = os.environ.get('BETATOKEN')
APP_ID = os.environ.get('APPLICATION_ID')
DB_PASSWORD = os.environ.get('DBPASSWORD')
HOST = os.environ.get('DBHOST')
USER = os.environ.get('DBUSER')
DBNAME = os.environ.get('DBNAME')