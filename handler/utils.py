from __future__ import annotations

import time
import logging

import discord
from discord.ui import Button
from datetime import datetime, timedelta

from handler.view import interaction_error_button
from handler.Context import Context
from pepebot import pepebot


async def error_embed(
        bot: pepebot, Interaction: discord.Interaction, title: str = None, *,
        description: str = None, error_name=None, error_dis: str = None,
        colour: discord.Colour = None, timestamp=discord.utils.utcnow()):
    error_emoji = bot.failed_emoji
    right_emoji = bot.right

    if title is None:
        title = f"{error_emoji} ``OPERATION FAILED``"
    if not colour:
        colour = bot.embed_colour

    embed = discord.Embed(title=title, description=description, timestamp=timestamp, colour=colour)

    if error_name and error_dis:
        error_name = f"__**{error_name}**__"
        error_dis = f"{right_emoji} {error_dis}"
        embed.add_field(name=error_name, value=error_dis)

    embed.set_footer(text='\u200b', icon_url=Interaction.user.avatar.url)
    view = interaction_error_button(Interaction)
    linkbutton = Button(url="https://sussybot.xyz", label="support", style=discord.ButtonStyle.url)
    view.add_item(linkbutton)
    is_done = Interaction.response.is_done()
    if is_done:
        await Interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        await Interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    view.message = await Interaction.original_message()
    return view.message


async def send_error(bot: pepebot, ctx, *, msg: str = None) -> discord.Message:
    msg = msg if msg else f"something went wrong {bot.spongebob}"
    embed = discord.Embed(description=f"{bot.right} {msg}")
    return await ctx.reply(embed=embed)


async def heloo(ctx: discord.Interaction):
    return await ctx.response.send_message("hello world")


async def send_dm(member=discord.Member, *, message: str = None, embed: discord.Embed = None,
                  view: discord.ui.View = None):
    logging.warning('create dm')
    channel = await member.create_dm()
    logging.warning('succes')
    return await channel.send(content=message, embed=embed, view=view)


def datetime_to_local_timestamp(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
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


def string_to_delta(input):
    if input is None:
        return
    slice_num = -1
    slice_object = slice(-1)
    time_in_delta = None
    input = input.lower()

    try:
        int(input[slice_object])
    except ValueError:
        return

    if input.endswith('d'):
        ab = slice(slice_num)
        a = input[ab]
        time_in_delta = timedelta(days=int(a))
    if input.endswith('h'):
        ab = slice(slice_num)
        a = input[ab]
        time_in_delta = timedelta(hours=int(a))
    if input.endswith('m'):
        ab = slice(slice_num)
        a = input[ab]
        time_in_delta = timedelta(minutes=int(a))
    if input.endswith('s'):
        ab = slice(slice_num)
        a = input[ab]
        time_in_delta = timedelta(seconds=int(a))
    time_in_delta = time_in_delta
    return time_in_delta


async def if_user_mememanager(bot: pepebot, ctx: Context, member: discord.Member = None) -> bool:
    """ check if a user is a meme manager """
    member = member if member else ctx.author
    print(member.name)
    role = await bot.db.fetchval(
        """
        SELECT mememanager_role FROM test.setup WHERE guild_id1 = $1
        """, member.guild.id
    )
    role = ctx.guild.get_role(role) if role else None

    # check the member has meme manager role if not owner
    if not member.id == ctx.guild.owner.id \
            or not member.id == await bot.is_owner(member):
        print("something is happening")
        if role not in member.roles:
            return True

    return False


async def user_check_self(bot:pepebot,ctx:Context, member:discord.Member) :
    if ctx.author.id == member.id or not await bot.is_owner(ctx.author):
        await send_error(
            bot=bot,
            ctx=ctx,
            msg="you cant add point to yourself, only owner can do it :o ")
        return


async def check_perm(
        ctx: Context, text_channel: discord.TextChannel, user: discord.User = None, *args):
    for i in args:
        print(i)
    # bot = ctx.guild.me
    # channel = text_channel
    # perm = channel.permissions_for(bot)
