import asyncio
import io
import os
import random
import typing
from datetime import datetime, timedelta
from io import BytesIO
import re
import aiohttp
import discord
from discord import errors
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown
from typing import TYPE_CHECKING
from pepebot import pepebot
from handler.Context import Context
from handler.pagination import SimplePages
from handler.view import duel_button, thread_channel
import logging


class leaderboard(SimplePages):
    def __init__(self, entries: list, *, ctx: Context, per_page: int = 12, title: str = None):
        converted = entries
        print(entries)
        super().__init__(converted, per_page=per_page, ctx=ctx)


async def handle_roles(bot: pepebot, message: discord.Message, reward_channel: int, user_limit: int, limits: list,
                       roles: list):
    print('i m here')
    if reward_channel:
        print('reward')

        if reward_channel == message.channel.id:
            print('hellooo')

            await bot.db.execute(
                """
                INSERT INTO peep.msg(guild_id,channel_id,user_id,limit1)
                VAlUES($1,$2,$3,$4)
                ON CONFLICT(guild_id,channel_id,user_id) DO
                UPDATE SET limit1 =  COALESCE(msg.limit1, 0) + $4 ;
                """, message.guild.id, message.channel.id, message.author.id, 1
            )
            if limits:
                print('limits')

                user_role1 = None
                user_role2 = None
                user_role3 = None
                if roles[0]:
                    user_role1 = message.author.get_role(roles[0])
                if roles[1]:
                    user_role2 = message.author.get_role(roles[1])
                if roles[2]:
                    user_role3 = message.author.get_role(roles[2])

                if limits[0] and user_limit >= limits[0]:
                    print('adding')
                    if not user_role1:
                        if roles[0]:
                            role1 = message.guild.get_role(roles[0])
                            if role1:
                                await message.author.add_roles(role1)
                if limits[1] and user_limit >= limits[1]:
                    print('adding1')

                    if not user_role2:
                        if roles[1]:
                            role2 = message.guild.get_role(roles[1])
                            if role2:
                                await message.author.add_roles(role2)
                if limits[2] and user_limit >= limits[2]:
                    print('adding2')

                    if not user_role3:
                        if roles[2]:
                            role3 = message.guild.get_role(roles[2])
                            if role3:
                                await message.author.add_roles(role3)


async def handle_gallery(bot: pepebot, message: discord.Message, announcement_id: int, _is_gallery=False):
    vote_time = await bot.db.fetchval(
        """SELECT vote_time FROM peep.setup
        WHERE guild_id=$1""", message.guild.id
    )
    vote_time = vote_time if vote_time else 18

    reaction_count1 = await bot.db.fetchval(
        """SELECT likes FROM peep.likes 
        WHERE guild_id=$1 AND channel = $2""", message.guild.id, message.channel.id
    )
    reaction_count1 = reaction_count1 if reaction_count1 else 2

    def check(reaction, user):
        count = 0
        reaction_count = 0
        for reaction in message.reactions:
            if reaction.emoji.id == 1008402662070427668:
                reaction_count = reaction.count
                break

        return reaction_count >= reaction_count1

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=vote_time * 60,
                                            check=check)
    except asyncio.TimeoutError:
        pass
    else:

        reaction_count = 0
        for reaction in message.reactions:
            if reaction.emoji.id == 1008402662070427668:
                reaction_count = reaction.count
                break
        await bot.db.execute(
            """
                    INSERT INTO peep.leaderboard(user_id,guild_id,likes)
                    VALUES($1,$2,$3)
                    ON CONFLICT (guild_id,user_id) DO
                    UPDATE SET likes = COALESCE(leaderboard.likes, 0) + $3 ;
                    """, message.author.id, message.guild.id, reaction_count
        )
        channel = message.guild.get_channel(announcement_id)
        if channel:
            if len(message.attachments):
                if message.attachments[0].content_type.startswith('image') or \
                        message.attachments[0].content_type.startswith('video'):
                    file = await message.attachments[0].to_file()
                    await channel.send(f"by {message.author.mention}",
                                       file=file)
            elif len(message.embeds):
                if message.embeds[0].type == 'image' or \
                        message.embeds[0].type == 'video' or \
                        message.embeds[0].type == 'gifv':
                    a = message.embeds[0]
                    session: aiohttp.ClientSession = bot.aiohttp_session
                    e = await session.get(url=a.url)
                    a = await e.read()

                    if e.content_type.endswith('gif'):
                        fileext = '.gif'
                    else:
                        fileext = '.png'
                    if _is_gallery:
                        await channel.send(
                            content=message.content,
                            file=discord.File(fp=io.BytesIO(a),
                                              filename=f'{bot.user.name}{fileext}'))
                    else:
                        await channel.send(
                            content=f"by {message.author.mention}",
                            file=discord.File(fp=io.BytesIO(a),
                                              filename=f'{bot.user.name}{fileext}'))


