from __future__ import annotations

import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from handler.Context import Context
from handler.pagination import SimplePages, bal_leaderboard
from handler.view import duel_button, accept_bought
from handler.utils import send_error, if_user_mememanager, user_check_self
from handler.economy import Economy, UserHasNotEnoughCoins
from pepebot import pepebot
import logging

log = logging.getLogger(__name__)

class pointsleaderboard(bal_leaderboard):
    def __init__(self, entries: list, *, ctx: Context, per_page: int = 12, title: str = None):
        converted = entries
        print(entries)
        super().__init__(converted, per_page=per_page, ctx=ctx)


def mycheck():  # Creating the check
    async def startCheck(ctx: Context):
        return ctx.author.id == ctx.guild.owner.id or ctx.author.id == 888058231094665266

    return commands.check(startCheck)


class economy(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot
        self.economy = Economy(self.bot.Database)

    @commands.command(name='add', aliases=['add_points'], description="Add points to user")
    async def add_points(self, ctx: Context, member: discord.Member, points: float = 0.1):

        # check if a user has meme_manager role
        is_meme_manager = await if_user_mememanager(
            bot=self.bot, ctx=ctx)
        if not is_meme_manager:
            return

        # check if user running command on themselves
        await user_check_self(bot=self.bot, member=member, ctx=ctx)

        # adding points
        await self.economy.addUserCoins(user=member, coins=points)

        # the total points
        total = await self.economy.getUserCoins(member)

        embed = discord.Embed(
            title='``points added!``',
            description=f'>>> {self.bot.right} **user:**{member.mention} \n'
                        f'{self.bot.coin} **points given:** {points} \n'
                        f'<:SDVitemeggbasket:1007685896184811550> **total points:** {total}'
        )

        await ctx.send(embed=embed)

    @commands.command(
        name='reset_points', aliases=['reset_coins'], description='reset the user points to given value')
    async def reset_coins(self, ctx: Context, member: discord.Member, point: float):

        is_meme_manager = await if_user_mememanager(bot=self.bot, ctx=ctx)
        if not is_meme_manager:
            return

        # resting points and get total coins
        await self.economy.setUserCoins(member, coins=point)
        total = await self.economy.getUserCoins(member)

        embed = discord.Embed(
            description=f'>>> {self.bot.right} User points has been reset to ``{point}``,'
                        f' now user has ``{total}`` {self.bot.coin} points'
        )
        await ctx.send(embed=embed)

    @commands.command(name='remove', aliases=['remove_points', 'remove_coins'])
    async def remove_points(self, ctx: Context, member: discord.Member, points: float = 1):

        is_meme_manager = await if_user_mememanager(bot=self.bot, ctx=ctx)
        if not is_meme_manager:
            return

        total = await self.economy.getUserCoins(user=member)

        if total == 0:
            embed = discord.Embed(
                description=f'{self.bot.right} this user has no points to remove')
            await ctx.send(embed=embed)
            return

        total = await self.economy.removeUserCoins(user=member, coins=points)

        embed = discord.Embed(
            title='``points removed!``',
            description=f'>>> {self.bot.right} **user:**{member.mention} \n'
                        f'<a:coin1:1008074318082752583> **points removed:** {points} \n'
                        f'<:SDVitemeggbasket:1007685896184811550> **total points:** {total}'
        )
        await ctx.send(embed=embed)

    @commands.command(name='reset', description="set the user coins to 0")
    async def reset_points(self, ctx: Context, member: discord.Member):

        is_meme_manager = await if_user_mememanager(bot=self.bot, ctx=ctx)
        if not is_meme_manager:
            return

        total = await self.economy.getUserCoins(user=member)

        if total == 0:
            embed = discord.Embed(
                description=f'{self.bot.right} this user already has 0 points')
            await ctx.send(embed=embed)
            return
        # set user coins to 0
        total = await self.economy.setUserCoins(user=member)

        embed = discord.Embed(
            title='``points reset!``',
            description=f'>>> {self.bot.right} **user:**{member.mention} \n'
                        f'<a:coin1:1008074318082752583> **points removed:** all \n'
                        f'<:SDVitemeggbasket:1007685896184811550> **total points:** {total}'
        )
        await ctx.send(embed=embed)

    @commands.command(name='give', aliases=['transfer'], description="give user points to other user")
    @commands.cooldown(1, 5, BucketType.user)
    async def give_points(self, ctx: Context, member: discord.Member, points: float):

        total_author = None
        total_member = None
        try:
            total_member, total_author = await self.economy.GivePoints(author=ctx.author, user=member,
                                                                       coins=abs(points))
        except UserHasNotEnoughCoins:  # catch the exception , raised when user don't have enough coins
            embed = discord.Embed(description=f'{self.bot.right} you dont enough points to give')
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title='``transfer!``',
            description=f'>>> {self.bot.right} **user:**{member.mention} \n'
                        f'<a:coin1:1008074318082752583> **coins given:** {points} \n'
                        f'<:SDVitemeggbasket:1007685896184811550> **total points:** {total_member}\n'
                        f'{self.bot.right} now you have {total_author} {self.bot.coin}'
        )
        await ctx.send(embed=embed)

    @commands.command(name='balance', aliases=['bal', 'points'])
    @commands.cooldown(1, 3, BucketType.member)
    async def balance(self, ctx: Context, user: discord.Member = None):
        member = user if user else ctx.author

        msg = await self.bot.db.fetch(
            """ SELECT user_id,  points 
            from test.economy WHERE guild_id = $1
            order by points desc
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
                            f'<a:coin1:1008074318082752583> **total points:** 0 \n',
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
                            f'<a:coin1:1008074318082752583> **total points:** {round(likes, 2)} \n'
                            f'<:SDViconsword:1007685391932981308> **rank:#**{number} \n'
                            f'<:SDVjunimosamurai:1007685493909115040> **user is top:** {top_rank if top_rank else "90%"} ',
                colour=discord.Colour.blurple(), timestamp=discord.utils.utcnow()
            )
        else:
            embed = discord.Embed(
                title='``stats``',
                description=f'>>> <a:coin1:1008074318082752583> **total points:** {round(likes, 2)} \n'
                            f'<:SDViconsword:1007685391932981308> **rank:#** {number} \n'
                            f'<:SDVjunimosamurai:1007685493909115040> **you are top:** {top_rank if top_rank else "90%"} ',
                colour=discord.Colour.blurple(), timestamp=discord.utils.utcnow()
            )

        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', aliases=['lb'])
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
                users.append([user, round(i['points'], 2)])

        if users:
            warnings = pointsleaderboard(entries=users, per_page=10, ctx=ctx,
                                         title=f'``Leaderboard for {ctx.guild.name} : ``{len(users)}``')
            await warnings.start()

    @commands.command(name='add_item')
    @commands.is_owner()
    async def shop1(self, ctx: Context, cost: int, emoji: int, *, name: str):
        emoji = self.bot.get_emoji(emoji)

        await self.bot.db.execute("""
            INSERT INTO test.shop(items,cost,emoji)
            VALUES($1,$2,$3)
            ON CONFLICT (items) DO
            UPDATE SET cost = $2,emoji = $3 ;
            """, name, cost, emoji)
        await ctx.send('item added')

    @commands.command(name='remove_user_item ')
    async def remove_user_item(self, ctx: Context, member: discord.Member, *, itemname: str):

        role = await self.bot.db.fetchval(
            """
            SELECT mememanager_role FROM test.setup WHERE guild_id1 = $1
            """, ctx.guild.id
        )

        role = ctx.guild.get_role(role) if role else None

        # check the member has meme manager role if not owner
        if not ctx.author.id == ctx.guild.owner.id:
            if role not in ctx.author.roles:
                return
            if ctx.author.id == member.id:
                await send_error(
                    bot=self.bot,
                    ctx=ctx,
                    msg="you cant add to point to yourself, only owner can do it ")
        item = await self.bot.db.fetch(
            """
            SELECT items,cost FROM test.shop WHERE items = $1
            """, itemname)
        print(item)
        user_items = await self.bot.db.fetchval(
            """
            SELECT items FROM test.inv 
            WHERE items = $1 AND user_id = $2 AND guild_id = $3
            """,
            itemname, member.id, ctx.guild.id
        )
        print(user_items)

        if len(item) == 0:
            await ctx.error_embed(description='the item doesnt exist')
            return
        if user_items is None:
            await ctx.error_embed(description=f'the user already not have the item : {itemname}')

        insert_item = await self.bot.db.execute(
            """
            DELETE FROM test.inv 
            WHERE items = $1 AND user_id = $2 AND guild_id = $3
            """,
            itemname, member.id, ctx.guild.id
        )
        points = await self.bot.db.fetchval(
            """SELECT points FROM test.economy WHERE guild_id = $1 AND user_id= $2 """, ctx.guild.id, member.id
        )

        total_sub_poinst = points + item[0]['cost'] if points else item[0]['cost']

        await self.bot.db.execute(
            """
            UPDATE test.economy SET points = $1 WHERE user_id = $2 AND guild_id = $3
            """, total_sub_poinst, member.id, ctx.guild.id
        )
        await ctx.send(embed=discord.Embed(
            description=f'>>> item {itemname} removed from {member.mention},'
                        f'**the points refunded**')
        )

    @commands.command(name='remove_item')
    @commands.is_owner()
    async def shopremove(self, ctx: Context, *, name: str):

        value = await self.bot.db.fetchval("""
                        SELECT items FROM test.shop WHERE items = $1
                        """, name)
        if not value:
            await ctx.send(
                embed=discord.Embed(description="the item already not in list")
            )
            return

        await self.bot.db.execute("""
                DELETE FROM test.shop
               WHERE items = $1
                """, name)
        await ctx.send('item removed')

    @commands.command(name='shop')
    @commands.cooldown(1, 5, BucketType.member)
    async def shop(self, ctx: Context):
        items = await self.bot.db.fetch(
            """
            SELECT * FROM test.shop
        """)
        shop_items = []
        for i in items:
            shop_items.append(f'{i["emoji"]} **{i["items"]}** ``cost``: {i["cost"]} {self.bot.coin} \n')

        embed = discord.Embed(
            title='``shop``'
        )
        embed.add_field(
            name=f"<:SDVitemtreasure:1008374574502658110> items",
            value=f">>> {''.join(shop_items)}")

        await ctx.send(embed=embed)

    @commands.command(name='buy')
    @commands.cooldown(1, 5, BucketType.member)
    async def buy(self, ctx: Context, *, item: str):

        items = await self.bot.db.fetch(
            """
            SELECT items,cost,emoji FROM test.shop
        """)
        itemname = ''
        maxcoin = 0
        emoji = ''

        for i in items:
            if item.lower() == i['items']:
                itemname = i['items']
                maxcoin = i['cost']
                emoji = i['emoji']
                break

        user_coin = await self.bot.db.fetchval(
            """
            SELECT points FROM test.economy WHERE guild_id = $1 AND user_id= $2
            """, ctx.guild.id, ctx.author.id
        )
        embed = discord.Embed()

        resolved = [i['items'] for i in items]
        isalready = await self.bot.db.fetchval(
            """SELECT 1 FROM test.inv WHERE user_id = $1 AND guild_id = $2 AND items=$3""",
            ctx.author.id, ctx.guild.id, itemname
        )

        if not item in resolved:
            embed.description = f'{self.bot.right} item {item} doesnt not exists,pls check ``$shop``'
            await ctx.send(embed=embed)
            return
        if isalready:
            embed.description = f'{self.bot.right} you cant buy more than one item'
            await ctx.send(embed=embed)
            return
        if user_coin < maxcoin:
            embed.description = f'{self.bot.right} you dont have enough coins to buy  {itemname}'
            await ctx.send(embed=embed)
            return

        minnamount = user_coin - maxcoin

        await self.bot.db.execute(
            """
            UPDATE test.economy SET points = $1 WHERE user_id = $2 AND guild_id = $3
            """, minnamount, ctx.author.id, ctx.guild.id
        )

        user_coin1 = await self.bot.db.fetchval(
            """
            SELECT points FROM test.economy WHERE guild_id = $1 AND user_id= $2
            """, ctx.guild.id, ctx.author.id
        )
        if item == 'point booster':
            user_coin1 = user_coin * 1.5
            await self.bot.db.execute(
                """
                UPDATE test.economy SET points = $1 WHERE user_id = $2 AND guild_id = $3
                """, user_coin1, ctx.author.id, ctx.guild.id
            )
            user_coin3 = await self.bot.db.fetchval(
                """
                SELECT points FROM test.economy WHERE guild_id = $1 AND user_id= $2
                """, ctx.guild.id, ctx.author.id
            )
            embed.description = f'{self.bot.right}  successfully perched point booster {emoji} **{itemname}** ' \
                                f'now your coin is increased  {user_coin} coins to {user_coin3} {self.bot.coin} coins'
            await ctx.send(embed=embed)
            return
        await self.bot.db.execute(
            """INSERT INTO test.inv(user_id,guild_id,items)
               VALUES($1,$2,$3)
               ON CONFLICT(items) DO
               NOTHING
            """,
            ctx.author.id, ctx.guild.id, itemname
        )

        embed.description = f'{self.bot.right} you successfully purchased {emoji} **{itemname}** ' \
                            f'now you have {round(user_coin1, 2)} {self.bot.coin} coins'
        await ctx.send(embed=embed)
        channel = await self.bot.db.fetchval(
            """SELECT shop_log FROM test.setup WHERE guild_id1 = $1""", ctx.guild.id
        )
        channel = self.bot.get_channel(channel)
        if channel:
            view = accept_bought(bot=self.bot, item=itemname, user=ctx.author)
            embed = discord.Embed(title='sold',
                                  description=f'{self.bot.right} {ctx.author.mention} purchased {emoji} **{itemname}**',
                                  timestamp=discord.utils.utcnow())
            await channel.send(embed=embed, view=view)

    @commands.command(name='inventory', aliases=['inv'])
    @commands.cooldown(1, 5, BucketType.user)
    async def inventory(self, ctx: Context, user: discord.Member = None):
        users = user if user else ctx.author

        inv = await self.bot.db.fetch(
            """SELECT items FROM test.inv WHERE guild_id = $1 AND user_id = $2""", users.guild.id, users.id
        )
        embed = discord.Embed()
        if len(inv) == 0 or inv == None:
            if user:
                embed.description = f'{self.bot.right} this user has no items'
                await ctx.send(embed=embed)
                return
            else:
                embed.description = f'{self.bot.right} you have  no items'
                await ctx.send(embed=embed)
                return

        o = await self.bot.db.fetch(
            """SELECT * FROM test.shop"""
        )
        shop_items = []

        for i in o:
            for j in inv:
                if i['items'] == j['items']:
                    shop_items.append(f'{i["emoji"]} **{i["items"]}** \n')
        if user:
            embed = discord.Embed(
                title='``inventory``',
                description=f'{self.bot.right} {users.mention}'
            )
        else:
            embed = discord.Embed(
                title='``inventory``'
            )
        embed.add_field(
            name=f"<:SDVitemtreasure:1008374574502658110> items",
            value=f">>> {''.join(shop_items)}")

        await ctx.send(embed=embed)


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        economy(bot))
