from __future__ import annotations

import json
import re
import math
import time
import logging
import unicodedata
from typing import TYPE_CHECKING, List, Optional, Union

import asyncpg
import discord
from dateutil.tz import tz
from discord.ext import commands
from discord.ext.commands.errors import MissingPermissions, NotOwner
from discord.ui import Button
from datetime import datetime, timedelta

from handler.Context import Context
from handler.errors import RoleNotFound

if TYPE_CHECKING:
    from pepebot import PepeBot
    from handler.view import interaction_error_button


async def error_embed(
        bot: PepeBot, Interaction: discord.Interaction, title: str = None, *,
        description: str = None, error_name=None, error_dis: str = None,
        colour: discord.Colour = None, timestamp=discord.utils.utcnow()):
    error_emoji = bot.failed_emoji
    right_emoji = bot.right

    if title is None:
        title = f"{error_emoji} ``OPERATION FAILED``"
    if not colour:
        colour = bot.embed_colour

    embed = discord.Embed(title=title, description=description,
                          timestamp=timestamp, colour=colour)

    if error_name and error_dis:
        error_name = f"__**{error_name}**__"
        error_dis = f"{right_emoji} {error_dis}"
        embed.add_field(name=error_name, value=error_dis)

    embed.set_footer(text='\u200b', icon_url=Interaction.user.avatar.url)
    view = interaction_error_button(Interaction)
    linkbutton = Button(url="https://sussybot.xyz", label="support",
                        style=discord.ButtonStyle.url)
    view.add_item(linkbutton)
    is_done = Interaction.response.is_done()
    if is_done:
        await Interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        await Interaction.response.send_message(embed=embed, view=view,
                                                ephemeral=True)

    view.message = await Interaction.original_message()
    return view.message


async def send_error(bot: PepeBot, ctx, *, msg: str = None) -> discord.Message:
    msg = msg if msg else f"something went wrong {bot.spongebob}"
    embed = discord.Embed(description=f"{bot.right} {msg}")
    return await ctx.reply(embed=embed)


def record_to_dict(Record: asyncpg.Record) -> dict:
    return dict(Record.items())


def records_to_dict(
        records: List[asyncpg.Record], remove_single: str = None
    ) -> List[Union[dict, any]]:
    data_columns = []
    for record in records:
        data_columns.append(
            record[remove_single] if remove_single else dict[record])
    return data_columns

async def heloo(ctx: discord.Interaction):
    return await ctx.response.send_message("hello world")


async def send_dm(member=discord.Member, *, message: str = None,
                  embed: discord.Embed = None,
                  view: discord.ui.View = None):
    logging.warning('create dm')
    channel = await member.create_dm()
    logging.warning('succes')
    return await channel.send(content=message, embed=embed, view=view)