async def GetAttachments(message: discord.Message, links: bool = False):
    AllowedTypes = ("Image", "video")
    attachments = message.attachments
    embeds = message.embeds
    if (not attachments or len(attachments) == 0) \
            or (not embeds or len(embeds) == 0):
        return
    Resolved_Attachments = []
    for image in attachments:
        if image.content_type.startswith(AllowedTypes):
            Resolved_Attachments.append(image)

    if links:
        for embed in embeds:
            if embed.image:
                Resolved_Attachments.append(embed.image)
            elif embed.image:
                Resolved_Attachments.append(embed.video)

    return Resolved_Attachments


async def AddLikes(bot: pepebot, user: discord.Member):
    await bot.Database.Insert(
        user.id,
        user.guild.id,
        table="peep.leaderboard",
        columns="user_id,guild_id,likes",
        values="$1,$2,$3",
        on_Conflicts="(user_id,guild_id) DO UPDATE SET likes = COALESCE(leaderboard.likes, 0) + 1"
    )


async def HandleThreadEvents():
    ...


class listeners(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot
        self.MsgLikes = {}
        self.Database = self.bot.Database

    @commands.Cog.listener('on_message')
    async def memes(self, message: discord.Message):

        if message.type != discord.MessageType.default:
            return

        if message.author.bot:
            return

        channel = await self.bot.db.fetchval("""SELECT meme_channel FROM peep.channels WHERE guild_id =$1""",
                                             message.guild.id)
        is_disabled = await self.bot.db.fetchval("""SELECT listener FROM peep.setup WHERE guild_id =$1""",
                                                 message.guild.id)
        if not is_disabled:
            return
        if not channel:
            return

        has_attachment = False
        has_embed = False

        if len(message.attachments):
            has_attachment = True

        elif len(message.embeds):
            for embed in message.embeds:
                if embed.type == 'image':
                    has_embed = True
                    break
        else:
            return

        if has_attachment or has_embed:
            message_check = re.sub(r'[^A-Za-z0-9]', '', message.content)
            if message_check.lower() == 'oc':
                pinned_msg = await message.channel.pins()
                if len(pinned_msg) == 50:
                    await pinned_msg[-1].unpin(reason='removing old pins')
                await message.pin(reason='original content')

    @commands.Cog.listener('on_message')
    async def thread_create(self, message: discord.Message):

        # check if the message is normal
        if message.type != discord.MessageType.default:
            return
        if message.author.bot:
            return

        Setup = await self.bot.Database.Select(
            message.guild.id,
            table="peep.setup",
            columns="thread_ls, mememanager_role",
            condition="guild_id=$1",
            row=True
        )
        is_enabled = Setup["thread_ls"]
        MemeManagerRole = Setup["mememanager_role"]
        if not is_enabled:
            return

        Channel_settings = await self.bot.Database.Select(
            message.guild.id,
            message.channel.id,
            table="peep.thread_channel",
            columns="channel_id,msg",
            condition="guild_id =$1 and channel_id = $2",
            row=True
        )

        ThreadChannelID = Channel_settings["channel_id"]
        MessageText = Channel_settings["msg"]

        if not ThreadChannelID:
            return

        Attachment = await GetAttachments(message=message)
        if not Attachment and len(Attachment) == 0:
            return

        Name = None

        thread = await message.channel.create_thread(
            name=f"{message.author.name} ({message.created_at.microsecond})",
            message=message, auto_archive_duration=60)

        rolemention = message.guild.get_role(rolemention)

        rolemention = rolemention.mention if rolemention else message.author.mention
        msg = msg if msg else f" {rolemention} Make Sure the meme is **original**"
        view = thread_channel(user=message.author)
        message = await thread.send(msg, view=view)
        return message

    @commands.Cog.listener('on_message')
    async def likes_handler(self, message: discord.Message):
        # return if system message
        if message.channel.type != discord.ChannelType.text:
            return
        if message.type != discord.MessageType.default:
            return
        if message.author.bot:
            return

        Attachments = await GetAttachments(message=message)
        if not Attachments or len(Attachments) == 0:
            return

        Channel: typing.Optional[int] = None

        if not Channel or message.channel.id != Channel:
            return

        User = message.author
        Guild = message.guild
        await message.add_reaction(self.bot.emoji.like)
        self.MsgLikes[message.id] = {"message": message, "likes": 0}

    @commands.Cog.listener(name="on_reaction_add")
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        message = reaction.message
        if user.bot:
            return
        if message.id not in self.MsgLikes:
            return
        if reaction.emoji != self.bot.emoji.like:
            return

        member = message.guild.get_member(user.id)
        self.MsgLikes[message.id]["likes"] = self.MsgLikes[message.id]["likes"] + 1
        if True:
            ...
        self.bot.loop.create_task(AddLikes(bot=self.bot, user=member))


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        listeners(bot))
