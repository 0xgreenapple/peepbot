import asyncio
import io
import os
import random
from datetime import datetime, timedelta
from io import BytesIO
import re
import aiohttp
import discord
from discord import errors
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from handler.Context import Context
from handler.pagination import SimplePages
from handler.view import duel_button, thread_channel
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
        if message.type == discord.MessageType.chat_input_command:
            return

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
        if message.type == discord.MessageType.chat_input_command:
            return

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
                        thread = await message.channel.create_thread(
                            name=f"{message.author.name} ({message.created_at.microsecond})" if len(message.attachments)
                            else f"{message.author.name} ({message.created_at.microsecond})",
                            message=message, auto_archive_duration=1440)
                        view = thread_channel(user=message.author)
                        message = await thread.send(f'{message.author.mention} Make Sure the meme is **original**',
                                                    view=view)
                        return message

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
                        announcement_id = await self.bot.db.fetchval(
                            """SELECT announcement FROM test.setup
                                WHERE guild_id1 = $1""", message.guild.id
                        )
                        if announcement_id:
                            vote_time = await self.bot.db.fetchval(
                                """SELECT vote_time FROM test.setup 
                                WHERE guild_id1=$1""", message.guild.id
                            )
                            vote_time = vote_time if vote_time else 10

                            reaction_count1 = await self.bot.db.fetchval(
                                """SELECT reaction_count FROM test.setup 
                                WHERE guild_id1=$1""", message.guild.id
                            )
                            print(reaction_count1)

                            def check(reaction, user):
                                count = 0
                                reaction_count = 0
                                for reaction in message.reactions:
                                    if reaction.emoji.id == 1008402662070427668:
                                        reaction_count = reaction.count
                                        break


                                return reaction_count >= reaction_count1

                            try:
                                reaction, user = await self.bot.wait_for('reaction_add', timeout=vote_time * 60,
                                                                         check=check)
                            except asyncio.TimeoutError:
                                pass
                            else:

                                reaction_count = 0
                                for reaction in message.reactions:
                                    if reaction.emoji.id == 1008402662070427668:
                                        reaction_count = reaction.count
                                        break
                                await self.bot.db.execute(
                                            """
                                            INSERT INTO test.leaderboard(user_id1,guild_id1,likes)
                                            VALUES($1,$2,$3)
                                            ON CONFLICT (guild_id1,user_id1) DO
                                            UPDATE SET likes = COALESCE(leaderboard.likes, 0) + $3 ;
                                            """, message.author.id, message.guild.id, reaction_count
                                        )
                                channel = message.guild.get_channel(announcement_id)
                                if channel:
                                    if len(message.attachments):
                                        if message.attachments[0].content_type.startswith('image') or \
                                                message.attachments[0].content_type.startswith('video'):
                                            file = await message.attachments[0].to_file()
                                            await channel.send(f"by {message.author.mention}",
                                                               file=file)
                                    elif len(message.embeds):
                                        if message.embeds[0].type == 'image' or \
                                                message.embeds[0].type == 'video' or \
                                                message.embeds[0].type == 'gifv':
                                            a = message.embeds[0]
                                            session: aiohttp.ClientSession = self.bot.aiohttp_session
                                            e = await session.get(url=a.url)
                                            a = await e.read()

                                            if e.content_type.endswith('gif'):
                                                fileext = '.gif'
                                            else:
                                                fileext = '.png'

                                            await channel.send(
                                                content=f"by {message.author.mention}",
                                                file=discord.File(fp=io.BytesIO(a),
                                                                  filename=f'{self.bot.user.name}{fileext}'))

    # @commands.Cog.listener(name='on_raw_reaction_add')
    # async def on_reactioon(self, payload: discord.RawReactionActionEvent):
    #
    #     guild = self.bot.get_guild(payload.guild_id)
    #     channel = self.bot.get_channel(payload.channel_id)
    #     message = await channel.fetch_message(payload.message_id)
    #     has_embed = False
    #     print(payload)
    #     if len(message.embeds):
    #         has_embed = False
    #         for embed in message.embeds:
    #             if embed.type == 'image':
    #                 has_embed = True
    #                 break
    #     if not payload.emoji.id == 1008402662070427668:
    #         return
    #     print('emoji')
    #     print(len(message.attachments))
    #     print(has_embed)
    #     if not len(message.attachments) and not has_embed:
    #         return
    #     print('has attachment')
    #     if not message.attachments[0].content_type.startswith('image') or not \
    #             message.attachments[0].content_type.startswith('video'):
    #         return
    #
    #
    #
    #
    #
    #     announcement_id = await self.bot.db.fetchval(
    #         """SELECT announcement FROM test.setup
    #             WHERE guild_id1 = $1""", guild.id
    #     )
    #     print(announcement_id)
    #
    #     await self.bot.db.execute(
    #         """
    #         INSERT INTO test.leaderboard(user_id1,guild_id1,likes)
    #         VALUES($1,$2,$3)
    #         ON CONFLICT (guild_id1,user_id1) DO
    #         UPDATE SET likes = COALESCE(leaderboard.likes, 0) + $3 ;
    #         """, payload.member.id, guild.id, 1
    #     )
    #
    #     if announcement_id:
    #         channel = message.guild.get_channel(announcement_id)
    #         if channel:
    #             if len(message.attachments):
    #                 count = 0
    #                 for reaction in message.reactions:
    #                     if reaction.emoji.id == 1008402662070427668:
    #                         count = reaction.count
    #                         break
    #                 print(count)
    #                 file = await message.attachments[0].to_file()
    #                 if count == 2:
    #                     await channel.send(content=f'by {message.author.mention}',
    #                                        file=file
    #                                        )


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        listeners(bot))
