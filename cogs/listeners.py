import asyncio
import io
import os
import random
import secrets
import typing
import logging
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
from handler.database import (
    Get_channel_settings,
    Get_Guild_settings
)


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
    AllowedTypes = ("image", "video")
    attachments = message.attachments
    embeds = message.embeds
    if (not attachments or len(attachments) == 0) \
            and (not embeds or len(embeds) == 0):
        return
    Resolved_Attachments = []
    for image in attachments:
        print(image.content_type)
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
        self.cachedLists = {}

    @commands.Cog.listener(name="on_message")
    async def AutoThreadCreate(self, message: discord.Message):
        guild = message.guild
        user = message.author
        channel = message.channel
        attachments = await GetAttachments(message=message)
        if user.bot:
            return
        if message.type != discord.MessageType.default:
            return
        if channel.type != discord.ChannelType.text:
            return
        if attachments is None or len(attachments) == 0:
            return

        guild_settings = await Get_Guild_settings(bot=self.bot, guild=guild)
        isThreadListenerEnabled = guild_settings["thread_lstnr"]
        if not isThreadListenerEnabled:
            return
        settings = await Get_channel_settings(bot=self.bot, Channel=channel)
        if not settings:
            return
        isThreadChannel = settings["is_threadchannel"]
        if not isThreadChannel:
            return
        MemeManagerRole_id = guild_settings["memeadmin"]
        MemeManagerRole = guild.get_role(MemeManagerRole_id)
        threadName = f"{user.name}({secrets.token_hex(5)})"
        threadMsg = settings['thread_msg'] if settings["thread_msg"] else \
            f"{MemeManagerRole.mention if MemeManagerRole else user.mention}" \
            f" make sure that the meme is original"

        thread = await channel.create_thread(
            name=threadName, message=message, auto_archive_duration=1440)
        view = thread_channel(user=user)
        thread_message = await thread.send(content=threadMsg, view=view)
        view.message = thread_message
        return

async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        listeners(bot))
