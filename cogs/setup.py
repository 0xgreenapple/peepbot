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
from discord.ext import commands

from pepebot import pepebot

from datetime import timedelta

import typing
from typing import Optional, Union, Literal

from handler.utils import (
    string_to_delta,
    getPlaceholders,
    getKeyPair,
    toStringList, GetRelativeTime)
from handler.database import (
    reinitialisedChannel_settings,
    reinitialisedGuild_settings,
    Get_channel_settings,
    Get_Guild_settings)

_log = logging.getLogger(__name__)


async def setup(bot: pepebot) -> None:
    await bot.add_cog(configuration(bot))


class configuration(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot
        self.Database = bot.Database

    async def setChannelSettings(self, guild_id, channel_id, **options):
        """
        Edit channel settings that is stored in the database
        """
        options_names = list(options.keys())
        options_names.insert(0, "guild_id")
        options_names.insert(1, "channel_id")
        names_str_list = toStringList(options_names)  # value1, value2,...
        placeholders_str = getPlaceholders(len(options_names))  # "$1,$2,$3,...
        options_names.remove("guild_id")
        options_names.remove("channel_id")
        key_value_str = getKeyPair(options_names, 3)
        values = list(options.values())
        values.insert(0, guild_id)
        values.insert(1, channel_id)

        await self.Database.Insert(
            *values,
            table="peep.channel_settings",
            columns=names_str_list,
            values=placeholders_str,
            on_Conflicts=
            "(guild_id,channel_id) DO UPDATE SET "
            f"{key_value_str}")
        # insert new settings to the guild cache,
        cache_new_settings = reinitialisedChannel_settings(
            bot=self.bot, channel_id=channel_id, guild_id=guild_id)
        self.bot.loop.create_task(cache_new_settings)

    async def setGuildSettings(self, guild_id, **options):
        """ change guild settings from the database"""
        options_names = list(options.keys())
        options_names.insert(0, "guild_id")
        names_str_list = toStringList(options_names)  # value1, value2, ...
        placeholders = getPlaceholders(len(options_names))  # $1, $2, $3, ...
        values = list(options.values())
        values.insert(0, guild_id)
        options_names.remove("guild_id")
        key_value_str = getKeyPair(options_names, 2)
        await self.bot.Database.Insert(
            *values,
            table="peep.guild_settings",
            columns=f"{names_str_list}",
            values=placeholders,
            on_Conflicts=
            "(guild_id) DO UPDATE SET "
            f"{key_value_str}")
        cache_new_settings = reinitialisedGuild_settings(
            bot=self.bot, guild_id=guild_id)
        self.bot.loop.create_task(cache_new_settings)

    def getValidEmojiString(self, string: str) -> Optional[str]:
        custom = string.replace(" ", "")
        firstEmoji = custom[0]
        dataType = unicodedata.category(firstEmoji)
        # it is a default emoji
        if dataType == "So":
            emoji = firstEmoji
        else:
            # check if given emoji is custom emoji
            emoji_id = self.bot.emoji.extractEmojiId(custom)
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
    async def editGuildSettings(
            self, interaction: discord.Interaction,
            option: Literal["Auto Thread", "Meme listener",
                            "Oc Listener", 'economy'],
            turn: Literal['on', 'off']):
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
        await self.setGuildSettings(
            guild_id=interaction.guild.id, **{setting: turned})

        embed = discord.Embed()
        embed.title = "``config update``"
        embed.description = f">>> {self.bot.emoji.right} {option}" \
                            f" has been turned ``{turn}``"
        await interaction.response.send_message(
            embed=embed, ephemeral=True)

    @setup.command(name="channel_settings")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def editChannelSettings(
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
            embed.description = f">>> {self.bot.right} bot missing following " \
                                f"permissions in {channel.mention} channel" \
                                f":{channel.mention} \n" \
                                f" \n".join(permission_string)
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
        await self.setChannelSettings(
            channel_id=channel.id, guild_id=channel.guild.id, **{setting: turned})
        embed.title = "**updated config**"
        embed.description = f">>> {option} for {channel.mention} has been turned {turn}"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="edit_meme_channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setMemeChannelSettings(
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
        Response = interaction.response
        embed = discord.Embed(title=f"``command failed``")
        channel_settings = await Get_channel_settings(
            bot=self.bot, Channel=meme_channel)
        # send a error message if given channel is not a meme channel
        if channel_settings is None or not channel_settings["is_memechannel"]:
            embed.description = \
                f">>> {self.bot.right} {meme_channel.mention} channel" \
                f" is not a meme channel, pls run command ``/config " \
                f"{meme_channel.name}`` to check if the channel is a " \
                f"meme channel or ``/serverconfig`` to see list of " \
                f"meme channels in the gild "
            await Response.send_message(embed=embed, ephemeral=True)
            return
        delta_time = 'NULL' if duration == '0' else duration
        if delta_time is not None and duration != '0':
            try:
                delta_time = string_to_delta(duration)
            except Exception as error:
                embed.description = \
                    f">>> {self.bot.right} the time ``{duration}`` is " \
                    f"invalid it must be in formate of" \
                    f"```1(h|hr|hour|hours) \n 1(m|min|minute) \n" \
                    f" 1(s|second|secs)``` "
                await Response.send_message(embed=embed, ephemeral=True)
                _log.error(error)
                return
        args = {}
        if max_likes is not None:
            if max_likes <= 1:
                embed.description = f">>> {self.bot.right}" \
                                    f" max likes must be greater than 1"
                await Response.send_message(embed=embed, ephemeral=True)
                return
            elif max_likes > 1:
                args["max_like"] = max_likes

        if delta_time is not None:
            args["voting_time"] = delta_time if delta_time != 'NULL' else None
        if next_gallery_channel:
            args["Nextlvl"] = next_gallery_channel.id

        await self.setChannelSettings(
            interaction.guild_id, interaction.channel_id, **args)

        embed.title = f"``updated config``"
        isDeltaTime = isinstance(delta_time, timedelta)
        humanRelativeTime = GetRelativeTime(delta_time) if isDeltaTime else "none"
        embed.description = f"""
        >>> {self.bot.right} **channel**:{meme_channel.mention}
        **maximum likes**: {max_likes}
        **gallery**: {next_gallery_channel.mention if next_gallery_channel else "none"}
        **time limit**: {humanRelativeTime}
        """
        return await Response.send_message(embed=embed)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    @setup.command(name="meme_admin_role")
    async def addMemeAdminRole(self, interaction: Interaction, role: discord.Role,
                               remove: Literal['true']):
        """
        add A role to manage economy related commands.

        Parameters
        ----------
        role:
            role that you wanted to manage commands
        """

        embed = discord.Embed()
        if interaction.guild.owner_id != interaction.user.id:
            embed.title = "``command failed!``"
            embed.description = "only owner can execute this command"
            await interaction.response.send_message(
                embed=embed, ephemeral=True)
            return
        await self.setGuildSettings(
            guild_id=interaction.guild.id, MemeAdmin=role.id)
        embed.title = "``role Added``"
        embed.description = \
            f">>> {self.bot.right} now members with " \
            f"{role.mention} will be able to execute " \
            f"all economy commands "
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.checks.has_permissions(administrator=True)
    @setup.command(name="like")
    async def setupLikeEmoji(
            self, interaction: Interaction, custom_emoji: str = None,
            setdefault: Literal['true'] = None, remove: Literal['true'] = None):
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
        embed = discord.Embed(title="``command failed``")
        emoji = ""
        if not any([custom_emoji, setup(), remove]):
            embed.description = f">>> {self.bot.emoji.right} " \
                                f"you must specify at least one setting"
            await interaction.response.send_message(embed=embed)
            return
        if custom_emoji is not None:
            emoji = self.getValidEmojiString(string=custom_emoji)
            if emoji is None:
                embed.description = f">>> {self.bot.emoji.right}" \
                                    f"given emoji is not a valid emoji :``{custom_emoji}``"
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        elif setdefault is not None:
            emoji = self.bot.emoji.like
        elif remove is not None:
            emoji = '0'
        await self.setChannelSettings(
            guild_id=interaction.guild_id, channel_id=interaction.channel_id,
            like_emoji=str(emoji))
        embed.title = "``updated config``"
        embed.description = f"now bot will react to {emoji}"
        if emoji == '0':
            embed.description = f"now bot will not able to like messages"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.checks.has_permissions(administrator=True)
    @setup.command(name="dislike")
    async def setupLikeEmoji(
            self, interaction: Interaction, custom_emoji: str = None,
            setdefault: Literal['true'] = None, remove: Literal['true'] = None):
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
        embed = discord.Embed(title="``command failed``")
        emoji = ""
        if not any([custom_emoji, setdefault, remove]):
            embed.description = f">>> {self.bot.emoji.right} " \
                                f"you must specify at least one setting"
            await interaction.response.send_message(embed=embed)
            return
        if custom_emoji is not None:
            emoji = self.getValidEmojiString(string=custom_emoji)
            if emoji is None:
                embed.description = f">>> {self.bot.emoji.right}" \
                                    f"given emoji is not a valid emoji :``{custom_emoji}``"
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        elif setdefault is not None:
            emoji = self.bot.emoji.like
        elif remove is not None:
            emoji = '0'
        await self.setChannelSettings(
            guild_id=interaction.guild_id, channel_id=interaction.channel_id,
            dislike_emoji=str(emoji))
        embed.title = "``updated config``"
        embed.description = f"now bot will react to {emoji}"
        if emoji == '0':
            embed.description = f"now bot will not able to dislike messages"
        await interaction.response.send_message(embed=embed, ephemeral=True)