import asyncio
import io

import random

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from handler.context import Context
from handler.view import duel_button
from pepebot import PepeBot

class duel(commands.Cog):
    def __init__(self, bot: PepeBot) -> None:
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
    #
    # @commands.command(name='meme_lb')
    # async def leaderboard(self, ctx: Context):
    #
    #     msg = await self.bot.db.fetch(
    #         """ SELECT user_id, likes
    #         from peep.leaderboard WHERE guild_id = $1
    #         order by likes desc
    #         fetch first 10 rows only
    #         """, ctx.guild.id
    #     )
    #
    #     if len(msg) == 0:
    #         await ctx.error_embed(description='the leaderboard for this guild is currently not available')
    #         return
    #
    #     users = []
    #     j = 1
    #     for i in msg:
    #         user = ctx.guild.get_member(i['user_id'])
    #         if user:
    #             users.append([user, i['likes']])
    #
    #     if users:
    #         warnings = leaderboard(entries=users, per_page=10, ctx=ctx,
    #                                title=f'``{ctx.guild.name} Leaderboard ``{len(users)}``')
    #         await warnings.start()

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


async def setup(bot: PepeBot) -> None:
    await bot.add_cog(
        duel(bot))
