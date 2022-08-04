import asyncio
import io
import os
import random
from io import BytesIO

import aiohttp
import discord
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

    @commands.group(name='setup', invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def setup_command(self, ctx: Context):
        embed = discord.Embed(
            title=f'``Setup``',
            description=f'>>> {self.bot.right} **run the following commands** \n'
                        f'``$setup vote <channel>`` : setup vote channel for you \n '
                        f'``$setup announcements <channel>`` : setup announcement channel for you !\n'
                        f'``$setup vote_time <time_in_minutes>`` :set voting time \n'
                        f'``$setup customization_time  <time_in_minutes>``: setup customisation time'
        )

        await ctx.send(embed=embed)

    @setup_command.command(name='vote')
    @commands.has_permissions(manage_guild=True)
    async def setup_vote(self, ctx: Context, channel: discord.TextChannel):

        send_message = channel.permissions_for(ctx.guild.me).send_messages
        read_messages = channel.permissions_for(ctx.guild.me).read_messages
        read_message_history = channel.permissions_for(ctx.guild.me).read_message_history
        if not send_message and not read_messages and not read_message_history:
            if (ctx.channel.type == discord.ChannelType.public_thread) or (
                    ctx.channel.type == discord.ChannelType.private_thread):
                await ctx.error_embed(
                    error_name='setup command error',
                    error_dis=f'{self.bot.right}i dont have permission to send messages in {channel.mention} \n'
                              f'make sure i have following permissions in that channel ``'
                              f'send messages`` ``read messages``'
                )
                return

        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,vote)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET vote = $2 ;
            """, ctx.guild.id, channel.id
        )
        embed = discord.Embed(
            title='``vote channel``',
            description=f"{self.bot.right} vote channel has been successfully updated to {channel.mention}"
        )
        await ctx.send(embed=embed)

    @setup_command.command(name='announcement')
    @commands.has_permissions(manage_guild=True)
    async def announcement(self, ctx: Context, channel: discord.TextChannel):
        send_message = channel.permissions_for(ctx.guild.me).send_messages
        read_messages = channel.permissions_for(ctx.guild.me).read_messages
        read_message_history = channel.permissions_for(ctx.guild.me).read_message_history
        if not send_message and not read_messages and not read_message_history:
            if (ctx.channel.type == discord.ChannelType.public_thread) or (
                    ctx.channel.type == discord.ChannelType.private_thread):
                await ctx.error_embed(
                    error_name='setup command error',
                    error_dis=f'{self.bot.right}i dont have permission to send messages in {channel.mention} \n'
                              f'make sure i have following permissions in that channel ``'
                              f'send messages`` ``read messages``'
                )
                return

        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,announcement)
            VALUES($1,$2) 
            ON CONFLICT (guild_id1) DO
            UPDATE SET announcement = $2 ;
            """, ctx.guild.id, channel.id
        )
        embed = discord.Embed(
            title='``vote channel``',
            description=f"{self.bot.right} announcement channel has been successfully updated to {channel.mention}"
        )
        await ctx.send(embed=embed)

    @setup_command.command(name='vote_time')
    @commands.has_permissions(manage_guild=True)
    async def vote_time(self, ctx: Context, voting_time: int):

        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,vote_time)
            VALUES($1,$2)
            ON CONFLICT (guild_id1) DO
            UPDATE SET vote_time = $2 ;
            """, ctx.guild.id, voting_time
        )

        embed = discord.Embed(
            title='``setup``',
            description=f'>>> {self.bot.right} **voting time has been updated to ``{voting_time}`` min**'
        )

        await ctx.send(embed=embed)

    @setup_command.command(name='customization_time')
    @commands.has_permissions(manage_guild=True)
    async def customisation_time(self, ctx: Context, customisation_time: int):

        await self.bot.db.execute(
            """
            INSERT INTO test.setup(guild_id1,customization_time)
            VALUES($1,$2)
            ON CONFLICT (guild_id1) DO
            UPDATE SET customization_time = $2 ;
            """, ctx.guild.id, customisation_time
        )

        embed = discord.Embed(
            title='``setup``',
            description=f'>>> {self.bot.right}**customisation time has been updated to ``{customisation_time}`` min**'
        )
        await ctx.send(embed=embed)


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        setup_memme(bot))
