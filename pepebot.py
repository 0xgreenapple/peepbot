"""
Peepbot main runner
~~~~~~~~~~~~~~~~~~~
starter of the peep bot for discord py
:copyright: (c) xgreenapple
:license: MIT.
"""

__title__ = 'Peepbot-bot'
__author__ = 'xgreenapple'
__copyright__ = 'Copyright xgreenapple'
__version__ = '0.0.2a'

import logging
import os
import time
import asyncio
import datetime
import typing
from collections import Counter

import aiohttp
import discord

from itertools import cycle
from platform import python_version
from discord.ext import commands, tasks

from handler import Context
from handler.database import database

log = logging.getLogger(__name__)


# Bot main class inheritance of discord py bot class
class pepebot(commands.Bot):
    """peep-bot v0.0.2a Interface
    """

    user: discord.ClientUser
    bot_app_info: discord.AppInfo
    owner: 888058231094665266

    # constructor
    def __init__(self):
        self.aiohttp_session = None
        allowed_mentions = discord.AllowedMentions(roles=True, everyone=False, users=True)
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

            application_id=appid,
            help_command=None,

        )
        # variables

        self.online_time = datetime.datetime.now(datetime.timezone.utc)
        self.spam_cooldown = commands.CooldownMapping.from_cooldown(5.0, 6.0, commands.BucketType.user)
        self.spam_count = Counter()
        self.version = "0.0.1a"
        self.owner_id = 888058231094665266
        self.message_prefix_s = "peep bot"
        self.bot_user_agent = "pepe (Discord Bot)"
        self.user_agent = (
            "peep "
            f"Python/{python_version()} "
            f"aiohttp/{aiohttp.__version__}"
            f"discord.py/{discord.__version__}"
        )

        # colours
        self.bot_color = 0xa68ee3
        self.pink_color = 0xff0f8c
        self.blue_color = 0x356eff
        self.embed_colour = 0x2E3136
        self.cyan_color = 0x00ffad
        self.white_color = 0xffffff
        self.black_color = 0x000000
        self.youtube_color = 0xcd201f
        self.violet_color = 0xba9aeb
        self.green_color = 0x00ff85
        self.yellow_color = 0xffe000
        self.embed_default_colour = 0x00ffad
        self.dark_theme_colour = 0x36393e

        # Emojis
        self.channel_emoji = '<:channel:990574854027743282>'
        self.search_emoji = '<:icons8search100:975326725472944168>'
        self.failed_emoji = '<:icons8closewindow100:975326725426778184>'
        self.success_emoji = '<:icons8ok100:975326724747304992>'
        self.right = '<:right:975326725158346774>'
        self.file_emoji = '<:icons8document100:975326725229641781>'
        self.moderator_emoji = "<:icons8protect100:975326725502296104>"
        self.spongebob = "<:AYS_sadspongebob:1005427777345949717>"
        self.doge = "<a:DogeDance:1005429259017392169>"
        self.like = '<:plusOne:1008402662070427668>'
        self.dislike = '<:dislike:1008403162874515649>'
        self.coin = '<a:coin1:1008074318082752583>'
        self.custom_pfp = '<:SDVchargunther:1008419132636663910>'
        self.shoutout = '<:AYS_WumpsShoutOut:1008421369379311767>'
        self.chect = '<:SDVitemtreasure:1008374574502658110>'

        self.db = self.database = self.database_connection_pool = None
        self.Database: typing.Optional[database] = None
        self.connected_to_database = asyncio.Event()
        self.connected_to_database.set()

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
        # the list of cogs that will being initialize late
        COGS = ['duel', 'setup', 'help', 'creation', 'economy', 'server', 'error handler', 'listeners']
        self.console_log("loading cogs..")

        for cog in COGS:
            await self.load_extension(f"cogs.{cog}")
            self.console_log(f"{cog} loaded ")
        self.console_log("setup hook complete")
        await self.tree.sync()

    # setup database and create tables
    # async def connect_to_database(self):
    #     if self.database_connection_pool:
    #         return
    #     if self.connected_to_database.is_set():
    #         self.connected_to_database.clear()
    #         self.db = self.database = self.database_connection_pool = await create_database_pool()
    #         self.connected_to_database.set()
    #     else:
    #         await self.connected_to_database.wait()

    # setup database and create tables
    async def initialize_database(self):
        # await self.connect_to_database()

        await self.Database.CreateSchema(schema_name="test")
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
        await self.Database.CreateTable(
            table_name="test.inv",
            columns=
            """
                guild_id           BIGINT,
                user_id            BIGINT,
                items              TEXT,
                PRIMARY KEY		   (items),
                FOREIGN KEY (items) REFERENCES test.shop(items) 
                ON DELETE CASCADE ON UPDATE CASCADE
            """
        )

    def console_log(self, message):
        print(f"[{datetime.datetime.now().strftime(r'%D %I:%M %p')}] > {self.user} > {message}")

    # app info
    @property
    async def app_info(self):
        if not hasattr(self, "_app_info"):
            self._app_info = await self.application_info()
        return self._app_info

    # return the bot owner
    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner

    async def dm_member(
            self, user: discord.Member, *args, message=None,
            embed=None, file=None, view=None, **kwargs):
        """deprecated"""
        channel = await user.create_dm()
        await channel.send(content=message, embed=embed, file=file, view=view)

    @staticmethod
    async def get_command_prefix(bot, message: discord.Message):
        prefixes = "$"
        return prefixes if prefixes else "$"

    async def on_ready(self):
        self.console_log(f"is shard is rate limited? :{self.is_ws_ratelimited()}")
        if not hasattr(self, 'uptime'):
            self.startTime = time.time()
        if not self.ready:
            self.ready = True
            self.console_log(f"bot is logged as {self.user}")
        else:
            self.console_log(f'{self.user}bot reconnected.')

    # change status every 15 minutes
    @tasks.loop(minutes=15)
    async def change_status(self):
        await self.change_presence(status=discord.Status.online,
                                   activity=discord.Activity(
                                       type=discord.ActivityType.listening,
                                       name=next(self.statues)))

    # events
    async def on_guild_join(self, guild):
        print(guild)

    async def on_guild_remove(self, guild):
        print(guild)

    async def startup_tasks(self):
        await self.wait_until_ready()
        await self.change_status.start()

    async def start(self) -> None:
        await super().start(token, reconnect=True)

    async def close(self) -> None:
        try:
            self.console_log(f"closing bot session")
            await self.aiohttp_session.close()
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

    # shutdown task
    async def shutdown_tasks(self):
        """shutdown the database connection"""
        # Close database connection

    async def get_context(self, message, /, *, cls=Context.Context) -> Context.Context:
        """overwrite the context"""
        ctx = await super().get_context(message, cls=cls)
        return ctx

    async def on_message(self, message):
        """process the command"""
        await self.process_commands(message)


token = os.environ.get('BETATOKEN')
print(token)
appid = os.environ.get('APPLICATION_ID')
password = os.environ.get('DBPASSWORD')
host = os.environ.get('DBHOST')
USER = os.environ.get('DBUSER')
DBNAME = os.environ.get('DBNAME')
