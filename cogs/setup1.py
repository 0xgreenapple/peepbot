import asyncio
import io
import os
import random
import typing
from io import BytesIO

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from handler.Context import Context
from handler.pagination import SimplePages
from handler.view import duel_button
from pepebot import pepebot
import logging


class leaderboard(SimplePages):
    def __init__(self, entries: list, *, ctx: Context, per_page: int = 12, title: str = None):
        converted = entries
        print(entries)
        super().__init__(converted, per_page=per_page, ctx=ctx)


class setup_memme(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot

    setup = app_commands.Group(name='setup', description='setup commands for you', guild_only=True,
                               default_permissions=discord.Permissions(manage_guild=True))

    @setup.command(name='help', description='help related to setup command')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.default_permissions(manage_guild=True)
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

    @setup.command(name='deadchat_role', description='setup dead chat role')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    @app_commands.describe(
        role='deadchat ping role'
    )
    async def deadchat_role(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """ 
                INSERT INTO test.utils(guild_id1,role_id1)
                VALUES($1,$2)
                ON CONFLICT (guild_id1) DO
                UPDATE SET role_id1 = $2
            """, interaction.guild.id, role.id
        )

        embed = discord.Embed(
            title='``deadchat listener``',
            description=f"{self.bot.right} deadchat role has been updated to ``{role.mention}`` \n"
        )

        await interaction.followup.send(embed=embed)

    @setup.command(name='deadchat', description='enable or disable dead chat command')
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def deadchat_disable(self, interaction: discord.Interaction, type: typing.Literal['true', 'false']):
        await interaction.response.defer(ephemeral=True)
        if type == 'true':
            await self.bot.db.execute(
                """ 
                    INSERT INTO test.utils(guild_id1,active)
                    VALUES($1,$2)
                    ON CONFLICT (guild_id1) DO
                    UPDATE SET active = $2
                """, interaction.guild.id, True
            )
        elif type == 'false':
            await self.bot.db.execute(
                """ 
                    INSERT INTO test.utils(guild_id1,active)
                    VALUES($1,$2)
                    ON CONFLICT (guild_id1) DO
                    UPDATE SET active = $2
                """, interaction.guild.id, False
            )
        embed = discord.Embed(
            title='``deadchat listener``',
            description=f"{self.bot.right} deadchat listener has been updated to ``{type}`` \n"
                        f"to setup role do ``$setup deadchat_role <role>``"
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @setup.command(name='meme_listener', description='enable or disable meme listener')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def disable_meme(self, interaction: discord.Interaction, type: typing.Literal['true', 'false']):
        await interaction.response.defer(ephemeral=True)
        if type == 'true':
            await self.bot.db.execute(
                """ 
                INSERT INTO test.setup(guild_id1,listener)
                VALUES($1,$2)
                ON CONFLICT (guild_id1) DO
                UPDATE SET listener = $2
            """, interaction.guild.id, True
            )
        elif type == 'false':
            await self.bot.db.execute(
                """ 
                    INSERT INTO test.setup(guild_id1,listener)
                    VALUES($1,$2)
                    ON CONFLICT (guild_id1) DO
                    UPDATE SET listener = $2
                """, interaction.guild.id, False
            )
        embed = discord.Embed(
            title='``meme listener``',
            description=f"{self.bot.right} meme listener has been updated to ``{type}`` \n"
                        f"to setup channel do ``$setup meme <channel>``"
        )

        await interaction.followup.send(embed=embed)

    @setup.command(name='vote', description='setup vote channel')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def setup_vote(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,vote)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET vote = $2 ;
            """, interaction.guild.id, channel.id
        )
        embed = discord.Embed(
            title='``vote channel``',
            description=f"{self.bot.right} vote channel has been successfully updated to {channel.mention}"
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name='announcement', description='setup announcement channel')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def announcement(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,announcement)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET announcement = $2 ;
            """, interaction.guild.id, channel.id
        )
        embed = discord.Embed(
            title='``announcement channel``',
            description=f"{self.bot.right} announcement channel has been successfully updated to {channel.mention}"
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name='vote_time', description='setup voting time')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def vote_time(self, interaction: discord.Interaction, voting_time: int):
        if voting_time > 60:
            embed = discord.Embed(description=f'{self.bot.right} the time must be under 1 hours')
            await interaction.response.send_message(embed=embed, epehemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,vote_time)
            VALUES($1,$2)
            ON CONFLICT (guild_id1) DO
            UPDATE SET vote_time = $2 ;
            """, interaction.guild.id, voting_time
        )

        embed = discord.Embed(
            title='``setup``',
            description=f'>>> {self.bot.right} **voting time has been updated to ``{voting_time}`` min**'
        )

        await interaction.followup.send(embed=embed)

    @setup.command(name='customisation_time', description='setup customisation time')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def customisation_time(self, interaction: discord.Interaction, customisation_time: int):

        if customisation_time > 60:
            embed = discord.Embed(description=f'{self.bot.right} the time must be under 15 min')
            await interaction.response.send_message(embed=embed, epehemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,customization_time)
            VALUES($1,$2)
            ON CONFLICT (guild_id1) DO
            UPDATE SET customization_time = $2 ;
            """, interaction.guild.id, customisation_time
        )

        embed = discord.Embed(
            title='``setup``',
            description=f'>>> {self.bot.right}**customisation time has been updated to ``{customisation_time}`` min**'
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name='meme', description='setup meme channel for oc listener')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def meme(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,memechannel)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET memechannel = $2 ;
            """, interaction.guild.id, channel.id
        )
        embed = discord.Embed(
            title='``meme channel``',
            description=f"{self.bot.right} meme channel has been successfully updated to {channel.mention}"
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name='thread-listener', description='enable or disable thread-listener')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def disable_thread(self, interaction: discord.Interaction, type: typing.Literal['true', 'false']):
        await interaction.response.defer(ephemeral=True)
        if type == 'true':
            await self.bot.db.execute(
                """ 
                INSERT INTO test.setup(guild_id1,thread_ls)
                VALUES($1,$2)
                ON CONFLICT (guild_id1) DO
                UPDATE SET thread_ls = $2
            """, interaction.guild.id, True
            )
        elif type == 'false':
            await self.bot.db.execute(
                """ 
                    INSERT INTO test.setup(guild_id1,thread_ls)
                    VALUES($1,$2)
                    ON CONFLICT (guild_id1) DO
                    UPDATE SET thread_ls = $2
                """, interaction.guild.id, False
            )
        embed = discord.Embed(
            title='``meme listener``',
            description=f"{self.bot.right} thread listener has been updated to ``{type}`` \n"
                        f"to setup channel do ``/setup thread-channel <channel>``"
        )

        await interaction.followup.send(embed=embed)

    @setup.command(name='thread-channel', description='setup thread channel for oc listener')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def thread_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,thread_channel)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET thread_channel = $2 ;
            """, interaction.guild.id, channel.id
        )
        embed = discord.Embed(
            title='``thread channel``',
            description=f"{self.bot.right} thread channel has been successfully updated to {channel.mention}"
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name='shop-log', description='setup shop log channel')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def shop_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,shop_log)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET shop_log = $2 ;
            """, interaction.guild.id, channel.id
        )
        embed = discord.Embed(
            title='``shop_log channel``',
            description=f"{self.bot.right} shop_log channel has been successfully updated to {channel.mention}"
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name='reaction-channel',
                   description='add a reaction channel where bot will automatically react to memes')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def reaction_channel(self, interaction: discord.Interaction, mode: typing.Literal['remove', 'add'],
                               channel: discord.TextChannel,
                               ):
        await interaction.response.defer(ephemeral=True)

        channels = await self.bot.db.fetchval(
            """ SELECT reaction_channel FROM test.setup WHERE guild_id1=$1""",
            interaction.guild.id
        )
        if mode == 'add':
            if channels is not None:
                if channel.id in channels:
                    embed = discord.Embed(description=f'{self.bot.right} the channel is already in the list')
                    await interaction.followup.send(embed=embed)
                    return

        if channels is not None:
            if mode == 'remove':
                if channel.id not in channels:
                    embed = discord.Embed(
                        description=f'{self.bot.right} there is no channel called {channel.mention} in the list')
                    await interaction.followup.send(embed=embed)
                    return

        if channels is None:
            channels = []
            channels.append(channel.id)
        else:
            if mode == 'add':
                channels.append(channel.id)
            else:
                channels.remove(channel.id)

        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,reaction_channel)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET reaction_channel = $2 ;
            """, interaction.guild.id, channels
        )
        embed = discord.Embed(
            title='``reaction channel``',
            description=f"{self.bot.right} {channel.mention} {'added' if mode == 'add' else 'removed'} to the list"
        )
        await interaction.followup.send(embed=embed)

    @setup.command(name='reactions', description='enable or disable thread-listener')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def desable_reaction(self, interaction: discord.Interaction, type: typing.Literal['true', 'false']):
        await interaction.response.defer(ephemeral=True)
        if type == 'true':
            await self.bot.db.execute(
                """ 
                INSERT INTO test.setup(guild_id1,reaction_ls)
                VALUES($1,$2)
                ON CONFLICT (guild_id1) DO
                UPDATE SET reaction_ls = $2
            """, interaction.guild.id, True
            )
        elif type == 'false':
            await self.bot.db.execute(
                """ 
                    INSERT INTO test.setup(guild_id1,reaction_ls)
                    VALUES($1,$2)
                    ON CONFLICT (guild_id1) DO
                    UPDATE SET reaction_ls = $2
                """, interaction.guild.id, False
            )
        embed = discord.Embed(
            title='``meme listener``',
            description=f"{self.bot.right} reaction listener has been updated to ``{type}`` \n"
                        f"to setup channel do"
        )

        await interaction.followup.send(embed=embed)

    @setup.command(name='likes', description='how many likes need to get to the announcement channel')
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def likes(self, interaction: discord.Interaction, likes:int):
        await interaction.response.defer(ephemeral=True)
        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,reaction_count)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET reaction_count = $2 ;
            """, interaction.guild.id, likes
        )
        embed = discord.Embed(
            title='``likes ``',
            description=f"{self.bot.right} reaction counts has been updated to {likes}"
        )
        await interaction.followup.send(embed=embed)

async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        setup_memme(bot))