def datetime_to_local_timestamp(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(
        now_timestamp)
    return round(int(time.mktime((utc_datetime + offset).timetuple())))


def format_ns(self, ns):
    if ns > 1000 ** 3:
        return f"{ns / 1000 ** 3} s"
    elif ns > 1000 ** 2:
        return f"{ns / 1000 ** 2} ms"
    elif ns > 1000:
        return f"{ns / 1000} µs"
    else:
        return f"{ns} ns"


def string_to_delta(Input: str):
    Input = Input.replace(" ", "")
    regex = re.compile(r'((?P<hours>\d+?)(hr|h|hour|hours))?'
                       r'((?P<minutes>\d+?)(m)|min|mins|minutes|minute)?'
                       r'((?P<seconds>\d+?)(s|sec|secs|second|seconds))?'
                       r'((?P<days>\d+?)(d|days|day))?'
                       r'((?P<weeks>\d+?)(w|week|weeks))?'
                       r'((?P<seconds_alone>\d+))?')
    group = regex.match(Input)
    parameters = group.groupdict().items()
    key_value_pair = {}
    for key, value in parameters:
        if key == "seconds_alone" and value is not None:
            key_value_pair["seconds"] = int(value)
        elif value:
            key_value_pair[key] = int(value)
    return timedelta(**key_value_pair)


async def is_user_mememanager(bot: PepeBot, ctx: Context,
                              member: discord.Member = None) -> bool:
    """ check if a user is a meme manager """
    member = member if member else ctx.author
    role = await bot.db.fetchval(
        """
        SELECT mememanager_role FROM test.setup WHERE guild_id1 = $1
        """, member.guild.id
    )
    role = ctx.guild.get_role(role) if role else None
    if member.id == ctx.guild.owner.id or member.id == await bot.is_owner(
            member):
        return True

    if role not in member.roles:
        return True

    return False


def is_meme_manager():
    """check if a user have meme manager role
    :raises roleNotfound: user doesn't have the role
    """

    async def predicate(ctx: Context) -> bool:
        role = await ctx.bot.database.select(
            ctx.guild.id,
            table_name="peep.guild_settings",
            columns="MemeAdmin",
            conditions="guild_id = $1")
        role = ctx.author.get_role(role) if role else None
        if ctx.author.id == ctx.guild.owner.id or \
                ctx.author.id == await ctx.bot.is_owner(ctx.author):
            return True
        if role:
            return True
        raise RoleNotFound()

    return commands.check(predicate)


def is_guild_owner():
    """ check if the user is guild owner """

    async def predicate(ctx: Context) -> bool:
        if await ctx.bot.is_owner(ctx.author):
            return True
        elif ctx.guild.owner_id == ctx.author.id:
            return True
        else:
            raise NotOwner()

    return commands.check(predicate)


async def user_check_self(bot: PepeBot, ctx: Context, member: discord.Member):
    if ctx.author.id == member.id or not await bot.is_owner(ctx.author):
        await send_error(
            bot=bot,
            ctx=ctx,
            msg="you cant add point to yourself, only owner can do it :o ")
        return


async def check_perm(
        ctx: Context, text_channel: discord.TextChannel,
        user: discord.User = None, *args):
    for i in args:
        print(i)
    # bot = ctx.guild.me
    # channel = text_channel
    # perm = channel.permissions_for(bot)


def get_relative_time(time: timedelta):
    if time <= timedelta(seconds=59):
        formate = f"{time.total_seconds()} secs"
    elif time <= timedelta(minutes=59):
        formate = f"{round(time.total_seconds() / 60)} mins"
    elif time <= timedelta(hours=24):
        formate = f"{round(time.total_seconds() / (60 * 60))} hours"
    elif time <= timedelta(days=6):
        formate = f"{math.floor(time.total_seconds() / (60 * 60 * 24))} days"
    elif time <= timedelta(days=31):
        formate = f"{math.floor(time.total_seconds() / (60 * 60 * 24 * 7))} weeks"
    elif time <= timedelta(days=365):
        formate = f"{round(time.total_seconds() / (60 * 60 * 24 * 30))} month"
    else:
        formate = f"{round(time.total_seconds() / (60 * 60 * 24 * 365))} years"
    return formate


class Emojis:
    """
    Emoji class for the bot
    some useful emojis attributes
    """
    emoji_404 = "<:404:975326725368066058>"
    goldenbughunter = "<:AYS_goldenbughunter:1001503524590465084>"
    Cancel = "<:Cancel:975326725426778184>"
    discord_staff = "<:DiscordStaff:1001503522501697717>"
    protect = "<:Protect:975326725502296104>"
    booster = "<:booster:1001501865692901386>"
    booster2 = "<:booster2:1001501867886530680>"
    booster3 = "<:booster3:1001501869635534939>"
    booster4 = "<:booster4:1001501871879499786>"
    botTag = "<:botTag:1001503528432439378>"
    bughunter = "<:bughunter:1001503525999755265>"
    cancel2 = "<:cancel2:975326725577801748>"
    certifiedmod = "<:certifiedmod:1001503531301355531>"
    channel = "<:channel:990574854027743282>"
    channel_bold = " <:channel:1001501875482398801>"
    chip = "<:chip:975326725430968330>"
    cloud = "<:cloud:975326725649096734>"
    database = "<:database:975326725699432458>"
    discord_emoji = "<:discord:1001501877990588437>"
    document = "<:document:975326725229641781>"
    document_1 = "<:document:975326725787508837>"
    doubleleft = "<:doubleleft:975326725456154644>"
    doubleright = "<:doubleright:975326725389037568>"

    download = "<:download:975326725435162666>"
    glass = "<:glass:975326725472944168>"
    good = "<:good:975326724747304992>"
    hypesquad = "<:hypesquad:1001501884294639709>"
    hypesquad_events_1 = "<:hypesquad_events:1001501882163941516>"

    # most used emojis
    channel_emoji = '<:channel:990574854027743282>'
    search_emoji = '<:icons8search100:975326725472944168>'
    failed_emoji = '<:icons8closewindow100:975326725426778184>'
    success_emoji = '<:icons8ok100:975326724747304992>'
    right = '<:right:975326725158346774>'
    left = "<:left:975326725565190194>"
    file_emoji = '<:icons8document100:975326725229641781>'
    moderator_emoji = "<:icons8protect100:975326725502296104>"
    spongebob = "<:AYS_sadspongebob:1005427777345949717>"
    doge = "<a:DogeDance:1005429259017392169>"
    like = '<:plusOne:1008402662070427668>'
    dislike = '<:dislike:1008403162874515649>'
    coin = '<a:coin1:1008074318082752583>'
    custom_pfp = '<:SDVchargunther:1008419132636663910>'
    shoutout = '<:AYS_WumpsShoutOut:1008421369379311767>'
    chect = '<:SDVitemtreasure:1008374574502658110>'
    basket = '<:SDVitemeggbasket:1007685896184811550>'
    iconsword = '<:SDViconsword:1007685391932981308>'
    samurai = '<:SDVjunimosamurai:1007685493909115040>'
    treasure = '<:SDVitemtreasure:1008374574502658110>'

    def __init__(self, bot):
        self.bot = bot
        self.default_emoji_url = (
            "https://gist.githubusercontent.com"
            "/Vexs/629488c4bb4126ad2a9909309ed6bd71"
            "/raw/edd5473221f42ea0f8b9de16545b4b853bf11140"
            "/emoji_map.json")
        self.default_emojis: Optional[dict] = None
        self.custom_emoji_regex = re.compile(
            r"<(?P<animated>a?):"
            r"(?P<name>[a-zA-Z0-9_]{2,32}):"
            r"(?P<id>[0-9]{18,22})>")

    async def initialise(self):
        self.default_emojis = await self.get_unicode_emojis()

    def get_emoji_id(self, emoji_string: str):
        emoji = self.custom_emoji_regex.match(emoji_string)
        if emoji is not None:
            emoji_metadata = emoji.groupdict()
            return int(emoji_metadata["id"])
        return

    @staticmethod
    def is_default_emoji(string: str) -> bool:
        if string is None:
            return False
        string = string.replace(" ", "")
        atIndex1 = string[0]
        if not atIndex1:
            return False
        unicode_type = unicodedata.category(atIndex1)
        if unicode_type == "So":
            return True
        return False

    def is_custom_emoji(self, string: str) -> bool:
        if string is None:
            return False
        string = string.replace(" ", "")
        is_custom_emoji = self.custom_emoji_regex.match(string)
        return is_custom_emoji is not None

    async def get_unicode_emojis(self) -> Optional[dict]:
        response = await self.bot.aiohttp_session.get(
            url=self.default_emoji_url)
        Json = json.loads(await response.text())
        print(Json)
        return Json

    def get_emoji_name(self, unicode_moji: str) -> Optional[str]:
        emoji_lists = self.default_emojis
        for name, emoji in emoji_lists.items():
            if emoji == unicode_moji:
                return name

    def getEmojiByName(self, name: str) -> Optional[str]:
        return self.default_emojis.get(name)


class Colour:
    bot_color = 0xa68ee3
    pink_color = 0xff0f8c
    blue_color = 0x356eff
    embed_colour = 0x2E3136
    cyan_color = 0x00ffad
    white_color = 0xffffff
    black_color = 0x000000
    youtube_color = 0xcd201f
    violet_color = 0xba9aeb
    green_color = 0x00ff85
    yellow_color = 0xffe000
    embed_default_colour = 0x00ffad
    dark_theme_colour = 0x36393e


def utc_to_local(utc: datetime):
    from_zone = tz.gettz('UTC')
    to_zone = tz.tzlocal()
    utctime = utc.replace(tzinfo=from_zone)
    local = utctime.astimezone(to_zone)
    return local


def get_place_holders(max: int):
    placeholders = ""
    for i in range(1, max + 1):
        comma_or_not = ", " if i != max else ""
        current_holder = f"${i}" + comma_or_not
        placeholders += current_holder
    return placeholders


def get_key_pair(Keys: List[str], start_at: int = None):
    """ returns string with their
    key and value placeholders pair"""
    key_value_pair = ""
    Counter = start_at if start_at else 1
    listCounter = 0
    for key in Keys:
        listCounter += 1
        comma_or_not = ", " if listCounter != len(Keys) else ""
        current_pair = f"{key} = ${Counter}" + comma_or_not
        key_value_pair += current_pair
        Counter += 1
    return key_value_pair


def to_string_list(keys: List[str]):
    """ return a string made of keys order by order"""
    key_str = " "
    Counter = 0
    for key in keys:
        Counter += 1
        comma_or_not = ", " if Counter != len(keys) else ""
        current_str = key + comma_or_not
        key_str += current_str
    return key_str


def get_attachments(message: discord.Message, links: bool = False):
    AllowedTypes = ("image", "video")
    attachments = message.attachments
    embeds = message.embeds
    if (not attachments or len(attachments) == 0) \
            and (not embeds or len(embeds) == 0):
        return
    Resolved_Attachments = []
    for image in attachments:
        if image.content_type is None:
            return Resolved_Attachments
        if image.content_type.startswith(AllowedTypes):
            Resolved_Attachments.append(image)

    if links:
        for embed in embeds:
            if embed.image:
                Resolved_Attachments.append(embed.image)
            elif embed.image:
                Resolved_Attachments.append(embed.video)

    return Resolved_Attachments