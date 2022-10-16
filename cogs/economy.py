from __future__ import annotations

import time
import typing
from typing import TYPE_CHECKING
import logging
import discord

from handler.Context import Context
from handler.errors import NotEnoughMembers, NotFound, ItemNotFound, BadRequest
from handler.pagination import bal_leaderboard
from handler.view import accept_bought
from pepebot import pepebot
from discord.ext import commands
from discord.ext.commands import BucketType
from handler.utils import (
    send_error,
    if_user_mememanager,
    user_check_self,
    is_Meme_manager,
    string_to_delta,
    GetRelativeTime
)
from handler.economy import (
    Economy,
    UserHasNotEnoughCoins,
    DataDoesNotExists
)

log = logging.getLogger(__name__)


class Points_Leaderboard(bal_leaderboard):
    """ returns points leaderboard pages
    """
    def __init__(self, entries: list, *, ctx: Context, per_page: int = 12, title: str = None):
        converted = entries
        print(entries)
        super().__init__(converted, per_page=per_page, ctx=ctx)

def mycheck():  # Creating the check
    async def startCheck(ctx: Context):
        return ctx.author.id == ctx.guild.owner.id or ctx.author.id == 888058231094665266
    return commands.check(startCheck)


class economy(commands.Cog):
    """economy cog class for the bot"""
    bot: pepebot

    def __init__(self, bot: pepebot) -> None:
        self.bot = bot
        self.economy = Economy(self.bot.Database)

    @commands.command(name="do")
    async def dosomething(self, ctx: Context, item_name: str):
        await ctx.send(self.bot.glas)

    @commands.command(name='add', aliases=['add_points'], description="Add points to user")
    @is_Meme_manager()
    async def add_points(self, ctx: Context, member: discord.Member, points: float = 0.1):
        # add coins to user bank column
        await self.economy.addUserCoins(user=member, coins=points)
        # the total points
        total = await self.economy.getUserCoins(member)
        embed = discord.Embed(
            title='``points added!``',
            description=f'>>> {self.bot.right} **user:**{member.mention} \n'
                        f'{self.bot.coin} **points given:** {points} \n'
                        f'{self.bot.emoji.basket} **total points:** {total}'
        )
        await ctx.send(embed=embed)

    @commands.command(
        name='reset_points', aliases=['reset_coins'], description='reset the user points to given value')
    @is_Meme_manager()
    async def reset_coins(self, ctx: Context, member: discord.Member, point: float):

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

        # gets total user coins
        total = await self.economy.getUserCoins(user=member)
        if not total:
            embed = discord.Embed(
                description=f'{self.bot.right} this user has no points to remove')
            await ctx.send(embed=embed)
            return
        # remove the given points to user
        total = await self.economy.removeUserCoins(user=member, coins=points)
        embed = discord.Embed(
            title='``points removed!``',
            description=f'>>> {self.bot.right} **user:**{member.mention} \n'
                        f'{self.bot.emoji.coin} **points removed:** {points} \n'
                        f'{self.bot.emoji.basket} **total points:** {total}'
        )
        await ctx.send(embed=embed)

    @commands.command(name='reset', description="set the user coins to 0")
    @is_Meme_manager()
    async def reset_points(self, ctx: Context, member: discord.Member):
        total = await self.economy.getUserCoins(user=member)
        if not total:
            embed = discord.Embed(
                description=f'{self.bot.right} this user already has 0 points')
            await ctx.send(embed=embed)
            return

        # set user coins to 0
        total = await self.economy.setUserCoins(user=member)
        embed = discord.Embed(title='``points reset!``')
        embed.description = f'>>> {self.bot.right} **user:**{member.mention} \n' \
                            f'{self.bot.emoji.coin} **points removed:** all \n' \
                            f'{self.bot.emoji.basket} **total points:** {total}'
        await ctx.send(embed=embed)

    @commands.command(name='give', aliases=['transfer'], description="give user points to other user")
    @commands.cooldown(1, 5, BucketType.user)
    async def give_points(self, ctx: Context, member: discord.Member, points: float):

        try:
            # fetch total member and command user coins
            total_member, total_author = await self.economy.GivePoints(
                author=ctx.author,
                user=member,
                coins=abs(points))
        except UserHasNotEnoughCoins:  # catch the exception , raised when user don't have enough coins
            embed = discord.Embed(
                description=f'{self.bot.right} you dont enough points to give')
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title='``transfer!``')
        embed.description=f'>>> {self.bot.right} **user:**{member.mention} \n' \
                        f'{self.bot.emoji.coin} **coins given:** {points} \n' \
                        f'{self.bot.emoji.basket} **total points:** {total_member}\n' \
                        f'{self.bot.right} now you have {total_author} {self.bot.coin}'
        await ctx.send(embed=embed)

    @commands.command(name='balance', aliases=['bal', 'points'], description="get user balance and stats")
    @commands.cooldown(1, 3, BucketType.member)
    async def balance(self, ctx: Context, user: discord.Member = None):

        member = user if user else ctx.author
        # get the stats parameters
        try:
            top_rank, User_position, User_likes = await self.economy.getUser_stats(member)
        except DataDoesNotExists or NotEnoughMembers:
            embed = discord.Embed(
                title='``stats``',
                description=f'>>> {self.bot.right} user: {member.mention} \n'
                            f'{self.bot.emoji.coin} **total points:** 0 \n',
                colour=discord.Colour.blurple(), timestamp=discord.utils.utcnow())
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(title='``stats``')
        embed.colour = discord.Colour.blurple()
        embed.timestamp = discord.utils.utcnow()
        embed.description=f'>>> {self.bot.right} user: {user.mention} \n' if user else "" \
                        f'{self.bot.emoji.coin} **total points:** {User_likes} \n' \
                        f'{self.bot.emoji.iconsword} **rank:#**{User_position} \n' \
                        f'{self.bot.emoji.samurai} **{user if user else ""} is top:** {top_rank} ',
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', aliases=['lb'],
                      description="gets the guild point leaderboard")
    async def pointsLeaderboard(self, ctx: Context):
        UserList = await self.economy.getAll_users(
            ctx.guild.id,
            Filter="""order by points desc
            fetch first 100 rows only"""
        )
        if len(UserList) == 0:
            await ctx.error_embed(
                description='the leaderboard for this guild is currently not available')
            return

        users = []
        for i in UserList:
            user = ctx.guild.get_member(i['user_id'])
            if user:
                users.append([user, round(i['points'], 2)])
        if users:
            warnings = Points_Leaderboard(
                entries=users, per_page=10, ctx=ctx,
                title=f'``Leaderboard for {ctx.guild.name} : ``{len(users)}``')
            await warnings.start()
        else:
            await ctx.error_embed (
                description='the leaderboard for this guild is currently not available')
            return

    @commands.command(name='add_item')
    @commands.is_owner()
    async def add_items(self, ctx: Context,cost: int, emoji: str, time: str = None, *,
                        name: str):
        """ add items to the shop database column"""
        delta = string_to_delta(time) if time != '0' else None
        await self.economy.addShopItem(
            name=name, cost=cost, emoji=emoji,
            seconds=delta.total_seconds() if delta else None)
        await ctx.send('item added to the shop')

    @commands.command(name='remove_user_item')
    @is_Meme_manager()
    async def remove_user_item(
            self, ctx: Context, member: discord.Member, forced: typing.Literal['true', 'false'] = 'true', *,
            itemname: str):
        """remove user items from the list"""
        # refund the points if set to true
        forced = True if forced == 'true' else False
        try:
            await self.economy.GetItemNamed(item=itemname)
        except NotFound:
            await ctx.error_embed(description="this item not exists")
        try:
            await self.economy.getUserItem(itemname=itemname, user=member)
        except NotFound:
            await ctx.error_embed(
                description=f'the user already not have the item : {itemname}')

        await self.economy.removeUserItems(user=member, itemname=itemname, forced=forced)
        await ctx.send(embed=discord.Embed(
            description=f'>>> item {itemname} removed from {member.mention},'
                        f'{"** the points refunded **" if not forced else ""}'))

    # removes an item from the shop
    @commands.command(name='remove_item', description="removes the item from the list")
    @commands.is_owner()
    async def ShopRemove(self, ctx: Context, *, name: str):
        try:
            await self.economy.removeShopItems(name)
        except NotFound:
            await ctx.send(
                embed=discord.Embed(description="the item already not in list"))
            return
        await ctx.error_embed(description='item removed')

    # show shop items
    @commands.command(name='shop')
    @commands.cooldown(1, 5, BucketType.member)
    async def shop(self, ctx: Context):
        # get the list of items
        items = await self.economy.GetShopItems()
        shop_items = []

        # formate the list
        for i in items:
            date = i['expired'] if i['expired'] else None
            shop_items.append(
                f'{i["emoji"]} **{i["items"]}** ``cost``: {i["cost"]} {self.bot.coin} '
                f'{f"expires after {GetRelativeTime(date)}" if i["expired"] else ""} \n')
        embed = discord.Embed(
            title='``shop``')
        embed.add_field(
            name=f"{self.bot.emoji.treasure} items",
            value=f">>> {''.join(shop_items)}")
        await ctx.send(embed=embed)

    @commands.command(name='buy')
    @commands.cooldown(1, 5, BucketType.member)
    async def buy(self, ctx: Context, *, item: str):

        embed = discord.Embed()
        try:
            cost, emoji, total, expired, Pointsbooster, threshold = \
                await self.economy.Buyitem(user=ctx.author,item_name=item,bot=self.bot)
        except ItemNotFound:
            embed.description = f'{self.bot.right} item {item} doesnt not exists,pls check ``$shop``'
            await ctx.send(embed=embed)
            return
        except BadRequest:
            embed.description = f'{self.bot.right} you cant buy more than one item'
            await ctx.send(embed=embed)
            return
        except (DataDoesNotExists,UserHasNotEnoughCoins):
            embed.description = f'{self.bot.right} you dont have enough coins to buy  {item}'
            await ctx.send(embed=embed)
            return

        if Pointsbooster:
            embed.description = f'{self.bot.right}  successfully purchased point booster {emoji} **{item}** ' \
                            f'now you are getting {threshold}x coins item will expire 1 min'
            await ctx.send(embed=embed)
            return
        embed.description = f'{self.bot.right} you successfully purchased {emoji} **{item}** ' \
                            f'now you have {total} {self.bot.coin} coins'
        await ctx.send(embed=embed)

        # channel = await self.bot.db.fetchval(
        #     """SELECT shop_log FROM test.setup WHERE guild_id1 = $1""", ctx.guild.id
        # )
        # channel = self.bot.get_channel(channel)
        # if channel:
        #     view = accept_bought(bot=self.bot, item=itemname, user=ctx.author)
        #     embed = discord.Embed(title='sold',
        #                           description=f'{self.bot.right} {ctx.author.mention} purchased {emoji} **{itemname}**',
        #                           timestamp=discord.utils.utcnow())
        #     await channel.send(embed=embed, view=view)

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
