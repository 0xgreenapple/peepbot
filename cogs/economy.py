from __future__ import annotations

import datetime
import logging
import time
import discord
from discord.ext import commands
from discord.ext.commands import BucketType
import typing
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from pepebot import pepebot

from handler.Context import Context
from handler.utils import (
    send_error,
    if_user_mememanager,
    is_guild_owner,
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
        self.economy = Economy(Bot=bot)

    @is_Meme_manager()
    @commands.command(name='add', aliases=['add_points'])
    async def add_points(
            self, ctx: Context, member: discord.Member, points: float = 0.1):
        """ add given points to user inventory """

        ogPoints = points
        # check is a user has booster item in their inventory or not
        # HasBooster: boolean value, true if user has booster
        # boost: return the booster data, for example name, cost
        HasBooster, boost = await self.economy.HasBooster(user=member)
        if HasBooster:
            points = boost['threshold'] * points
            if points < 0:
                points = 0
        try:
            total_points = await self.economy.addUserPoints(
                user=member, points=points)
        except BadRequest as error:
            # raised if given negative value
            await ctx.error_embed(
                title="BadRequest", description=error.message)
            return

        embed = discord.Embed(title='``points added!``')
        embed.description = f"""
        >>> {self.bot.right} **user:**{member.mention} 
            ⭐ **multiplier:** {boost["threshold"] if HasBooster else "none"} 
            {self.bot.coin} **points given:** {ogPoints}
            {" -> " + str(points) if HasBooster else ""} \
            {self.bot.emoji.basket} **total points:** {total_points} """
        await ctx.send(embed=embed)

    @is_Meme_manager()
    @commands.command(name='set_points', aliases=['set_coins', 'set'])
    async def set_coins(
            self, ctx: Context, member: discord.Member, point: float):
        """set user points to given points"""
        if point < 0:
            await ctx.error_embed(description="points must be greater than zero or zero")
            return
        total = await self.economy.setUserPoints(member, points=point)
        embed = discord.Embed()
        embed.description = f"""
            >>> {self.bot.right} User points has been set to
            ``{total}`` {self.bot.emoji.coin}"""
        await ctx.send(embed=embed)

    @is_Meme_manager()
    @commands.command(name='remove', aliases=['remove_points', 'remove_coins'])
    async def remove_points(
            self, ctx: Context, member: discord.Member, points: float = 1):
        """ remove given points to user inventory """
        embed = discord.Embed()
        try:
            total = await self.economy.removeUserPoints(
                user=member, points=points)
        except NotEnoughCoins:
            embed.description = f'{self.bot.right} this user has no points to remove'
            await ctx.send(embed=embed)
            return

        embed.title = '``points removed!``'
        embed.description = f"""
        >>> {self.bot.right} **user:**{member.mention} 
            {self.bot.emoji.coin} **points removed:** {points} 
            {self.bot.emoji.basket} **total points:** {total}"""
        await ctx.send(embed=embed)

    @is_Meme_manager()
    @commands.command(name='reset', aliases=["reset_points"])
    async def reset_points(self, ctx: Context, member: discord.Member):
        """ reset user points to zero """
        # set user coins to 0
        total = await self.economy.setUserPoints(user=member)
        embed = discord.Embed(title='``points reset!``')
        embed.description = f"""
        >>> {self.bot.right} **user:**{member.mention} 
            {self.bot.emoji.coin} **points removed:** all 
            {self.bot.emoji.basket} **total points:** {total} """
        await ctx.send(embed=embed)

    @commands.cooldown(1, 5, BucketType.user)
    @commands.command(name='give', aliases=['transfer'])
    async def give_points(self, ctx: Context, member: discord.Member, points: float):
        """ give your inventory points to another user """
        if points < 0:
            points = 0
        try:
            total_member_coins, total_author_coins = await self.economy.GivePoints(
                author=ctx.author, user=member, points=abs(points))
        except NotEnoughCoins as error:
            await ctx.error_embed(description=error.message)
            return
        except BadRequest as error:
            await ctx.error_embed(description=error.message)
            return

        embed = discord.Embed(title='``transfer!``')
        embed.description = f"""
        >>> {self.bot.right} **user:**{member.mention} 
            {self.bot.emoji.coin} **coins given:** {points} 
            {self.bot.emoji.basket} **total points:** {total_member_coins}
            {self.bot.right} now you have {total_author_coins} {self.bot.coin}"""
        await ctx.send(embed=embed)

    @commands.cooldown(1, 3, BucketType.member)
    @commands.command(name='balance', aliases=['bal', 'points'])
    async def balance(self, ctx: Context, user: discord.Member = None):
        """ check inventory points and user stats in the guild """
        member = user if user else ctx.author
        embed = discord.Embed(
            title='``stats``', colour=discord.Colour.blurple(),
            timestamp=discord.utils.utcnow())

        # get the stats parameters
        try:
            top_rank, User_position, User_points = await self.economy.getUser_stats(member)
        except (DataDoesNotExists, NotEnoughMembers):
            embed.description = \
                f'>>> {self.bot.right} user: {member.mention} \n' \
                f'{self.bot.emoji.coin} **total points:** 0'
            await ctx.send(embed=embed)
            return

        embed.title = f'>>> {self.bot.right} user: {user.mention} ' if user else "``balance``"
        embed.description = f"""
        >>>  {self.bot.emoji.coin} **total points:** {User_points} 
             {self.bot.emoji.iconsword} **rank:#**{User_position} 
             {self.bot.emoji.samurai} **{user if user else ""} is top:** {top_rank}
        """
        embed.colour = discord.Colour.blurple()
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', aliases=['lb'])
    async def pointsLeaderboard(self, ctx: Context):
        """ fetch the users order by maximum coins """
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
        # fetches all members by id that was returned to the list
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

    @is_guild_owner()
    @commands.command(name='add_item')
    async def add_items(
            self, ctx: Context, cost: float, emoji: str, expiration_time: str = None,
            *, name: str):
        """ add a new item to shop
            :param name: what's the new item will be called
            :param cost: the cost of new item
            :param emoji: the emoji that will present the item
            :param expiration_time: expiration date of new item
        """
        if cost < 0:
            await ctx.error_embed(description="cost must be greater than 0")
            return
        delta = string_to_delta(expiration_time) if expiration_time != '0' else None
        await self.economy.addShopItem(
            guild_id=ctx.guild.id, name=name.lower(),
            cost=cost, emoji=emoji,
            seconds=delta.total_seconds() if delta else None)
        embed = discord.Embed(title="``item added!``")

        embed.description = f"""
        >>> {self.bot.emoji.right} **item name** : {name} 
            **cost**: ``{cost}`` 
            {self.bot.emoji.right} **emoji**: {emoji}
            {f"**expires in**: {GetRelativeTime(delta)}" if delta else ""}"""
        await ctx.send(embed=embed)

    @is_Meme_manager()
    @commands.command(name='remove_user_item')
    async def remove_user_item(
            self, ctx: Context, member: discord.Member,
            forced: Literal['true', 'false'] = 'true', *, item_name: str):
        """ remove given item to user inventory
            :param forced: whether you want to refund coins or not
        """
        forced = True if forced == 'true' else False
        try:
            await self.economy.removeUserItems(
                user=member, item_name=item_name, forced=forced)
        except NotFound:
            await ctx.error_embed(
                description="this item does not exist")
            return
        except BadRequest:
            await ctx.error_embed(
                description=f'the user already not have the item : {item_name}')
            return
        embed = discord.Embed()
        embed.description = f"""
            >>> item {item_name} removed from {member.mention}
            {"** the points refunded **" if not forced else ""}"""
        await ctx.send(embed=embed)

    # removes an item from the shop
    @commands.command(name='remove_item')
    @commands.is_owner()
    async def ShopRemove(self, ctx: Context, *, item_name: str):
        """ remove given item from the shop """
        try:
            await self.economy.removeShopItems(
                guild_id=ctx.guild.id, item_name=item_name)
        except NotFound:
            await ctx.send(
                embed=discord.Embed(description="the item already not in list"))
            return
        embed = discord.Embed()
        embed.description = f">>> {self.bot.right} " \
                            f"item `{item_name}` removed from the shop"
        await ctx.send(embed=embed)

    # show shop items
    @commands.command(name='shop')
    @commands.cooldown(1, 5, BucketType.member)
    async def shop(self, ctx: Context):
        """ show the list of item that shop"""

        booster = await self.economy.GetBooster(guild_id=ctx.guild.id)
        # get the list of items
        try:
            items = await self.economy.GetShopItems(guild_id=ctx.guild.id)
        except:
            await ctx.error_embed(description="this guild doesnt have a shop")
            return
        shop_items = []
        # formate the list
        for item in items:
            date = item['expired'] if item['expired'] else None
            # check if item is the item is point booster
            isBooster = await self.economy.isPoint_booster(
                item_name=item["items"], guild_id=ctx.guild.id)
            booster_message = f'{" threshold :" + str(booster["threshold"]) + "x" if isBooster else ""}'
            shop_items.append(
                f'{item["emoji"]} **{item["items"]}**'
                f'{booster_message}'
                f'``cost``: {item["cost"]} {self.bot.coin}'
                f'{f"expires after {GetRelativeTime(date)}" if item["expired"] else ""}')
        if shop_items is None or len(shop_items) == 0:
            await ctx.error_embed(description="there is no items in the shop!")
            return
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
            cost, emoji, total, expired, Point_booster, threshold = \
                await self.economy.BuyItem(user=ctx.author, item_name=item, bot=self.bot)
        except ItemNotFound:
            embed.description = f'{self.bot.right} item {item} doesnt not exists' \
                                f',pls check ``{self.bot.command_prefix}shop``'
            await ctx.send(embed=embed)
            return
        except BadRequest:
            embed.description = f'{self.bot.right} you cant buy more than one item'
            await ctx.send(embed=embed)
            return
        except (DataDoesNotExists, NotEnoughCoins):
            embed.description = f'{self.bot.right} ' \
                                f'you dont have enough coins to buy {item}'
            await ctx.send(embed=embed)
            return

        future = expired + datetime.datetime.now() if expired else None
        if Point_booster:
            embed.description = f"""
                {self.bot.right}  successfully purchased point booster {emoji} **{item}** 
                now you will get {threshold}x coins item will 
                expire <t:{round(time.mktime(future.timetuple()))}:R>"""
            await ctx.send(embed=embed)
            return
        future_time = f"item will expire <t:{round(time.mktime(future.timetuple()))}:R>" if future else ''
        embed.description = f'{self.bot.right} you successfully purchased {emoji} **{item}** ' \
                            f'now you have {total} {self.bot.coin} coins \n {future_time}'
        await ctx.send(embed=embed)

    @commands.command(name='inventory', aliases=['inv'])
    @commands.cooldown(1, 5, BucketType.user)
    async def inventory(self, ctx: Context, user: discord.Member = None):
        """ show the all items available in user inventory """
        User = user if user else ctx.author
        embed = discord.Embed()
        try:
            inv = await self.economy.getUserItems(User, row=True)
        except DataDoesNotExists:
            embed.description = f'{self.bot.right} ' \
                                f'{"this user has" if user else "you have "}' \
                                f' no items'
            await ctx.send(embed=embed)
            return

        shop_items = []
        for i in inv:
            item = await self.economy.GetItemNamed(item=i["items"], guild_id=ctx.guild.id)
            future: typing.Optional[datetime.datetime] = i["expired"]
            if future:
                future = utc2local(future)
            expiring = f"expire <t:{round(time.mktime(future.timetuple()))}:R>" if i["expired"] else ""
            shop_items.append(f'{item["emoji"]} **{i["items"]}** {expiring}\n')

        embed.title = '``inventory``'
        embed.description = f'{self.bot.right} {User.mention}' if user else None
        embed.add_field(
            name=f"{self.bot.emoji.treasure} items",
            value=f">>> {''.join(shop_items)}")
        await ctx.send(embed=embed)

    @commands.command(name='add_booster')
    @is_guild_owner()
    async def addBooster(self, ctx: Context, threshold: float, *, item_name: str):
        """ add booster to guild """
        try:
            Booster = await self.economy.Insert_Booster(
                name=item_name, threshold=threshold, guild_id=ctx.guild.id)
        except BadRequest as error:
            await ctx.error_embed(description=error.message)
            return
        except ItemNotFound as error:
            await ctx.error_embed(description=error.message)
            return
        embed = discord.Embed()
        embed.title = "``booster added!``"
        expired_on = GetRelativeTime(Booster["expired"])
        embed.description = f"""
            >>> {self.bot.right} **name**: {Booster["item_name"]}
            **threshold**: ``{Booster["threshold"]}``
            **expires**: ``{expired_on}``
            """
        await ctx.send(embed=embed)

    @commands.command(name="remove_booster")
    @is_guild_owner()
    async def remove_booster(self, ctx: Context):
        """remove booster item from the guild"""
        try:
            await self.economy.delete_Booster(guild_id=ctx.guild.id)
        except NotFound:
            await ctx.error_embed(description="the booster already no exist")

        embed = discord.Embed(title="``booster removed!``")
        embed.description("the booster item has been removed successfully")
        await ctx.send(embed=embed)

async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        economy(bot))
