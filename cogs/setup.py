"""
:copyright: (C) 2022-present xgreenapple
:license: MIT.
"""
import asyncio
import logging
import discord
from discord import app_commands, Interaction
from discord.ext import commands
from pepebot import pepebot

import typing
from typing import Optional

from handler.utils import string_to_delta
from handler.database import (
    reinitialisedChannel_settings,
    reinitialisedGuild_settings,
)

_log = logging.getLogger(__name__)


class setup_memme(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot
        self.Database = bot.Database

    def setChannelSettings(
            self,
            channel: discord.TextChannel,
            *,
            is_memeChannel: bool = False,
            isThreadChannel: bool = False,
            is_oc_channel: bool = False,
            is_deadChat: bool = False,
            is_voteChannel: bool = False,
            thread_msg: Optional[str] = None,
            time: Optional[str] = None,
            max_like: int = 4,
    ) -> asyncio.Task:
        """
        Edit channel settings that is stored in the database
        """

        guild = channel.guild
        # change the string value to timedelta
        timedelta = string_to_delta(time) if time else None
        insert_data = self.Database.Insert(
            channel.id, guild.id, is_memeChannel,
            isThreadChannel, is_deadChat, is_voteChannel,
            is_oc_channel, thread_msg, timedelta, max_like,
            table="peep.Channels",
            columns="channel_id,"
                    "guild_id,"
                    "is_memeChannel,"
                    "is_threadChannel,"
                    "is_deadChat,"
                    "is_voteChannel,"
                    "is_ocChannel,"
                    "thread_msg,"
                    "voting_time,"
                    "max_like",
            values="$1,$2,$3,$4,$5,$6,$7,$8,$9,$10",
            on_Conflicts="(guild_id,channel_id) DO UPDATE SET "
                         "is_memeChannel = $3, "
                         "is_threadChannel=$4, "
                         "is_deadChat=$5, "
                         "is_voteChannel=$6, "
                         "is_ocChannel=$7, "
                         "thread_msg=$8, "
                         "voting_time=$9, "
                         "max_like=$10")
        self.bot.loop.create_task(reinitialisedChannel_settings(
            bot=self.bot, channel=channel)
        )
        return self.bot.loop.create_task(insert_data)

    async def setGuildSettings(
            self,
            guild: discord.Guild,
            *,
            reaction_lstnr=False,
            thread_lstnr=False,
            vote_time: int = None,
            vote: int = None,
            MemeAdmin: int = None,
            customization_time: int = None,
            oc=False):
        task = self.bot.Database.Insert(
            guild.id,
            reaction_lstnr,
            thread_lstnr,
            vote_time,
            vote,
            MemeAdmin,
            customization_time,
            oc,
            table="peep.guild_settings",
            columns="guild_id,"
                    "reaction_lstnr,"
                    "thread_lstnr,"
                    "vote_time,"
                    "vote,"
                    "MemeAdmin,"
                    "customization_time,"
                    "oc_lstnr",
            values="$1,$2,$3,$4,$5,$6,$7,$8",
            on_Conflicts="(guild_id) DO UPDATE SET "
                         "reaction_lstnr=$2, "
                         "thread_lstnr = $3, "
                         "vote_time = $4, "
                         "vote = $5, "
                         "MemeAdmin = $6,"
                         "customization_time = $7,"
                         "oc_lstnr=$8"
        )
        self.bot.loop.create_task(reinitialisedGuild_settings(
            bot=self.bot, guild_id=guild.id))
        return self.bot.loop.create_task(task)

    setup = app_commands.Group(
        name='setup',
        description='setup commands for you',
        guild_only=True,
        default_permissions=discord.Permissions(manage_guild=True)
    )

    @setup.command(name='help', description='help related to setup command')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f'``Setup``',
            description=f'>>> {self.bot.right} **run the following commands** \n'
                        f'``/setup vote <channel>`` : \n setup vote channel for you \n '
                        f'``/setup announcements <channel>`` :\n setup announcement channel for you !\n'
                        f'``/setup vote_time <time_in_minutes>`` : \nset voting time \n'
                        f'``/setup customization_time  <time_in_minutes>``:\n setup customisation time\n'
                        f'``/setup meme  <channel>``:\n setup meme channel to pin messages \n'
                        f'``/setup meme_listener <true_or_false> ``: \ndisable OC meme listener \n'
                        f'``/setup deadchat <true_or_false> ``: \ndisable deadchat  listener \n'
                        f'``/setup deadchat_role <role> ``: \n specify deadchat ping role \n'
                        f'``/setup thread <true_or_false> ``: \n disable thread  listener \n'
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="guild_settings", description="edit guild configuration")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(turn="turn on or off the whole system")
    async def editGuildSettings(
            self,
            interaction: discord.Interaction,
            option: typing.Literal["Auto Thread", "Meme listener", "Oc Listener"],
            turn: typing.Literal['on', 'off']):
        # change the value to boolean value
        turned = True if turn == 'on' else False
        settings_map = {
            "Auto Thread": "thread_lstnr",
            "Meme listener": "reaction_lstnr",
            "Oc Listener": "oc"
        }
        setting = settings_map[option]
        await self.setGuildSettings(guild=interaction.guild, **{setting: turned})
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"**updated config**",
                description=f">>> {self.bot.emoji.right} {option} has been turned ``{turn}``"
            ),
            ephemeral=True
        )

    @setup.command(name="channel_settings", description="edit specific channel settings")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(channel="the channel you want to change settings of",
                           option="chose a option you  want to edit",
                           turn="turn on or off whole option")
    async def editChannelSettings(
            self, interaction: Interaction, channel: discord.TextChannel,
            option: typing.Literal["Auto thread", "Meme listener", "Oc listener"],
            turn: typing.Literal["on", "off"]
    ):
        embed = discord.Embed(title="**updated Config**")
        permission = channel.permissions_for(interaction.guild.me)
        required_permissions = [permission.manage_messages, permission.view_channel,
                                permission.read_messages, permission.add_reactions]
        string = ["manage_messages", "view_channel", "read_messages", "add_reactions"]
        if not all(required_permissions):
            embed.title = f"**invalid permissions**"
            embed.description = f">>> {self.bot.right} bot missing any of " \
                                f"below permissions in channel:{channel.mention} \n" \
                                f" \n".join(string)
            await interaction.response.send_message(embed=embed,ephemeral=True)
            return

        turned = True if turn == "on" else False
        settings_map = {
            "Auto thread": "isThreadChannel",
            "Meme listener": "is_memeChannel",
            "Oc listener": "is_oc_channel"
        }
        setting = settings_map[option]
        await self.setChannelSettings(channel=channel,**{setting: turned})
        embed.title = "**updated config**"
        embed.description = f">>> {option} for {channel.mention} has been turned {turn}"
        await interaction.response.send_message(embed=embed,ephemeral=True)


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        setup_memme(bot))
