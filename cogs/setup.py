"""
:Author: @0xgreenapple(xgreenapple)
:Licence: MIT
:Copyright: 2022-present @0xgreenapple
"""
import logging
import re
import unicodedata

import discord
from discord import app_commands, Interaction
from discord.app_commands import Range
from discord.ext import commands

from pepebot import PepeBot

from datetime import timedelta

import typing
from typing import Optional, Union, Literal

from handler.utils import (
    string_to_delta,
    get_place_holders,
    get_key_pair,
    to_string_list, get_relative_time, records_to_dict)
from handler.database import (
    reinitialise_channel_settings,
    reinitialise_guild_settings,
    get_channel_settings,
    get_guild_settings)

_log = logging.getLogger("pepebot")


async def setup(bot: PepeBot) -> None:
    await bot.add_cog(Configuration(bot))


class Configuration(commands.Cog):
    def __init__(self, bot: PepeBot) -> None:
        self.bot = bot
        self.Database = bot.database

    async def set_channel_settings(self, guild_id, channel_id, **options):
        """
        Edit channel settings that is stored in the database
        """
        options_names = list(options.keys())
        options_names.insert(0, "guild_id")
        options_names.insert(1, "channel_id")
        names_str_list = to_string_list(options_names)
        placeholders_str = get_place_holders(len(options_names))
        options_names.remove("guild_id")
        options_names.remove("channel_id")
        key_value_str = get_key_pair(options_names, 3)
        values = list(options.values())
        values.insert(0, guild_id)
        values.insert(1, channel_id)

        await self.Database.insert(
            *values,
            table="peep.channel_settings",
            columns=names_str_list,
            values=placeholders_str,
            on_conflicts=
            "(guild_id,channel_id) DO UPDATE SET "
            f"{key_value_str}")
        # insert new settings to the guild cache,
        cache_new_settings = reinitialise_channel_settings(
            bot=self.bot, channel_id=channel_id, guild_id=guild_id)
        self.bot.loop.create_task(cache_new_settings)

    async def set_guild_settings(self, guild_id, **options):
        """ change guild settings from the database"""
        options_names = list(options.keys())
        options_names.insert(0, "guild_id")
        names_str_list = to_string_list(options_names)
        placeholders = get_place_holders(len(options_names))
        values = list(options.values())
        values.insert(0, guild_id)
        options_names.remove("guild_id")
        key_value_str = get_key_pair(options_names, 2)
        await self.bot.database.insert(
            *values,
            table="peep.guild_settings",
            columns=f"{names_str_list}",
            values=placeholders,
            on_conflicts=
            "(guild_id) DO UPDATE SET "
            f"{key_value_str}")
        cache_new_settings = reinitialise_guild_settings(
            bot=self.bot, guild_id=guild_id)
        self.bot.loop.create_task(cache_new_settings)

    def get_valid_emoji_string(self, string: str) -> Optional[str]:
        custom = string.replace(" ", "")
        firstEmoji = custom[0]
        # it is a default emoji
        if self.bot.emoji.is_default_emoji(custom):
            emoji = firstEmoji
        else:
            # check if given emoji emoji is custom emoji and is usable
            emoji_id = self.bot.emoji.get_emoji_id(custom)
            custom_emoji = None
            if emoji_id:
                custom_emoji = self.bot.get_emoji(int(emoji_id))
            if custom_emoji is None or not custom_emoji.is_usable():
                return None
            emoji = custom_emoji
        return emoji

    setup = app_commands.Group(
        name='setup',
        description='some configuration commands related to memes',
        guild_only=True,
        default_permissions=discord.Permissions(administrator=True)
    )

    @setup.command(name="guild_settings")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def edit_guild_settings(
            self, interaction: discord.Interaction,
            option: Literal["Auto Thread", "Meme listener",
                            "Oc Listener", 'economy'],
            turn: Literal['on', 'off']
    ):

        """
         configuration commands related to server.

        Parameters
        ----------
        option: :class:`typing.Literal`
            choose a setting that you want to change
        turn: typing.Literal
            turn on or turn off setting
        """

        # change the str value to boolean value
        turned = True if turn == 'on' else False
        settings_map = {
            "Auto Thread": "thread_lstnr",
            "Meme listener": "reaction_lstnr",
            "Oc Listener": "oc_lstnr",
            "economy": "economy"
        }
        setting = settings_map[option]
        await self.set_guild_settings(
            guild_id=interaction.guild.id, **{setting: turned})

        embed = discord.Embed()
        embed.title = "``config update``"
        embed.description = (f">>> {self.bot.emoji.right} {option}"
                             f" has been turned ``{turn}``")
        await interaction.response.send_message(
            embed=embed, ephemeral=True)

    @setup.command(name="channel_settings")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def edit_channel_settings(
            self, interaction: Interaction, channel: discord.TextChannel,
            option: typing.Literal["Auto thread", "Meme listener",
                                   "Oc listener"],
            turn: typing.Literal["on", "off"]
    ):

        """
        change channel related settings.

        Parameters
        ----------
        channel:
            channel that you want change settings
        option:
            what settings you want to change
        turn:
            turn on or off setting
        """
        embed = discord.Embed(title="``updated Config``")
        permission = channel.permissions_for(interaction.guild.me)

        bot_required_permissions = [
            permission.manage_messages, permission.view_channel,
            permission.read_messages, permission.add_reactions]
        permission_string = [
            "manage_messages", "view_channel",
            "read_messages", "add_reactions"]
        if not all(bot_required_permissions):
            embed.title = f"**invalid permissions**"
            embed.description = (
                f">>> {self.bot.right} bot missing following "
                f"permissions in {channel.mention} channel"
                f":{channel.mention} \n"
                f" \n".join(permission_string)
            )
            await interaction.response.send_message(
                embed=embed, ephemeral=True)
            return
        turned = True if turn == "on" else False
        settings_map = {
            "Auto thread": "is_threadChannel",
            "Meme listener": "is_memeChannel",
            "Oc listener": "is_ocChannel"
        }
        setting = settings_map[option]
        await self.set_channel_settings(
            channel_id=channel.id, guild_id=channel.guild.id,
            **{setting: turned})
        embed.title = "**updated config**"
        embed.description = (
            f">>> {option} for {channel.mention} has been turned {turn}")
        await interaction.response.send_message(
            embed=embed, ephemeral=True)

    @setup.command(name="edit_meme_channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_meme_channel_settings(
            self, interaction: Interaction,
            meme_channel: discord.TextChannel, duration: Optional[str] = None,
            max_likes: Optional[int] = None,
            next_gallery_channel: Optional[discord.TextChannel] = None
    ):

        """
        configure meme channel related settings.

        Parameters
        ----------
        meme_channel:
            the meme channel that you want to configure
        duration:
            example:1d,1s,1w etc. and 0 for no time limit.
        max_likes:
            maximum likes needed to go to next gallery
        next_gallery_channel:
            the channel where memes will be moved
            when reaching max likes
        """
        response = interaction.response
        embed = discord.Embed(title=f"``command failed``")
        # get configurations realted to the channel
        channel_settings = await get_channel_settings(
            bot=self.bot, channel=meme_channel)
        # send a error message if given channel is not a meme channel
        if channel_settings is None or not channel_settings["is_memechannel"]:
            embed.description = (
                f">>> {self.bot.right} {meme_channel.mention} channel"
                f" is not a meme channel, pls run command ``/config "
                f"{meme_channel.name}`` to check if the channel is a "
                f"meme channel or ``/serverconfig`` to see list of "
                f"meme channels in the gild "
            )
            await response.send_message(embed=embed, ephemeral=True)
            return
        delta_time = 'NULL' if duration == '0' else duration
        if delta_time is not None and duration != '0':
            try:
                delta_time = string_to_delta(duration)
            except Exception as error:
                embed.description = (
                    f">>> {self.bot.right} the time ``{duration}`` is "
                    f"invalid it must be in formate of"
                    f"```1(h|hr|hour|hours) \n 1(m|min|minute) \n"
                    f" 1(s|second|secs)``` "
                )
                await response.send_message(embed=embed, ephemeral=True)
                _log.error(error)
                return
        args = {}
        if max_likes is not None:
            if max_likes <= 1:
                embed.description = (
                    f">>> {self.bot.right} max likes must be greater than 1")
                await response.send_message(embed=embed, ephemeral=True)
                return
            elif max_likes > 1:
                args["max_like"] = max_likes
        if (next_gallery_channel is not None and
                next_gallery_channel.id == interaction.channel_id):
            embed.description = "the channel is not valid choose another " \
                                "channel "
            await response.send_message(embed=embed)
        if delta_time is not None:
            args["voting_time"] = delta_time if delta_time != 'NULL' else None

        if next_gallery_channel is not None:
            args["Nextlvl"] = next_gallery_channel.id

        await self.set_channel_settings(
            interaction.guild_id, interaction.channel_id, **args)

        embed.title = f"``updated config``"
        is_delta_time = isinstance(delta_time, timedelta)
        is_next_gallery_channel = "none"
        if next_gallery_channel is not None:
            is_next_gallery_channel = next_gallery_channel.mention
        human_relative_time = "none"
        if is_delta_time:
            human_relative_time = get_relative_time(delta_time)
        embed.description = f"""
        >>> {self.bot.right} **channel**:{meme_channel.mention}
        **maximum likes**: {max_likes}
        **gallery**: {is_next_gallery_channel}
        **time limit**: {human_relative_time}
        """
        await response.send_message(embed=embed)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    @setup.command(name="meme_admin_role")
    async def add_meme_admin_role(
            self, interaction: Interaction, role: discord.Role,
            remove: Literal['true']
    ):
        """
        add A role to manage economy related commands.

        Parameters
        ----------
        role:
            role that you wanted to manage commands
        """
        response = interaction.response
        embed = discord.Embed()
        if interaction.guild.owner_id != interaction.user.id:
            embed.title = "``command failed!``"
            embed.description = "only owner can execute this command"
            await interaction.response.send_message(
                embed=embed, ephemeral=True)
            return
        role_id = None if remove == 'true' else role.id
        await self.set_guild_settings(
            guild_id=interaction.guild.id, MemeAdmin=role_id)
        embed.title = f"``role {'added' if role_id else 'removed'}``"
        embed.description = (
            f">>> {self.bot.right} now members with "
            f"{role.mention} will be able to execute "
            f"all meme and economy commands")
        if role_id is None:
            embed.description = (
                f">>> {self.bot.right} meme admin role has been removed, "
                f"economy and meme commands are now owner only")
        await response.send_message(embed=embed, ephemeral=True)

    @app_commands.checks.has_permissions(administrator=True)
    @setup.command(name="like")
    async def setup_like_emoji(
            self, interaction: Interaction, meme_channel: discord.TextChannel,
            custom_emoji: str = None, setdefault: Literal['true'] = None,
            remove: Literal['true'] = None
    ):
        """
        settings related bot reactions

        Parameters
        ----------
        custom_emoji:
            specify the emoji you want the bot to react with
        setdefault:
            change the reaction emoji to default one that bot use
        remove:
            stop the bot to react like emoji on memes
        """
        response = interaction.response
        embed = discord.Embed(title="``command failed``")
        emoji = ""
        channel_settings = await get_channel_settings(
            bot=self.bot, channel=meme_channel)

        if (channel_settings is None or
                not channel_settings["is_memechannel"]):
            embed.description = (
                f">>> {self.bot.right} channel {meme_channel.mention} is "
                f"not a meme channel please run commands ``/channelconfig`` to "
                f"see list of meme channels")
            await response.send_message(embed=embed, ephemeral=True)
            return

        if not any([custom_emoji, setdefault, remove]):
            embed.description = (
                f">>> {self.bot.emoji.right}"
                f" you must specify at least one setting")
            await response.send_message(embed=embed, ephemeral=True)
            return

        if custom_emoji is not None:
            emoji = self.get_valid_emoji_string(string=custom_emoji)
            if emoji is None:
                embed.description = (
                    f">>> {self.bot.emoji.right}"
                    f"given emoji is not a valid emoji :``{custom_emoji}``")
                await response.send_message(embed=embed, ephemeral=True)
                return
        elif setdefault is not None:
            emoji = self.bot.emoji.like
            custom_emoji = emoji
        elif remove is not None:
            emoji = '0'
        await self.set_channel_settings(
            guild_id=interaction.guild_id, channel_id=meme_channel.id,
            like_emoji=str(emoji))
        embed.title = "``updated config``"
        embed.description = f"now bot will react to {custom_emoji}"
        if emoji == '0':
            embed.description = f"now bot will not able to like messages"
        await response.send_message(embed=embed, ephemeral=True)

    @app_commands.checks.has_permissions(administrator=True)
    @setup.command(name="dislike")
    async def setup_dislike_emoji(
            self, interaction: Interaction, meme_channel: discord.TextChannel,
            custom_emoji: str = None, setdefault: Literal['true'] = None,
            remove: Literal['true'] = None
    ):
        """
        settings related bot reactions

        Parameters
        ----------
        custom_emoji:
            specify the emoji you want the bot to react with
        setdefault:
            change the reaction emoji to default one that bot use
        remove:
            stop the bot to react like emoji on memes
        """

        response = interaction.response
        embed = discord.Embed(title="``command failed``")
        emoji = ""
        channel_settings = await get_channel_settings(
            bot=self.bot, channel=meme_channel)

        if (channel_settings is None or
                not channel_settings["is_memechannel"]):
            embed.description = (
                f">>> {self.bot.right} channel {meme_channel.mention} is "
                f"not a meme channel please run commands ``/channelconfig`` to "
                f"see list of meme channels")
            await response.send_message(embed=embed, ephemeral=True)
            return

        if not any([custom_emoji, setdefault, remove]):
            embed.description = (
                f">>> {self.bot.emoji.right}"
                f" you must specify at least one setting")
            await response.send_message(embed=embed, ephemeral=True)
            return

        if custom_emoji is not None:
            emoji = self.get_valid_emoji_string(string=custom_emoji)
            if emoji is None:
                embed.description = (
                    f">>> {self.bot.emoji.right}"
                    f"given emoji is not a valid emoji :``{custom_emoji}``")
                await response.send_message(embed=embed, ephemeral=True)
                return
        elif setdefault is not None:
            emoji = self.bot.emoji.like
            custom_emoji = emoji
        elif remove is not None:
            emoji = '0'
        await self.set_channel_settings(
            guild_id=interaction.guild_id, channel_id=meme_channel.id,
            like_emoji=str(emoji))
        embed.title = "``updated config``"
        embed.description = f"now bot will react to {custom_emoji}"
        if emoji == '0':
            embed.description = f"now bot will not able to dislike messages"

        await response.send_message(embed=embed, ephemeral=True)

    @app_commands.checks.has_permissions(administrator=True)
    @setup.command(name="reward_role")
    async def setup_reward_role(
            self, interaction: discord.Interaction, at_likes: Range[int, 1],
            give_role: discord.Role
    ):
        """
        setup reward role for specific likes

        Parameters
        ----------
        at_likes
            at what like levels will user be given the role
        give_role
            the role that will be given to user
        """
        embed = discord.Embed(title="``command failed``")
        if not give_role.is_assignable():
            embed.description = (
                f">>> {self.bot.emoji.right} the bot can't" 
                f"assign this role, whether the role is above " 
                f"bot role or bot lack permissions to assign it")
            await interaction.response.send_message(embed=embed)
            return

        insert_role = self.bot.database.insert(
            interaction.guild_id,
            at_likes,
            give_role.id,
            table="peep.rolerewards",
            columns="guild_id,likes,role_id",
            values="$1,$2,$3",
            on_conflicts="(guild_id,likes) DO UPDATE SET "
                         "role_id = $3")
        embed.title = "``role added!``"
        embed.description = (
            f"{give_role.mention} will be assigned to user after "
            f"reaching ``{at_likes}`` {self.bot.emoji.like}"
        )
        await interaction.response.send_message(embed=embed)
        self.bot.loop.create_task(insert_role)

    @setup.command(name="logging")
    @app_commands.checks.has_permissions(administrator=True)
    async def configure_logging(
            self, interaction: discord.Interaction,
            shop_log: discord.TextChannel,
            remove: Literal['true'] = None,
            dm_member_on_accept: Literal['true', 'false'] = 'false',
    ):
        """
        setup logging for the purchased items by the user.

        Parameters
        ----------
        shop_log:
            the channel that you want the bot to send messages in
        dm_member_on_accept:
            whether dm user after accepting the item or not
        """

        bot_reactions = shop_log.permissions_for(shop_log.guild.me)
        required_permission = [
            bot_reactions.send_messages,
            bot_reactions.view_channel,
            bot_reactions.read_message_history,
        ]
        embed = discord.Embed(title="``command failed``")
        if not any(required_permission):
            embed.description = (
                f"the bot missing permission in channel "
                f"{shop_log.mention} check if bot has following permissions "
                f"in the channel\n"
                f"[read messages, send messages,read message history]")
            await interaction.response.send_message(embed=embed)
            return
        shop_log_channel = shop_log.id
        guild_settings = await get_guild_settings(
            bot=self.bot, guild_id=interaction.guild_id)
        if remove == 'true':
            if guild_settings["shoplog"] is None:
                embed.description = "there is already no shop log channel"
                await interaction.response.send_message(embed=embed)
                return
            shop_log_channel = None

        dm_member_on_accept = True if dm_member_on_accept == 'true' else False
        await self.set_guild_settings(
            guild_id=interaction.guild_id,
            shoplog=shop_log_channel,
            dm_on_accept=dm_member_on_accept
        )
        embed.title = "``logging configuration``"
        embed.description = (
            f">>> {self.bot.right}"
            f"bot will now send item logs to channel {shop_log.mention} "
        )
        if remove == 'true':
            embed.description = f">>> {self.bot.right}" \
                                f"logging channel has been removed"
        await interaction.response.send_message(
            embed=embed)

    @setup.command(name="thread_msg")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_thread_message(
        self, interaction:discord.Interaction,
        thread_channel: discord.TextChannel,
        thread_message: app_commands.Range[str, 1, 500],
        set_default: Literal['true'] = None):

        channel_settings = await get_channel_settings(
            bot=self.bot, channel=thread_channel)
        embed = discord.Embed(title="command failed")
        if channel_settings is None or not channel_settings["is_threadchannel"]:
            embed.description = (
                f"Channel {thread_channel} is not a thread channel" 
                f"please run ``/channelconfig`` to see list of channels "
                f"in the guild ")
            await interaction.response.send_message(embed=embed)
            return

        if set_default is not None:
            thread_message = None

        await self.edit_channel_settings(
            channel=interaction.channel,
            thread_msg=thread_message
        )
        embed.title = "``config update``"
        embed.description = (
            f"thread message for the channel :{interaction.channel.mention}"
            f"has been updated to message: ``{thread_message}``"
        )
        await interaction.response.send_message(
            embed=embed
        )
