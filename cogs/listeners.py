"""
:Author: 0xgreenapple(xgreenapple)
:Licence: MIT
:Copyright: 2022-present 0xgreenapple
"""

import asyncio
import secrets
import typing
from datetime import datetime, tzinfo
from typing import Union

import discord
from discord.ext import commands

from handler.Context import Context
from handler.database import (
    get_channel_settings,
    get_guild_settings
)
from handler.utils import records_to_dict, get_attachments
from handler.view import thread_channel
from pepebot import PepeBot


class Listeners(commands.Cog):
    def __init__(self, bot: PepeBot) -> None:
        self.bot = bot
        self.Database = self.bot.database

    @staticmethod
    def is_valid_emoji(
            emoji: discord.PartialEmoji,
            compair_to: Union[discord.PartialEmoji, str]
    ) -> bool:
        if compair_to is not None and compair_to != '0':
            partial_emoji = discord.PartialEmoji.from_str(compair_to)
            if partial_emoji != emoji:
                return True
        return True

    @staticmethod
    def get_author_from_message(message: discord.Message):
        if not message.author.bot:
            return message.author
        message_content = message.content
        if message_content is None:
            return
        if message_content.lower().startswith("by"):
            mentions = message.mentions
            if mentions is None or len(mentions) != 1:
                return
            return mentions[0]
        return

    def cache_meme_message(
            self, message: discord.Message, maxLikes: int,
            next_Channel: int, author_id: int,
            gallery_message: typing.Optional[discord.Message] = None):

        """ store memes related messages """
        guild_cache = self.bot.cache.get_guild(message.guild.id)
        gallery_msg = None
        if gallery_msg is not None:
            gallery_msg = gallery_message
        guild_cache["memes"] = {}
        message_obj = {
            "message": message,
            "author_id": author_id,
            "gallery_message": gallery_msg,
        }
        guild_cache["memes"][message.id] = message_obj

    def get_cached_message(self, guild_id, message_id):
        """ return message from bot cache """
        memes = self.bot.cache.get_from_guild(guild_id, "memes")
        if memes is None:
            return None
        return memes.get(message_id)

    def set_meme_is_completed(self, message: discord.Message):
        to_insert = self.bot.database.insert(
            message.guild.id,
            message.channel.id,
            message.id,
            table="peep.meme_completed_messages",
            columns="guild_id,channel_id,message_id",
            values="$1,$2,$3",
            on_conflicts=f"(message_id) DO NOTHING"
        )
        self.bot.cache.append_completed_message(
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            message_id=message.id
        )
        self.bot.loop.create_task(to_insert)

    async def is_completed_meme(self, message: discord.Message):
        """ check from the database the meme"""
        channel = message.channel
        guild = channel.guild
        meme_messages = self.bot.cache.get_completed_messages(
            channel_id=channel.id, guild_id=guild.id
        )
        if meme_messages is None:
            channel_cache = self.bot.cache.get_channel(
                channel_id=channel.id, guild_id=guild.id)
            meme_messages = channel_cache["meme_completed_messages"] = (
                records_to_dict(await self.bot.database.select(
                    guild.id, channel.id,
                    table_name="peep.meme_completed_messages",
                    columns="message_id",
                    conditions="guild_id = $1 AND channel_id = $2",
                    return_all_rows=True,
                ), remove_single="message_id"))
        return meme_messages.count(message.id) != 0

    async def check_for_rewards(self, limit: int, member: discord.Member):
        guild = member.guild
        rewards = self.bot.cache.get_from_guild(
            guild_id=guild.id, key="rewards")
        reward_role = None
        if rewards is not None:
            reward_role = rewards.get(limit)
        if reward_role is None:
            reward_role = await self.Database.select(
                guild.id,
                limit,
                table_name="peep.rolerewards",
                columns="role_id",
                conditions="guild_id=$1 AND likes=$2",
            )
            self.bot.cache[guild.id]["rewards"] = {}
            self.bot.cache[guild.id]["rewards"][limit] = reward_role
        if reward_role is None:
            return
        role = guild.get_role(reward_role)
        if role is None or not role.is_assignable():
            return
        member_roles = member.roles
        if role not in member_roles:
            member_roles.append(role)
            await member.edit(roles=member_roles)

    async def add_likes(self, member_id, guild_id, like: int = 1):
        await self.bot.database.insert(
            member_id,
            guild_id,
            like,
            table="peep.user_details",
            columns="guild_id,user_id,likes",
            values="$1,$2,$3",
            on_conflicts="(user_id,guild_id) "
                         "DO UPDATE SET "
                         "likes = COALESCE(user_details.likes, 0) + $3")

    async def remove_likes(self, user: discord.Member):
        await self.bot.database.insert(
            user.id,
            user.guild.id,
            0,
            table="peep.user_details",
            columns="guild_id,user_id,likes",
            values="$1,$2,$3",
            on_conflicts="""
            (user_id,guild_id) DO UPDATE SET likes =
             CASE
                WHEN user_details.likes <= 0 THEN 0
                ELSE user_details.likes - 1
            END;""")

    async def move_message_to(
            self, channel: discord.TextChannel, message_obj: dict = None):

        cached_message: discord.Message = message_obj["message"]
        attachment: discord.Attachment = get_attachments(cached_message)[0]
        attachment_file = await attachment.to_file(
            filename=attachment.filename, use_cached=True)
        author = cached_message.guild.get_member(message_obj["author_id"])

        message = await channel.send(
            content=f"by {author.mention}",
            file=attachment_file
        )

        # delete old message object from the cache and append new one
        self.bot.cache.get_guild(message.guild.id)["memes"].pop(
            cached_message.id)
        self.set_meme_is_completed(message=cached_message)
        channel_settings = await get_channel_settings(
            bot=self.bot, channel=channel)
        if channel_settings is None:
            return
        max_like_limit = channel_settings["max_like"]
        next_gallery = channel_settings["nextlvl"]
        self.cache_meme_message(
            message=message, author_id=author.id, maxLikes=max_like_limit,
            next_Channel=next_gallery)

    @commands.Cog.listener(name="on_message")
    async def auto_thread_create(self, message: discord.Message):
        """
        Called when a message is received,
        Create threads on messages that contains attachments,
        Only if Auto thread in the server settings is turned on.
        """
        guild = message.guild
        user = message.author
        channel = message.channel

        attachments = get_attachments(message=message)
        if user.bot:
            return
        if message.type != discord.MessageType.default:
            return
        if channel.type != discord.ChannelType.text:
            return
        if attachments is None or len(attachments) == 0:
            return

        guild_settings, settings = await asyncio.gather(
            get_guild_settings(bot=self.bot, guild_id=guild.id),
            get_channel_settings(bot=self.bot, channel=channel)
        )
        if not guild_settings or not settings:
            return
        is_thread_listener_enabled = guild_settings["thread_lstnr"]
        if not is_thread_listener_enabled:
            return
        is_thread_channel = settings["is_threadchannel"]
        if not is_thread_channel:
            return

        meme_manager_role_id = guild_settings["memeadmin"]
        meme_manager_role = guild.get_role(meme_manager_role_id)
        role_to_mention = meme_manager_role
        if meme_manager_role is None:
            role_to_mention = user.mention
        thread_name = f"{user.name}({secrets.token_hex(5)})"
        thread_msg = settings['thread_msg']
        if thread_msg is None:
            thread_msg = (
                f"{role_to_mention}"
                f" make sure that the meme is original")
        # create thread on message and send A message to thread
        thread = await channel.create_thread(
            name=thread_name, message=message, auto_archive_duration=1440)
        view = thread_channel(user=user)
        thread_message = await thread.send(content=thread_msg, view=view)
        view.message = thread_message
        return

    @commands.Cog.listener(name="on_raw_reaction_add")
    @commands.Cog.listener(name="on_raw_reaction_remove")
    async def watch_for_reactions(
            self, reaction: discord.RawReactionActionEvent
    ):

        """ watch for reactions on the message containing
         attachments in meme channels and store likes"""

        is_event_type_removed = reaction.event_type == "REACTION_REMOVE"
        channel = self.bot.get_channel(reaction.channel_id)
        message = await channel.fetch_message(reaction.message_id)
        guild = channel.guild
        reactions = message.reactions
        attachments = get_attachments(message=message)

        if not is_event_type_removed and reaction.member.bot:
            return
        if not attachments or len(attachments) == 0:
            return

        guild_settings = await get_guild_settings(self.bot, guild.id)
        if guild_settings is None:
            return
        channel_settings = await get_channel_settings(self.bot, channel)
        like_limit = channel_settings["max_like"]
        next_channel = channel_settings["nextlvl"]

        if channel_settings is None:
            return

        like_emoji = channel_settings.get("like_emoji")
        is_right_emoji = self.is_valid_emoji(
            emoji=reaction.emoji, compair_to=like_emoji)
        if not is_right_emoji:
            return
        # check if Meme Listener in server is allowed
        is_meme_listener_enabled = guild_settings.get("reaction_lstnr")
        if not is_meme_listener_enabled:
            return
        # check if channel is a Meme channel
        is_channel_a_meme_channel = channel_settings.get("is_memechannel")
        if not is_channel_a_meme_channel:
            return
        if await self.is_completed_meme(message):
            print("already completed")
            return
        message_watch_duration = channel_settings["voting_time"]
        message_cache = self.get_cached_message(
            guild_id=guild.id, message_id=message.id)
        if message_watch_duration is not None:
            watch_message_until = (
                    message.created_at
                    + message_watch_duration)
            now = datetime.now(message.created_at.tzinfo)
            if watch_message_until <= now:
                if message_cache is not None:
                    guild_cache = self.bot.cache.get_guild(guild_id=guild.id)
                    guild_cache["memes"].pop(message.id)
                return
        likes = 0
        for reaction in reactions:
            if self.is_valid_emoji(
                    emoji=reaction.emoji, compair_to=like_emoji):
                likes = reaction.count
                break

        if (likes + 1 if is_event_type_removed else likes - 1) >= like_limit:
            print("here")
            return

        if message_cache is None:
            author = self.get_author_from_message(message)
            if author is None:
                return
            self.cache_meme_message(
                author_id=author.id,
                message=message,
                maxLikes=like_limit,
                next_Channel=next_channel
            )
            message_cache = self.get_cached_message(
                guild_id=guild.id, message_id=message.id)

        message_author = message_cache["author_id"]
        if (likes >= like_limit and next_channel is not None and
                not is_event_type_removed):
            await self.move_message_to(
                channel=self.bot.get_channel(next_channel),
                message_obj=message_cache
            )
        member = guild.get_member(message_author)
        if not is_event_type_removed:
            self.bot.loop.create_task(self.add_likes(
                member_id=message_author, guild_id=guild.id),
                name=f"store likes")
            self.bot.loop.create_task(self.check_for_rewards(
                limit=likes, member=member), name="role rewards")
        else:
            self.bot.loop.create_task(self.remove_likes(user=member))

    @commands.Cog.listener(name="one")
    @commands.Cog.listener(name="on_message")
    async def watch_for_memes(self, message: discord.Message):
        """
        Called when a message is received,
        And react to message
        """
        guild = message.guild
        user = message.author
        channel = message.channel
        attachments = get_attachments(message=message)

        if user.bot and user.id != self.bot.user.id:
            return
        if message.type != discord.MessageType.default:
            return
        if channel.type != discord.ChannelType.text:
            return
        if attachments is None or len(attachments) == 0:
            return

        guild_settings, settings = await asyncio.gather(
            get_guild_settings(bot=self.bot, guild_id=guild.id),
            get_channel_settings(bot=self.bot, channel=channel)
        )

        if not guild_settings or not settings:
            return
        is_memes_allowed = guild_settings.get("reaction_lstnr")
        if not is_memes_allowed:
            return
        is_channel_a_meme_channel = settings.get("is_memechannel")
        if not is_channel_a_meme_channel:
            return

        next_channel = settings.get("nextlvl")
        max_likes = settings.get("max_like")
        if message.author.id != self.bot.user.id:
            self.cache_meme_message(
                message=message, maxLikes=max_likes,
                next_Channel=next_channel, author_id=message.author.id)

        like_emoji = settings.get("like_emoji")
        if like_emoji is None:
            like_emoji = self.bot.emoji.like
        dislike_emoji = settings.get("dislike_emoji")
        if dislike_emoji is None:
            dislike_emoji = self.bot.emoji.dislike

        if like_emoji != '0':
            like_message = message.add_reaction(like_emoji)
            self.bot.loop.create_task(like_message)

        if dislike_emoji != '0':
            dislike_message = message.add_reaction(dislike_emoji)
            self.bot.loop.create_task(dislike_message)


async def setup(bot: PepeBot) -> None:
    await bot.add_cog(Listeners(bot))
