"""
peepbot main runner
~~~~~~~~~~~~~~~~~~~
starter of the peep bot for discord py
that start the bot and connect to discord gateway.
:copyright: (c) xgreenapple
:license: MIT.
"""

__title__ = 'Sussy-bot'
__author__ = 'xgreenapple'
__copyright__ = 'Copyright xgreenapple'
__version__ = '0.0.2a'

import logging
import os
import time
import asyncio
import datetime
from collections import Counter

import aiohttp
import discord

from itertools import cycle
from platform import python_version
from discord.ext import commands, tasks

from handler import Context
from handler.database import create_database_pool

"""this is the main file that run the bot"""
log = logging.getLogger(__name__)


# class bot the main code
class pepebot(commands.Bot):
    """Sussy-bot v0.0.2a Interface
    """

    user: discord.ClientUser
    bot_app_info: discord.AppInfo
    owner: 888058231094665266

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

            ),

            application_id=958334261541343262,
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

        self.db = self.database = self.database_connection_pool = None
        self.connected_to_database = asyncio.Event()
        self.connected_to_database.set()

    async def setup_hook(self) -> None:
        self.aiohttp_session = aiohttp.ClientSession(loop=self.loop)
        self.console_log("client session start")
        self.bot_app_info = await self.application_info()
        self.owner_id = self.bot_app_info.owner.id
        self.console_log("setting up database")
        await self.initialize_database()
        self.console_log("database setup done")

        self.loop.create_task(
            self.startup_tasks(), name="Bot startup tasks"
        )
        COGS = ['duel','setup1','help','creation','error handler']
        self.console_log("loading cogs..")
        for cog in COGS:
            await self.load_extension(f"cogs.{cog}")
            self.console_log(f"{cog} loaded ")
        self.console_log("setup hook complete")
        await self.tree.sync()

    # setup database and create tables
    async def connect_to_database(self):
        if self.database_connection_pool:
            return
        if self.connected_to_database.is_set():
            self.connected_to_database.clear()
            self.db = self.database = self.database_connection_pool = await create_database_pool()
            self.connected_to_database.set()
        else:
            await self.connected_to_database.wait()

    # setup database and create tables
    async def initialize_database(self):
        await self.connect_to_database()
        await self.db.execute("CREATE SCHEMA IF NOT EXISTS test")
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS test.duel(
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
            )
        """)

        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS test.leaderboard(
                guild_id1     BIGINT NOT NULL,
                user_id1      BIGINT NOT NULL,
                likes         BIGINT DEFAULT 0,
                 PRIMARY KEY (guild_id1,user_id1)
            )
        """)

        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS test.setup(
                guild_id1     BIGINT NOT NULL,
                announcement      BIGINT,
                vote              BIGINT,
                vote_time         BIGINT DEFAULT 10,
                customization_time BIGINT DEFAULT 5,
                PRIMARY KEY (guild_id1)
            )
        """)

    def console_log(self, message):
        print(f"[{datetime.datetime.now().strftime(r'%D %I:%M %p')}] > {self.user} > {message}")

    # do ready tasks
    @property
    async def app_info(self):
        if not hasattr(self, "_app_info"):
            self._app_info = await self.application_info()
        return self._app_info

    @property
    def owner(self) -> discord.User:
        return self.bot_app_info.owner

    async def dm_member(self, user: discord.Member, *args, message=None, embed=None, file=None, view=None, **kwargs):
        channel = await user.create_dm()
        await channel.send(content=message, embed=embed, file=file, view=view)

    @staticmethod
    async def get_command_prefix(bot, message: discord.Message):
        prefixes = "$"

        return prefixes if prefixes else "$"

    # the code that change bot status in every hour.
    async def on_ready(self):
        self.console_log(f"is shard is rate limited :{self.is_ws_ratelimited()}")

        if not hasattr(self, 'uptime'):
            self.startTime = time.time()
        if not self.ready:
            self.ready = True
            self.console_log(f"bot is logged as {self.user}")
        else:
            self.console_log(f'{self.user}bot reconnected.')

    @tasks.loop(minutes=15)
    async def change_status(self):
        await self.change_presence(status=discord.Status.online,
                                   activity=discord.Activity(
                                       type=discord.ActivityType.listening,
                                       name=next(self.statues)), )

    # load the prefix on guild join
    async def on_guild_join(self, guild):  # when the bot joins the guild
        print(guild)

    # pop the guild prefix on leaving from the guild
    async def on_guild_remove(self, guild):
        print(guild)

    async def startup_tasks(self):
        await self.wait_until_ready()
        await self.change_status.start()

    async def start(self) -> None:
        await super().start(token, reconnect=True, )

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

    # bot monitor
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
        ctx = await super().get_context(message, cls=cls)
        return ctx

    # this is the code that make the bot automatically response on ping
    async def on_message(self, message):

        await self.process_commands(message)


token = os.environ.get('BETATOKEN')
