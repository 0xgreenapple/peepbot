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


async def handle_roles(bot: pepebot, message: discord.Message, reward_channel: int, user_limit: int, limits: list,
                       roles: list):
    print('i m here')
    if reward_channel:
        print('reward')

        if reward_channel == message.channel.id:
            print('hellooo')

            await bot.db.execute(
                """
                INSERT INTO test.msg(guild_id1,channel_id,user_id,limit1)
                VAlUES($1,$2,$3,$4)
                ON CONFLICT(guild_id1,channel_id,user_id) DO
                UPDATE SET limit1 =  COALESCE(msg.limit1, 0) + $4 ;
                """, message.guild.id, message.channel.id, message.author.id, 1
            )
            if limits:
                print('limits')

                user_role1 = None
                user_role2 = None
                user_role3 = None
                if roles[0]:
                    user_role1 = message.author.get_role(roles[0])
                if roles[1]:
                    user_role2 = message.author.get_role(roles[1])
                if roles[2]:
                    user_role3 = message.author.get_role(roles[2])

                if limits[0] and user_limit >= limits[0]:
                    print('adding')
                    if not user_role1:
                        if roles[0]:
                            role1 = message.guild.get_role(roles[0])
                            if role1:
                                await message.author.add_roles(role1)
                if limits[1] and user_limit >= limits[1]:
                    print('adding1')

                    if not user_role2:
                        if roles[1]:
                            role2 = message.guild.get_role(roles[1])
                            if role2:
                                await message.author.add_roles(role2)
                if limits[2] and user_limit >= limits[2]:
                    print('adding2')


                    if not user_role3:
                        if roles[2]:
                            role3 = message.guild.get_role(roles[2])
                            if role3:
                                await message.author.add_roles(role3)


