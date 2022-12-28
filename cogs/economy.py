from __future__ import annotations

import datetime
import zoneinfo
import logging
import time

import discord
import typing

from typing import TYPE_CHECKING

from dateutil import tz

if TYPE_CHECKING:
    from pepebot import pepebot

from discord.ext import commands
from discord.ext.commands import BucketType

from handler.view import accept_bought
from handler.Context import Context
from handler.utils import (
    send_error,
    if_user_mememanager,
    user_check_self,
    is_Meme_manager,
    string_to_delta,
    GetRelativeTime, utc2local)
from handler.errors import NotEnoughMembers, NotFound, ItemNotFound, BadRequest
from handler.economy import Economy, NotEnoughCoins, DataDoesNotExists
from handler.pagination import bal_leaderboard

# logger
log = logging.getLogger(__name__)


class Points_Leaderboard(bal_leaderboard):
    """ returns points leaderboard pages
    """

    def __init__(self,
                 entries: list, *,
                 ctx: Context,
                 per_page: int = 12,
                 title: str = None):
        converted = entries
        super().__init__(converted, per_page=per_page, ctx=ctx)


class economy(commands.Cog):
    """ economy cog class for the bot
    """
    bot: pepebot

    def __init__(self, bot: pepebot) -> None:
        self.bot = bot
        self.economy = Economy(self.bot.Database)

    @commands.command(name='add', aliases=['add_points'], description="Add points to user")
    @is_Meme_manager()
    async def add_points(self, ctx: Context, member: discord.Member, points: float = 0.1):
        """ add coins to use bank """
        ogPoints = points
        HasBooster, boost = await self.economy.HasBooster(user=member)
        if HasBooster:
            points = boost['threshold'] * points
            if points < 0:
                points = 0

        await self.economy.addUserCoins(user=member, coins=points)
        # the total points
        total = await self.economy.getUserCoins(member)
        embed = discord.Embed(
            title='``points added!``',
            description=f'>>> {self.bot.right} **user:**{member.mention} \n'
                        f'⭐ **multiplier:** {boost["threshold"] if HasBooster else "none"} \n'
                        f'{self.bot.coin} **points given:** {ogPoints}'
                        f'{" -> " + str(points) if HasBooster else ""} \n '
                        f'{self.bot.emoji.basket} **total points:** {total}'
        )
        await ctx.send(embed=embed)

    @commands.command(
        name='reset_points', aliases=['reset_coins'], description='reset the user points to given point value')
    @is_Meme_manager()
    async def reset_coins(self, ctx: Context, member: discord.Member, point: float):

        # resting points and get total coins
        total = await self.economy.setUserCoins(member, coins=point)
        embed = discord.Embed(
            description=f'>>> {self.bot.right} User points has been reset to ``{point}``,'
                        f' now user has ``{total}`` {self.bot.coin} points'
        )
        await ctx.send(embed=embed)

    @commands.command(name='remove', aliases=['remove_points', 'remove_coins'])
    async def remove_points(self, ctx: Context, member: discord.Member, points: float = 1):
        total = None
        # remove the given points to user
        try:
            total = await self.economy.removeUserCoins(user=member, coins=points)
        except NotEnoughCoins:
            embed = discord.Embed(
                description=f'{self.bot.right} this user has no points to remove')
            await ctx.send(embed=embed)
            return
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
        except NotEnoughCoins:  # catch the exception , raised when user don't have enough coins
            embed = discord.Embed(
                description=f'{self.bot.right} {NotEnoughCoins}')
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title='``transfer!``')
        embed.description = f'>>> {self.bot.right} **user:**{member.mention} \n' \
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
        except (DataDoesNotExists, NotEnoughMembers):
            embed = discord.Embed(
                title='``stats``',
                description=f'>>> {self.bot.right} user: {member.mention} \n'
                            f'{self.bot.emoji.coin} **total points:** 0 \n',
                colour=discord.Colour.blurple(), timestamp=discord.utils.utcnow())
            await ctx.send(embed=embed)
            return
        title = f'>>> {self.bot.right} user: {user.mention} ' if user else ""
        embed = discord.Embed(title='``stats``',
                              description=f""">>> {title} 
                                             {self.bot.emoji.coin} **total points:** {User_likes} 
                                             {self.bot.emoji.iconsword} **rank:#**{User_position} 
                                             {self.bot.emoji.samurai} **{user if user else ""} is top:** {top_rank} """)
        embed.colour = discord.Colour.blurple()
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', aliases=['lb'],
                      description="gets the guild point leaderboard")
    async def pointsLeaderboard(self, ctx: Context):
        """fetch the users order by maximum coins"""
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
            await ctx.error_embed(
                description='the leaderboard for this guild is currently not available')
            return

    @commands.command(name='add_item')
    @commands.is_owner()
    async def add_items(self, ctx: Context, cost: int, emoji: str, time: str = None, *,
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
        """ remove user items from the list """

        # refund the points if set to true
        forced = True if forced == 'true' else False
        try:
            await self.economy.removeUserItems(user=member, itemname=itemname, forced=forced)
        except NotFound:
            await ctx.error_embed(description="this item does not exist")
            return
        except BadRequest:
            await ctx.error_embed(
                description=f'the user already not have the item : {itemname}')
            return
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
        booster = await self.economy.GetBooster(guild_id=ctx.guild.id)
        # get the list of items
        try:
            items = await self.economy.GetShopItems()
        except:
            await ctx.error_embed(description="this guild doesnt have a shop")
            return
        shop_items = []
        # formate the list
        for i in items:
            date = i['expired'] if i['expired'] else None
            # check if item is the item is point booster
            isBooster = await self.economy.isPoint_booster(
                item_name=i["items"], guild_id=ctx.guild.id)
            shop_items.append(
                f'{i["emoji"]} **{i["items"]}**'
                f'{booster["threshold"] if isBooster else ""}'
                f'``cost``: {i["cost"]} {self.bot.coin}'
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
        """ buy an item from the shop """
        embed = discord.Embed()
        try:
            cost, emoji, total, expired, Pointsbooster, threshold = \
                await self.economy.Buyitem(user=ctx.author, item_name=item, bot=self.bot)
        except ItemNotFound:
            embed.description = f'{self.bot.right} item {item} doesnt not exists,pls check ``{self.bot.command_prefix}shop``'
            await ctx.send(embed=embed)
            return
        except BadRequest:
            embed.description = f'{self.bot.right} you cant buy more than one item'
            await ctx.send(embed=embed)
            return
        except (DataDoesNotExists, NotEnoughCoins):
            embed.description = f'{self.bot.right} you dont have enough coins to buy  {item}'
            await ctx.send(embed=embed)
            return

        future = expired + datetime.datetime.now() if expired else None
        if Pointsbooster:
            embed.description = f'{self.bot.right}  successfully purchased point booster {emoji} **{item}** ' \
                                f'now you are getting {threshold}x coins item will ' \
                                f'expire <t:{round(time.mktime(future.timetuple()))}:R>'
            await ctx.send(embed=embed)
            return
        future_time = f" item will expire <t:{round(time.mktime(future.timetuple()))}:R>" if future else ''
        embed.description = f'{self.bot.right} you successfully purchased {emoji} **{item}** ' \
                            f'now you have {total} {self.bot.coin} coins \n {future_time}'

        await ctx.send(embed=embed)

    @commands.command(name='inventory', aliases=['inv'])
    @commands.cooldown(1, 5, BucketType.user)
    async def inventory(self, ctx: Context, user: discord.Member = None):
        User = user if user else ctx.author
        embed = discord.Embed()
        try:
            inv = await self.economy.getUserItems(User, row=True)
        except DataDoesNotExists:
            if user:
                embed.description = f'{self.bot.right} this user has no items'
                await ctx.send(embed=embed)
                return
            else:
                embed.description = f'{self.bot.right} you have no items'
                await ctx.send(embed=embed)
                return

        shop_items = []
        for i in inv:
            item = await self.economy.GetItemNamed(item=i["items"])
            future: typing.Optional[datetime.datetime] = i["expired"]
            if future:
                future = utc2local(future)
            expiring = f"expire <t:{round(time.mktime(future.timetuple()))}:R>" if i["expired"] else ""
            shop_items.append(f'{item["emoji"]} **{i["items"]}** {expiring}\n')
        if user:
            embed = discord.Embed(
                title='``inventory``',
                description=f'{self.bot.right} {User.mention}'
            )
        else:
            embed = discord.Embed(
                title='``inventory``'
            )
        embed.add_field(
            name=f"<:SDVitemtreasure:1008374574502658110> items",
            value=f">>> {''.join(shop_items)}")
        await ctx.send(embed=embed)

    @commands.command(name='update_booster', description="update booster from the database")
    @commands.is_owner()
    async def update_booster(
            self, ctx: Context, cost: float, emoji: str, threshold: float, expired: str, *, name: str):
        delta = string_to_delta(expired)
        await self.economy.Insert_Booster(
            name=name, guild_id=ctx.guild.id, threshold=threshold, expired=delta)
        await self.economy.UpdateShopBooster(
            guild_id=ctx.guild.id,
            cost=cost,
            emoji=emoji
        )
        await ctx.send("done")

    @commands.command(name='insert_booster', description="update booster from the database")
    @commands.is_owner()
    async def insert_booster(self, ctx: Context, name: str, expired: str, threshold: float):
        delta = string_to_delta(expired)
        await self.economy.Insert_Booster(name=name.lower(), guild_id=ctx.guild.id, threshold=threshold, expired=delta)
        await ctx.send('done')

    @commands.command(name='addBooster', description="add booster to the shop")
    @commands.is_owner()
    async def addBooster(self, ctx: Context, cost: int, emoji: str = "⭐"):
        try:
            await self.economy.UpdateShopBooster(
                guild_id=ctx.guild.id,
                cost=cost,
                emoji=emoji)
        except NotFound:
            await ctx.error_embed(description="booster not available for the guild")
        await ctx.send("done")


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        economy(bot))
