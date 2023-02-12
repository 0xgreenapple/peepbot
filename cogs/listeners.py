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
from typing import TYPE_CHECKING, Optional
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


def GetAttachments(message: discord.Message, links: bool = False):
    AllowedTypes = ("image", "video")
    attachments = message.attachments
    embeds = message.embeds
    if (not attachments or len(attachments) == 0) \
            and (not embeds or len(embeds) == 0):
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


async def removeLikes():
    ...


async def HandleThreadEvents():
    ...


class listeners(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot
        self.MsgLikes = {}
        self.Database = self.bot.Database
        self.cachedLists = {}

    def cacheMemeMessage(
            self, message: discord.Message, duration: timedelta,
            maxLikes: int, next_Channel: int, author_id: int):

        """ store memes related messages """
        guild_cache = self.bot.cache.get_guild(message.guild.id)
        if guild_cache is None:
            self.bot.cache.set_guild(message.guild.id)
            guild_cache = self.bot.cache.get_guild(message.guild.id)

        guild_cache["memes"] = {}
        message_obj = {
            "message": message,
            "WatchUntil": duration,
            "author_id": author_id,
            "nextLvl": next_Channel,
            "maxLikes": maxLikes
        }
        guild_cache["memes"][message.id] = message_obj

    def get_cached_message(self, guild_id, message_id):
        """ return message from bot cache """
        guild_cache = self.bot.cache.get(guild_id)
        if guild_cache is None:
            return None
        memes = guild_cache.get("memes")
        if memes is None:
            return None
        return memes.get(message_id)

    async def add_likes(self, member_id, guild_id, like: int = 1):
        await self.bot.Database.Insert(
            member_id,
            guild_id,
            like,
            table="peep.user_details",
            columns="guild_id,user_id,likes",
            values="$1,$2,$3",
            on_Conflicts="(user_id,guild_id) "
                         "DO UPDATE SET "
                         "likes = COALESCE(user_details.likes, 0) + $3")

    async def move_message_to(
            self, channel: discord.TextChannel, message_obj: dict = None):

        Message: discord.Message = message_obj["message"]
        Attachment: discord.Attachment = GetAttachments(Message)[0]
        AttachmentFile = await Attachment.to_file(
            filename=Attachment.filename, use_cached=True)
        Author = Message.guild.get_member(message_obj["author_id"])

        message = await channel.send(
            content=f"by {Author.mention}",
            file=AttachmentFile
        )

        # delete old message object from the cache and append new one
        self.bot.cache[Message.guild.id]["memes"].pop(Message.id)
        channel_settings = await Get_channel_settings(
            bot=self.bot, Channel=channel)
        MaxLikeLimit = channel_settings["NextLvl"]
        NextGallery = channel_settings["NextLvl"]
        self.cacheMemeMessage(
            message=message,
            author_id=Author.id, duration=message_obj["WatchUntil"],
            maxLikes=MaxLikeLimit, next_Channel=NextGallery)

    @commands.Cog.listener(name="on_message")
    async def AutoThreadCreate(self, message: discord.Message):
        """
        Called when a message is received,
        Create threads on messages that contains attachments,
        Only if Auto thread in the server settings is turned on.
        """
        guild = message.guild
        user = message.author
        channel = message.channel

        attachments = GetAttachments(message=message)
        if user.bot:
            return
        if message.type != discord.MessageType.default:
            return
        if channel.type != discord.ChannelType.text:
            return
        if attachments is None or len(attachments) == 0:
            return

        # get Guild settings and channel settings from the cache if available
        # else database if guild settings or channel settings is None it will return
        guild_settings, settings = await asyncio.gather(
            Get_Guild_settings(bot=self.bot, guild_id=guild.id),
            Get_channel_settings(bot=self.bot, Channel=channel)
        )
        if not guild_settings or not settings:
            return
        isThreadListenerEnabled = guild_settings["thread_lstnr"]
        if not isThreadListenerEnabled:
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
        # create thread on message and send A message to thread
        thread = await channel.create_thread(
            name=threadName, message=message, auto_archive_duration=1440)
        view = thread_channel(user=user)
        thread_message = await thread.send(content=threadMsg, view=view)
        view.message = thread_message
        return

    @commands.Cog.listener(name="on_raw_reaction_add")
    async def WatchForReactions(self, reaction: discord.RawReactionActionEvent):
        # get message channel and guild
        Channel = self.bot.get_channel(reaction.channel_id)
        Message = await Channel.fetch_message(reaction.message_id)
        Guild = Channel.guild
        Reactions = Message.reactions
        Attachments = GetAttachments(message=Message)
        if reaction.member.bot:
            return
        if reaction.emoji.id != 1008402662070427668:
            return
        if not Attachments or len(Attachments) == 0:
            return
        # check if Meme Listener in server is allowed
        Guild_settings = await Get_Guild_settings(self.bot, Guild.id)
        if Guild_settings is None:
            return
        isEnabled = Guild_settings.get("reaction_lstnr")
        if not isEnabled:
            return
        # check if channel is a Meme channel
        channel_settings = await Get_channel_settings(self.bot, Channel)
        if not channel_settings:
            return
        isChannelAMemeChannel = channel_settings.get("is_memechannel")
        if not isChannelAMemeChannel:
            return

        # add and get message from the cache
        message_cache = self.get_cached_message(
            guild_id=Guild.id, message_id=Message.id)
        message_watch_duration = message_cache["WatchUntil"]
        LikeLimit = message_cache["maxLikes"]
        message_author = message_cache["author_id"]

        if message_watch_duration is not None:
            WatchMessageUntil = Message.created_at.utcnow() + message_cache["WatchUntil"]
            Now = datetime.utcnow()
            if WatchMessageUntil <= Now:
                guild_cache = self.bot.cache.get_guild(guild_id=Guild.id)
                guild_cache["memes"].pop(Message.id)
                return
        likes = 0
        for reaction in Reactions:
            if reaction.emoji.id == 1008402662070427668:
                likes = reaction.count
                break
        if likes >= LikeLimit:
            # TODO: move the message to next level
            await self.move_message_to(channel=Channel, message_obj=message_cache)

        await self.add_likes(
            member_id=message_author, guild_id=Guild.id)

    @commands.Cog.listener(name="on_message")
    async def WatchForMemes(self, message: discord.Message):
        """
        Called when a message is received,
        And react to message
        """
        guild = message.guild
        user = message.author
        channel = message.channel

        attachments = GetAttachments(message=message)
        if user.bot and user.id != self.bot.user.id:
            return
        if message.type != discord.MessageType.default:
            return
        if channel.type != discord.ChannelType.text:
            return
        if attachments is None or len(attachments) == 0:
            return

        guild_settings, settings = await asyncio.gather(
            Get_Guild_settings(bot=self.bot, guild_id=guild.id),
            Get_channel_settings(bot=self.bot, Channel=channel)
        )
        if not guild_settings or not settings:
            return
        IsMemesAllowed = guild_settings.get("reaction_lstnr")
        if not IsMemesAllowed:
            return
        IsChannelAMemeChannel = settings.get("is_memechannel")
        if not IsChannelAMemeChannel:
            return

        watchUntil = guild_settings.get("vote_time")
        nextChannel = settings.get("NextLvl")
        maxLikes = settings.get("max_like")
        if watchUntil:
            watchUntil = watchUntil
        if message.author.id != self.bot.user.id:
            self.cacheMemeMessage(
                message=message, duration=watchUntil, maxLikes=maxLikes,
                next_Channel=nextChannel, author_id=message.author.id)
        like = message.add_reaction(self.bot.emoji.like)
        dislike = message.add_reaction(self.bot.emoji.dislike)
        self.bot.loop.create_task(like)
        self.bot.loop.create_task(dislike)
        return


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        listeners(bot))
