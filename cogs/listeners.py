import asyncio
import io
import os
import random
from io import BytesIO
import re
import aiohttp
import discord
from discord import errors
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


class listeners(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def memes(self, message: discord.Message):

        channel = await self.bot.db.fetchval("""SELECT memechannel FROM test.setup WHERE guild_id1 =$1""",
                                             message.guild.id)
        is_disabled = await self.bot.db.fetchval("""SELECT listener FROM test.setup WHERE guild_id1 =$1""",
                                             message.guild.id)
        channel_resolved = self.bot.get_channel(channel)
        has_embed = False
        if len(message.embeds):
            has_embed = False
            for embed in message.embeds:
                if embed.type == 'image':
                    has_embed = True
                    break
        if not message.author.bot:
            if is_disabled:
                if message.channel == channel_resolved:
                    if len(message.attachments) or has_embed:
                        message_check = re.sub(r'[^A-Za-z0-9]', '', message.content)
                        if message_check.lower() == 'oc':

                            pinned_msg = await message.channel.pins()
                            if len(pinned_msg) == 50:
                                await pinned_msg[-1].unpin(reason='removing old pins')
                            await message.pin(reason='original content')

    @commands.Cog.listener('on_message')
    async def submissions(self, message: discord.Message):

        channel = await self.bot.db.fetchval("""SELECT thread_channel FROM test.setup WHERE guild_id1 =$1""",
                                             message.guild.id)
        is_disabled = await self.bot.db.fetchval("""SELECT thread_ls FROM test.setup WHERE guild_id1 =$1""",
                                                 message.guild.id)
        channel_resolved = self.bot.get_channel(channel)

        has_embed = False
        if len(message.embeds):
            has_embed = False
            for embed in message.embeds:
                if embed.type == 'image':
                    has_embed = True
                    break
        if not message.author.bot:
            if is_disabled:
                if message.channel == channel_resolved:
                    if len(message.attachments) or has_embed:
                        await message.channel.create_thread(
                            name=message.attachments[0].filename if len(message.attachments)
                            else f"{message.author.name} submission"
                            ,message=message,auto_archive_duration=1440)
                        return


    @commands.Cog.listener('on_message')
    async def likes(self, message: discord.Message):
        if message.type == discord.MessageType.chat_input_command:
            return


        channel = await self.bot.db.fetchval("""SELECT reaction_channel FROM test.setup WHERE guild_id1 =$1""",
                                             message.guild.id)
        is_disabled = await self.bot.db.fetchval("""SELECT reaction_ls FROM test.setup WHERE guild_id1 =$1""",
                                                 message.guild.id)


        has_embed = False
        if len(message.embeds):
            has_embed = False
            for embed in message.embeds:
                if embed.type == 'image':
                    has_embed = True
                    break
        if not message.author.bot:
            if is_disabled:
                if message.channel.id in channel:
                    if len(message.attachments) or has_embed:
                        print('yes')
                        await message.add_reaction(self.bot.like)
                        await message.add_reaction(self.bot.dislike)


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        listeners(bot))
