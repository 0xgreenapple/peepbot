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
from handler.pagination import SimplePages,bal_leaderboard
from handler.view import duel_button
from pepebot import pepebot
import logging


class pointsleaderboard(bal_leaderboard):
    def __init__(self, entries: list, *, ctx: Context, per_page: int = 12, title: str = None):
        converted = entries
        print(entries)
        super().__init__(converted, per_page=per_page, ctx=ctx)


def mycheck():  # Creating the check
    async def startCheck(ctx: Context):  # This could be a async/sync.
        # Do whatever here. Note that this must return a bool (True/False). An example to check if the author is not the bot owner and if the member is in a guild.
        # If the check returns False (In this case, the author is the owner and/or the author is not in the guild), it would raise discord.ext.commands.CheckFailure. You can handle this in a on_command_error event.
        return ctx.author.id == 792917906165727264 or ctx.author.id == 888058231094665266

    return commands.check(startCheck)


class economy(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot

    @commands.command(name='add',aliases=['add_points'])
    @mycheck()
    async def add_points(self, ctx: Context, memeber: discord.Member, points: int = 1):
        await self.bot.db.execute("""
        INSERT INTO test.economy(guild_id,user_id,points)
        VALUES($1,$2,$3)
        ON CONFLICT (guild_id,user_id) DO
        UPDATE SET points = COALESCE(economy.points, 0) + $3 ;
        """, ctx.guild.id, memeber.id, points)

        total = await self.bot.db.fetchval(
            """SELECT points FROM test.economy WHERE guild_id = $1
            AND user_id = $2""",ctx.guild.id,memeber.id
        )
        embed = discord.Embed(
            title='``points added!``',
            description=f'>>> {self.bot.right} **user:**{memeber.mention} \n'
                        f'<a:aSDVstardrop:1007680622292123781> **points given:** {points} \n'
                        f'<:SDVitemeggbasket:1007685896184811550> **total points:** {total}'
        )
        await ctx.send(embed=embed)

    @commands.command(name='balance',aliases=['bal','points'])
    @commands.cooldown(1,3,BucketType.user)
    async def balance(self,ctx:Context,user:discord.Member=None):
        member = user if user else ctx.author

        msg = await self.bot.db.fetch(
            """ SELECT user_id,  points 
            from test.economy WHERE guild_id = $1
            order by points desc
            fetch first 10 rows only
            """, ctx.guild.id
        )
        total = await self.bot.db.fetchrow(
            """
            SELECT points, user_id FROM test.economy
            WHERE user_id=$1 AND guild_id=$2
            """, member.id, ctx.guild.id
        )
        if total is None:
            embed = discord.Embed(
                title='``stats``',
                description=f'>>> {self.bot.right} user: {member.mention} \n'
                            f'<a:aSDVstardrop:1007680622292123781> **total points:** 0 \n',
                colour=discord.Colour.blurple(), timestamp=discord.utils.utcnow()
            )
            await ctx.send(embed=embed)
            return

        likes = None
        number = None
        j = 1

        for i in msg:
            if total['user_id'] == i['user_id']:
                user_id = total['user_id']
                number = j
                likes = i['points']
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

        if user:
            embed = discord.Embed(
                title='``stats``',
                description=f'>>> {self.bot.right} user: {user.mention} \n'
                            f'<a:aSDVstardrop:1007680622292123781> **total points:** {likes} \n'
                            f'<:SDViconsword:1007685391932981308> **rank:#**{number} \n'
                            f'<:SDVjunimosamurai:1007685493909115040> **user is top:** {top_rank if top_rank else "90%"} ',
                colour=discord.Colour.blurple(),timestamp=discord.utils.utcnow()
            )
        else:
            embed = discord.Embed(
                title='``stats``',
                description=f'>>> <a:aSDVstardrop:1007680622292123781> **total points:** {likes} \n'
                            f'<:SDViconsword:1007685391932981308> **rank:#** {number} \n'
                            f'<:SDVjunimosamurai:1007685493909115040> **you are top:** {top_rank if top_rank else "90%"} ',
                colour = discord.Colour.blurple(), timestamp = discord.utils.utcnow()
            )
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard')
    async def pointsleaderboard(self, ctx: Context):

        msg = await self.bot.db.fetch(
            """ SELECT user_id,  points 
            from test.economy WHERE guild_id = $1
            order by points desc
            fetch first 50 rows only
            """, ctx.guild.id
        )

        if len(msg) == 0:
            await ctx.error_embed(description='the leaderboard for this guild is currently not available')
            return

        users = []
        j = 1
        for i in msg:
            user = ctx.guild.get_member(i['user_id'])
            if not user is None:
                users.append([user, i['points']])

        if users:
            warnings = pointsleaderboard(entries=users, per_page=10, ctx=ctx,
                                   title=f'``Leaderboard for {ctx.guild.name} : ``{len(users)}``')
            await warnings.start()



async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        economy(bot))