async def handle_gallery(bot: pepebot, message: discord.Message, announcement_id: int, _is_gallery=False):
    vote_time = await bot.db.fetchval(
        """SELECT vote_time FROM test.setup
        WHERE guild_id1=$1""", message.guild.id
    )
    vote_time = vote_time if vote_time else 18

    reaction_count1 = await bot.db.fetchval(
        """SELECT likes FROM test.likes 
        WHERE guild_id1=$1 AND channel = $2""", message.guild.id, message.channel.id
    )
    reaction_count1 = reaction_count1 if reaction_count1 else 2

    def check(reaction, user):
        count = 0
        reaction_count = 0
        for reaction in message.reactions:
            if reaction.emoji.id == 1008402662070427668:
                reaction_count = reaction.count
                break

        return reaction_count >= reaction_count1

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=vote_time * 60,
                                            check=check)
    except asyncio.TimeoutError:
        pass
    else:

        reaction_count = 0
        for reaction in message.reactions:
            if reaction.emoji.id == 1008402662070427668:
                reaction_count = reaction.count
                break
        await bot.db.execute(
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
                    session: aiohttp.ClientSession = bot.aiohttp_session
                    e = await session.get(url=a.url)
                    a = await e.read()

                    if e.content_type.endswith('gif'):
                        fileext = '.gif'
                    else:
                        fileext = '.png'
                    if _is_gallery:
                        await channel.send(
                            content=message.content,
                            file=discord.File(fp=io.BytesIO(a),
                                              filename=f'{bot.user.name}{fileext}'))
                    else:
                        await channel.send(
                            content=f"by {message.author.mention}",
                            file=discord.File(fp=io.BytesIO(a),
                                              filename=f'{bot.user.name}{fileext}'))


class listeners(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def memes(self, message: discord.Message):

        if message.type != discord.MessageType.default:
            return

        if message.author.bot:
            return

        channel = await self.bot.db.fetchval("""SELECT meme_channel FROM test.channels WHERE guild_id1 =$1""",
                                             message.guild.id)
        is_disabled = await self.bot.db.fetchval("""SELECT listener FROM test.setup WHERE guild_id1 =$1""",
                                                 message.guild.id)
        if not is_disabled:
            return
        if not channel:
            return

        has_attachment = False
        has_embed = False

        if len(message.attachments):
            has_attachment = True

        elif len(message.embeds):
            for embed in message.embeds:
                if embed.type == 'image':
                    has_embed = True
                    break
        else:
            return

        if has_attachment or has_embed:
            message_check = re.sub(r'[^A-Za-z0-9]', '', message.content)
            if message_check.lower() == 'oc':
                pinned_msg = await message.channel.pins()
                if len(pinned_msg) == 50:
                    await pinned_msg[-1].unpin(reason='removing old pins')
                await message.pin(reason='original content')

    @commands.Cog.listener('on_message')
    async def thread_create(self, message: discord.Message):
        # check if the message is normal
        print('happening')

        if message.type != discord.MessageType.default:
            return

        if message.author.bot:
            return
        channel = await self.bot.db.fetchval(
            """SELECT channel_id FROM test.thread_channel WHERE guild_id =$1 and channel_id = $2""",
            message.guild.id, message.channel.id
        )
        is_enabled = await self.bot.db.fetchval(
            """SELECT thread_ls FROM test.setup WHERE guild_id1 =$1""",
            message.guild.id
        )
        print(channel)

        if not is_enabled:
            return
        if not channel:
            return
        print('has_attachment')
        has_attachment = False
        has_embed = False

        if len(message.attachments):
            has_attachment = True

        elif len(message.embeds):
            for embed in message.embeds:
                if embed.type == 'image':
                    has_embed = True
                    break
        else:
            return

        if has_attachment or has_embed:
            thread = await message.channel.create_thread(
                name=f"{message.author.name} ({message.created_at.microsecond})" if len(message.attachments)
                else f"{message.author.name} ({message.created_at.microsecond})",
                message=message, auto_archive_duration=1440)
            msg = await self.bot.db.fetchval(
                """
                SELECT msg FROM test.thread_channel WHERE guild_id = $1 AND channel_id = $2
                """, message.guild.id, message.channel.id
            )
            rolemention = await self.bot.db.fetchval(
                """
                SELECT mememanager_role FROM test.setup WHERE guild_id1 = $1
                """, message.guild.id
            )
            rolemention =  message.guild.get_role(rolemention)

            rolemention = rolemention.mention if rolemention else message.author.mention
            msg = msg if msg else f" {rolemention} Make Sure the meme is **original**"
            view = thread_channel(user=message.author)
            message = await thread.send(msg, view=view)
            return message

    @commands.Cog.listener('on_message')
    async def likes_handler(self, message: discord.Message):

        # return if system message
        if message.type != discord.MessageType.default:
            return
        if message.author.bot and message.author.id != self.bot.user.id:
            return
        if message.channel.type != discord.ChannelType.text:
            return

        if message.author.id == self.bot.user.id:
            m = message.content.replace('by', '').replace(' ', '').replace('<@', '').replace('>', '')
            member1 = message.guild.get_member(int(m))
            message.author = member1
            print(message.author.name)

        channel = await self.bot.db.fetchval(
            """
            SELECT reaction_channel FROM test.channels 
            WHERE guild_id1 =$1
            """, message.guild.id
        )
        is_disabled = await self.bot.db.fetchval(
            """
            SELECT reaction_ls 
            FROM test.setup WHERE
             guild_id1 =$1
             """, message.guild.id
        )

        if not is_disabled:
            return

        channels = await self.bot.db.fetch(
            """
            SELECT gallery_l1,gallery_l2,gallery_l3,gallery_l4,
            gallery_l5,gallery_l6
            FROM test.channels WHERE guild_id1= $1;
            """, message.guild.id
        )
        user_limit = await self.bot.db.fetchval(
            """
            SELECT limit1
            FROM test.msg WHERE guild_id1= $1 and channel_id=$2 AND user_id = $3;
            """, message.guild.id, message.channel.id, message.author.id
        )
        user_limit = user_limit if user_limit else 0

        is_reward = await self.bot.db.fetchval(
            """
            SELECT rewards FROM test.setup WHERE guild_id1 =$1
            """, message.guild.id
        )
        reward = await self.bot.db.fetch(
            """
            SELECT * FROM test.rewards 
            WHERE guild_id1=$1 AND channel_id1 = $2
            """, message.guild.id, message.channel.id
        )


        new_channels = [channels[0]['gallery_l1'],
                        channels[0]['gallery_l2'],
                        channels[0]['gallery_l3'],
                        channels[0]['gallery_l4'],
                        channels[0]['gallery_l5'],
                        channels[0]['gallery_l6']]

        limits = None
        roles = None
        reward_channel = None

        if is_reward:
            if reward or len(reward) != 0:
                reward_channel = reward[0]['channel_id1']
                limits = [reward[0]['limit_1'], reward[0]['limit_2'], reward[0]['limit_3']]
                roles = [reward[0]['role_1'], reward[0]['role_2'], reward[0]['role_3']]

        has_embed = False
        has_attachment = False
        if len(message.attachments):
            has_attachment = True
        elif len(message.embeds):
            for embed in message.embeds:
                if embed.type == 'image':
                    has_embed = True
                    break
        else:
            return

        if not has_embed and not has_attachment:
            return
        print(new_channels)
        if message.channel.id in channel:
            await message.add_reaction(self.bot.like)
            await message.add_reaction(self.bot.dislike)
            print('normal channel')
            if not new_channels[0]:
                return
            announcement_id = new_channels[0]
            await handle_roles(bot=self.bot,message=message,reward_channel=reward_channel,
                               user_limit=user_limit,limits=limits,roles=roles)

            await handle_gallery(bot=self.bot, message=message, announcement_id=announcement_id)

        elif message.channel.id == new_channels[0]:
            await message.add_reaction(self.bot.like)
            await message.add_reaction(self.bot.dislike)
            print('secondndnd',message.author.name)
            print('im gallery lvl1')
            print('limitsss',limits)
            await handle_roles(bot=self.bot, message=message, reward_channel=reward_channel,
                               user_limit=user_limit, limits=limits, roles=roles)

            if not new_channels[1]:
                return
            announcement_id = new_channels[1]
            await handle_gallery(bot=self.bot, message=message, announcement_id=announcement_id,
                                 _is_gallery=True
                                 )

        elif message.channel.id == new_channels[1]:
            await message.add_reaction(self.bot.like)
            await message.add_reaction(self.bot.dislike)

            await handle_roles(bot=self.bot, message=message, reward_channel=reward_channel,
                               user_limit=user_limit, limits=limits, roles=roles)

            print('im gallery lvl2')
            if not new_channels[2]:
                return
            announcement_id = new_channels[2]
            await handle_gallery(bot=self.bot, message=message, announcement_id=announcement_id,
                                 _is_gallery=True)

        elif message.channel.id == new_channels[2]:
            await message.add_reaction(self.bot.like)
            await message.add_reaction(self.bot.dislike)

            await handle_roles(bot=self.bot, message=message, reward_channel=reward_channel,
                               user_limit=user_limit, limits=limits, roles=roles)

            if not new_channels[3]:
                return
            announcement_id = new_channels[3]
            await handle_gallery(bot=self.bot, message=message, announcement_id=announcement_id,
                                 _is_gallery=True)

        elif message.channel.id == new_channels[3]:
            await message.add_reaction(self.bot.like)
            await message.add_reaction(self.bot.dislike)

            await handle_roles(bot=self.bot, message=message, reward_channel=reward_channel,
                               user_limit=user_limit, limits=limits, roles=roles)
            if not new_channels[4]:
                return
            announcement_id = new_channels[4]
            await handle_gallery(bot=self.bot, message=message, announcement_id=announcement_id,
                                 _is_gallery=True)
            print('galleryl 4')
        elif message.channel.id == new_channels[4]:
            await message.add_reaction(self.bot.like)
            await message.add_reaction(self.bot.dislike)
            await handle_roles(bot=self.bot, message=message, reward_channel=reward_channel,
                               user_limit=user_limit, limits=limits, roles=roles)

            if not new_channels[5]:
                return
            announcement_id = new_channels[5]
            await handle_gallery(bot=self.bot, message=message, announcement_id=announcement_id,
                                 _is_gallery=True)
            print('galleryl 5')


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        listeners(bot))
