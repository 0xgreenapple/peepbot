"""
:copyright: (C) 2022-present 0xgreenapple
:license: MIT.
"""
import asyncio
import logging
from datetime import timedelta

import discord
from discord import app_commands, Interaction
from discord.ext import commands
from pepebot import pepebot

import typing
from typing import Optional, Union, Literal

from handler.utils import (
    string_to_delta,
    getPlaceholders,
    getKeyPair,
    KeyStr, GetRelativeTime
)
from handler.database import (
    reinitialisedChannel_settings,
    reinitialisedGuild_settings,
    Get_channel_settings,
    Get_Guild_settings
)


_log = logging.getLogger(__name__)


class setup_memme(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot
        self.Database = bot.Database

    async def setChannelSettings(self, guild_id, channel_id, **options):
        """
        Edit channel settings that is stored in the database
        """
        options_key = list(options.keys())
        options_key.insert(0, "guild_id")
        options_key.insert(1, "channel_id")
        keys_str = KeyStr(options_key)
        placeholders = getPlaceholders(len(options_key))
        options_key.remove("guild_id")
        options_key.remove("channel_id")
        key_value_str = getKeyPair(options_key, 3)
        values = list(options.values())
        values.insert(0, guild_id)
        values.insert(1, channel_id)
        await self.Database.Insert(
            *values,
            table="peep.Channels",
            columns=keys_str,
            values=placeholders,
            on_Conflicts="(guild_id,channel_id) DO UPDATE SET "
                         f"{key_value_str}")
        self.bot.loop.create_task(reinitialisedChannel_settings(
            bot=self.bot, channel_id=channel_id, guild_id=guild_id)
        )

    async def setGuildSettings(self, guild_id, **options):
        """ change guild settings from the database"""
        keys = list(options.keys())
        keys.insert(0, "guild_id")
        keys_str = KeyStr(keys)
        placeholders = getPlaceholders(len(keys))
        values = list(options.values())
        values.insert(0, guild_id)
        keys.remove("guild_id")
        key_value_str = getKeyPair(keys,2)
        await self.bot.Database.Insert(
            *values,
            table="peep.guild_settings",
            columns=f"{keys_str}",
            values=placeholders,
            on_Conflicts="(guild_id) DO UPDATE SET "
                         f"{key_value_str}")
        cacheGuildSettings = reinitialisedGuild_settings(
            bot=self.bot, guild_id=guild_id)
        self.bot.loop.create_task(cacheGuildSettings)

    setup = app_commands.Group(
        name='setup',
        description='setup commands for you',
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
         edit specific guild settings.

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
        embed = discord.Embed(title="**updated Config**")
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
            self, interaction: Interaction, meme_channel: discord.TextChannel,
            duration: Optional[str] = None, max_likes: Optional[int] = None,
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
        channel_settings = await Get_channel_settings(bot=self.bot, Channel=meme_channel)
        # send a error message if given channel is not a meme channel
        if channel_settings is None or not channel_settings["is_memechannel"] :
            embed.description = \
                f">>> {self.bot.right} {meme_channel.mention} channel" \
                f" is not a meme channel, pls run command ``/config " \
                f"{meme_channel.name}`` to check if the channel is a " \
                f"meme channel or ``/serverconfig`` to see list of " \
                f"meme channels in the gild "
            return await Response.send_message(embed=embed, ephemeral=True)

        # set default vale to null only if duration given is 0
        delta = 'NULL' if duration == '0' else duration
        # parse string to timedelta value only
        if delta and duration != '0':
            try:
                delta = string_to_delta(duration)
            except:
                embed.description = \
                    f">>> {self.bot.right} the time ``{duration}`` is " \
                    f"invalid it must be in formate of" \
                    f"```1(h|hr|hour|hours) \n 1(m|min|minute) \n" \
                    f" 1(s|second|secs)``` "
                return await Response.send_message(embed=embed, ephemeral=True)

        args = {}
        if max_likes is not None:
            if max_likes <= 1:
                embed.description = f">>> {self.bot.right} max likes must be greater than 1"
                return await Response.send_message(embed=embed, ephemeral=True)
            elif max_likes > 1:
                args["max_like"] = max_likes
        if delta is not None:
            args["voting_time"] = delta if delta != 'NULL' else None
        if next_gallery_channel:
            args["Nextlvl"] = next_gallery_channel.id

        await self.setChannelSettings(
            guild_id=interaction.guild.id, channel_id=interaction.channel_id, **args)
        embed.title = f"``updated config``"
        embed.description = f"""
                >>> {self.bot.right} **channel**:{meme_channel.mention}
                **maximum likes**: {max_likes}
                **gallery**: {next_gallery_channel.mention if next_gallery_channel else "none"}
                **time limit**: {GetRelativeTime(delta) if isinstance(delta,timedelta) else "none"}
                """
        return await Response.send_message(embed=embed)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(manage_roles=True)
    @setup.command(name="meme_admin_role")
    async def addMemeAdminRole(self, interaction: Interaction, role: discord.Role):
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
        embed.description = f">>> {self.bot.right} now members with " \
                            f"{role.mention} will be able to execute " \
                            f"all economy commands "
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        setup_memme(bot))
