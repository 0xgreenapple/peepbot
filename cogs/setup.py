import asyncio

import discord
from discord import app_commands, Interaction
from discord.ext import commands

import typing
from typing import (
    Optional,
    Literal
)

from handler.Context import Context
from handler.pagination import SimplePages
from handler.utils import string_to_delta, GetRelativeTime
from pepebot import pepebot
import logging

_log = logging.getLogger(__name__)


class setup_memme(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot
        self.Database = bot.Database

    def Edit_Channel(
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
        return self.bot.loop.create_task(insert_data)

    async def Guild_Settings(
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
        return self.bot.loop.create_task(task)

    async def Get_Guild_settings(self, guild: discord.Guild):
        """
        return the guild settings stored
        in database and in the cache if exists
        """
        # get cached data
        guild_data = self.bot.guild_cache.get(__key=guild.id)
        # cached guild settings
        cached_guild_settings = None
        # check if column is row or if not get data insert
        if guild_data is not None:
            cached_guild_settings = guild_data["guild_settings"]
        if cached_guild_settings is None:
            data = await self.bot.Database.Select(
                guild.id,
                table="peep.guild_settings",
                columns="*",
                condition="guild_id=$1",
                row=True
            )
            cached_guild_settings = data
        return cached_guild_settings

    async def Get_channel_settings(self, Channel: discord.TextChannel):
        guild_data = self.bot.guild_cache.get(__key=Channel.id)
        # cached guild settings
        cached_channel_settings = None
        if guild_data is not None:
            cached_channel_settings = guild_data["channel_settings"]
        if cached_channel_settings is None:
            data = await self.bot.Database.Select(
                Channel.id,
                Channel.guild.id,
                table="peep.Channels",
                columns="*",
                condition="guild_id=$2 AND channel_id = $1",
                row=True
            )
            cached_channel_settings = data
        return cached_channel_settings

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

    @setup.command(name="memes", description="on or off auto meme system")
    @app_commands.describe(turn="turn on or off the whole system")
    async def MemeListener(self, interaction: discord.Interaction, turn: typing.Literal['on', 'off']):
        # change the value to boolean value
        turned = True if turn == 'on' else False
        # insert value to the list
        await self.Guild_Settings(
            guild=interaction.guild, reaction_lstnr=turned)
        # send the message
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"**updated config**",
                description=f">>> {self.bot.emoji.right}the meme listener has been turned ``{turn}``"
            ),
            ephemeral=True
        )

    @setup.command(name="add_memes", description="Add meme channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        channel="The channel you want the bot to react in",
        maxlikes="the maximum like to get the meme to gallery",
        time="maximum time to listen for likes : ``1d,1h,1w,1s,1month``")
    async def AddMemes(self, interaction: Interaction, channel: discord.TextChannel, maxlikes: int = 4,
                       time: typing.Optional[str] = None):
        embed = discord.Embed()
        # check if bot has permission in the channel
        permission = channel.permissions_for(interaction.guild.me)
        if not (permission.add_reactions
                and permission.view_channel
                and permission.manage_messages):
            embed.title = f"**invalid permission**"
            embed.description = f'>>> bot missing permission in the channel'
            await interaction.response.send_message(embed=embed, ephemeral=True)
        # if max likes is less than 2 give a error message
        if maxlikes < 2:
            embed.title = f"**invalid settings**"
            embed.description = f"{self.bot.emoji.failed_emoji}" \
                                f" maximum likes must be at least 2"
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        # insert into database
        try:
            await self.Edit_Channel(
                channel=channel, max_like=maxlikes, time=time,
                is_memeChannel=True)
        except ValueError:
            embed.title = "**value error**"
            embed.description = f">>> {self.bot.emoji.failed_emoji} " \
                                f"time must be formate of: \n" \
                                f"1d = 1 day \n" \
                                f"1m = 1 minute \n" \
                                f"1h = 1 hour "
            await interaction.response.send_message(
                embed=embed
            )
            return
        timedelta = None
        if time:
            try:
                timedelta = string_to_delta(time)
            except ValueError:
                pass
            timedelta = GetRelativeTime(timedelta) if timedelta else None

        embed.title = "**updated config**"
        embed.description = f">>> set the {channel.mention} " \
                            f"to a meme channel " \
                            f"with voting time : {timedelta}"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="threads", description="on or off auto thread")
    @app_commands.describe(turn="turn on or off the whole system")
    async def ThreadListener(self, interaction: discord.Interaction, turn: typing.Literal['on', 'off']):
        # change string value to boolean value
        turned = True if turn == 'on' else False
        # add list to database
        await self.Guild_Settings(guild=interaction.guild, thread_lstnr=turned)
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"**updated config**",
                description=f">>> {self.bot.emoji.right} the thread listener has been turned ``{turn}``"
            ),
            ephemeral=True
        )

    @setup.command(name="add_threads", description="Add auto channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        channel="The channel you want the bot to make threads in",
        thread_msg="the message bot will send after creating thread"
    )
    async def AddThread(self, interaction: Interaction, channel: discord.TextChannel, thread_msg: str = None):
        """ ADD meme channel to list """
        embed = discord.Embed()
        # check if bot has permission in the channel
        permission = channel.permissions_for(interaction.guild.me)
        if not (permission.add_reactions
                and permission.view_channel
                and permission.manage_messages):
            embed.title = f"**invalid permission**"
            embed.description = f'>>> bot missing permission in the channel {channel.mention}'
            await interaction.response.send_message(embed=embed, ephemeral=True)
        # insert into database
        await self.Edit_Channel(
            channel=channel, isThreadChannel=True, thread_msg=thread_msg)
        embed.title = "**updated config**"
        embed.description = f">>> now bot will create threads when " \
                            f"a attachment in channel {channel.mention} posted"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="oc", description="on or off original content identifier")
    @app_commands.describe(turn="turn on or off the whole system")
    async def OCListener(self, interaction: discord.Interaction, turn: typing.Literal['on', 'off']):
        # change string value to boolean value
        turned = True if turn == 'on' else False
        # add list to database
        await self.Guild_Settings(guild=interaction.guild, oc=turned)
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"**updated config**",
                description=f">>> {self.bot.emoji.right} the oc listener has been turned ``{turn}``"
            ),
            ephemeral=True
        )

    @setup.command(name="add_oc", description="Add oc channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        channel="The channel you want the bot to pin messages in")
    async def AddOC(self, interaction: Interaction, channel: discord.TextChannel):
        """ ADD meme channel to list """
        embed = discord.Embed()
        # check if bot has permission in the channel
        permission = channel.permissions_for(interaction.guild.me)
        if not (permission.add_reactions
                and permission.view_channel
                and permission.manage_messages):
            embed.title = f"**invalid permission**"
            embed.description = f'>>> bot missing permission in the channel {channel.mention}'
            await interaction.response.send_message(embed=embed, ephemeral=True)
        # insert into database
        await selfEdit_Channel(
            channel=channel, is_oc_channel=True)
        embed.title = "**updated config**"
        embed.description = f">>> now bot will pin the messages " \
                            f"with attachments that contain oc text" \
                            f" in channel {channel.mention} posted"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="remove_oc", description="remove oc listener from channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        channel="the channel from where you want to remove oc listener")
    async def remove_OC(self, interaction: Interaction, channel: discord.TextChannel):
        embed = discord.Embed()
        # insert into database
        await self.Edit_Channel(
            bot=self.bot, channel=channel, is_oc_channel=False)
        embed.title = "**updated config**"
        embed.description = f">>> oc listener from channel {channel.mention} has been removed"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="remove_thread", description="remove auto thread from channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        channel="the channel from where you want to remove thread listener")
    async def remove_Thread(self, interaction: Interaction, channel: discord.TextChannel):
        embed = discord.Embed()
        # insert into database
        await self.Edit_Channel(
            channel=channel, isThreadChannel=False)
        embed.title = "**updated config**"
        embed.description = f">>> auto thread from channel {channel.mention} has been removed"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="remove_memes", description="remove meme reaction channel ")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        channel="the meme channel")
    async def remove_Memes(self, interaction: Interaction, channel: discord.TextChannel):
        embed = discord.Embed()
        # insert into database
        await self.Edit_Channel(
            channel=channel, is_memeChannel=False)
        embed.title = "**updated config**"
        embed.description = f">>> meme channel {channel.mention} has been removed"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @setup.command(name="thread_msg", description='change thread message of a auto thread channel')
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        channel="the auto thread channel",
        message="the new message text"
    )
    async def Thread_msg_update(
            self, interaction: discord.Interaction, channel: discord.TextChannel,
            message: str
    ):
        # check if the given channel have auto thread turned on or off
        is_thread_channel = await self.bot.Database.Select(
            interaction.guild.id,
            channel.id,
            table="peep.Channels",
            columns="is_threadChannel",
            condition="guild_id = $1 AND channel_id = $2"
        )
        # if channel is not a thread channel it will return a error message
        if not is_thread_channel:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="**invalid config**",
                    description=f">>> {channel.mention} is not a thread channel"
                )
            )
            return
        # edit the message
        await self.Edit_Channel(
            channel=channel, thread_msg=message)
        # send the response message
        embed = discord.Embed(
            title="**Updated config**",
            description=f">>> the thread message for channel {channel.mention} has been updated to \n"
                        f"{message}"
        )
        await interaction.response.send_message(embed=embed)

    @setup.command(name="update_likes", description='update the likes of meme channel')
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        channel="the auto thread channel")
    async def updateLikes(
            self, interaction: discord.Interaction, channel: discord.TextChannel, max_like: int = 2
    ):
        embed = discord.Embed()

        if max_like < 2:
            embed.title = "**invalid input**"
            embed.description = ">>> the max like must be maximum than 2"
            await interaction.response.send_message(
                embed=embed, ephemeral=True
            )

        isMemeChannel = await self.bot.Database.Select(
            interaction.guild.id,
            channel.id,
            table="peep.Channels",
            columns="is_memeChannel",
            condition="guild_id = $1 AND channel_id = $2"
        )

        if not isMemeChannel:
            embed.title = "**invalid config**"
            embed.description = ">>> the channel is not a meme channel"
        await self.Edit_Channel(
            channel=channel, max_like=max_like)
        # send the message
        embed.title = "**updated config**"
        embed.description = f">>> updated like for meme channel {channel.mention} to ``{max_like}``"
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        setup_memme(bot))
