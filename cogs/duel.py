import asyncio
import io

import random

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from handler.Context import Context
from handler.pagination import SimplePages
from handler.view import duel_button
from pepebot import pepebot


class leaderboard(SimplePages):
    def __init__(self, entries: list, *, ctx: Context, per_page: int = 12, title: str = None):
        converted = entries
        print(entries)
        super().__init__(converted, per_page=per_page, ctx=ctx)


class duel(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot

    @commands.command(name='battle')
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True, manage_threads=True)
    @commands.cooldown(2, 160, BucketType.member)
    async def duel(self, ctx: Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.error_embed(
                description='you cant duel your self!'
            )
            return
        if member.bot:
            await ctx.error_embed(
                description='you cant battle a bot'
            )
            return
        if (ctx.channel.type == discord.ChannelType.public_thread) or (
                ctx.channel.type == discord.ChannelType.private_thread):
            await ctx.error_embed(
                description='you cant run the battle command in a thread'
            )
            return

        response_msg = await ctx.send(f"{member.mention} has been invited for meme duel, status: waiting...")

        try:
            channel = await member.create_dm()
            view = duel_button(message=response_msg, member=member, user=ctx.author, bot=self.bot)
            embed = discord.Embed(title=f'you have been invited for meme battle by {ctx.author.name}')
            message = await channel.send(embed=embed, view=view)
            view.interaction_message = message

        except discord.Forbidden or discord.HTTPException:
            view = duel_button(message=response_msg, member=member, user=ctx.author, bot=self.bot)
            second_response = await response_msg.edit(content='failed to send message to user creating embed....')
            await asyncio.sleep(3)
            response2 = await second_response.edit(
                content=f"{member.mention} you have 20 min to accept the invite click on "
                        f"accept ", view=view)

    @commands.command(name='meme_lb')
    async def leaderboard(self, ctx: Context):

        msg = await self.bot.db.fetch(
            """ SELECT user_id, likes 
            from peep.leaderboard WHERE guild_id = $1
            order by likes desc
            fetch first 10 rows only
            """, ctx.guild.id
        )

        if len(msg) == 0:
            await ctx.error_embed(description='the leaderboard for this guild is currently not available')
            return

        users = []
        j = 1
        for i in msg:
            user = ctx.guild.get_member(i['user_id'])
            if user:
                users.append([user, i['likes']])

        if users:
            warnings = leaderboard(entries=users, per_page=10, ctx=ctx,
                                   title=f'``{ctx.guild.name} Leaderboard ``{len(users)}``')
            await warnings.start()

    @commands.command(name='template')
    @commands.cooldown(1, 5, BucketType.member)
    async def template(self, ctx: Context):
        session = self.bot.aiohttp_session
        a = await session.request(
            method='GET',
            url='https://api.imgflip.com/get_memes'
        )
        json = await a.json()
        memes = json['botconfig']['memes']
        ids = []

        for i in memes:
            if i['box_count'] == '2' or i['box_count'] == 2:
                ids.append(i['id'])
        memeid = random.choice(ids)

        for i in memes:
            if i['id'] == f'{memeid}':
                image = await session.get(url=i['url'])
                image_byets = await image.read()
                file = discord.File(fp=io.BytesIO(image_byets), filename='meme.png')

                await ctx.send(f"id:``{i['id']}``", file=file)
                break

    @commands.command(name='stats')
    @commands.guild_only()
    @commands.cooldown(4, 5, BucketType.user)
    async def stats(self, ctx: Context, member: discord.Member = None):
        member1 = member if member else ctx.author

        msg = await self.bot.db.fetch(
            """ SELECT user_id, likes 
            from peep.leaderboard WHERE guild_id = $1
            order by likes desc
            fetch first 10 rows only
            """, ctx.guild.id
        )

        stats = await self.bot.db.fetchrow(
            """
            SELECT likes, user_id FROM peep.leaderboard
            WHERE user_id=$1 AND guild_id=$2
            """, member1.id, ctx.guild.id
        )

        if stats is None:
            if not member:
                embed = discord.Embed(description=f'{self.bot.right} Stats for you are not available at the moment!')
            else:
                embed = discord.Embed(description=f'{self.bot.right} the stats for this user is not available!')

            await ctx.send(embed=embed)

            return
        users = []
        j = 1
        user_id = None
        number = None
        total = len(msg)
        likes = None
        print(msg)
        print(stats)
        for i in msg:
            if stats['user_id'] == i['user_id']:
                user_id = stats['user_id']
                number = j
                likes = i['likes']
                break

            j += 1

        top_rank = None

        if number is not None:

            percent = number / len(msg)
            if percent <= 0.1:
                top_rank = '1%'
            elif 0.1 <= percent <= 0.25:
                top_rank = '10%'
            elif 0.25 <= percent <= 0.50:
                top_rank = '25%'
            elif 0.50 <= percent <= 0.75:
                top_rank = '75%'
            else:
                top_rank = None

        if top_rank:
            if not member:
                msg = f'**rank**: #{number} \n you are top {top_rank} in the list'
            else:
                msg = f'**rank**: #{number} \n  {member1.name} top {top_rank} in the list'

        else:
            msg = f'**rank**: #{number}'

        embed = discord.Embed(
            title=f'``{member1.name}`` stats',
            description=f'>>> {self.bot.right} **User**:{member1.mention} \n'
                        f'**upvotes**:{likes}'
                        f'\n{msg} '

        )
        await ctx.send(embed=embed)


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        duel(bot))
