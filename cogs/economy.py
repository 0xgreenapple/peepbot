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
    from pepebot import PepeBot

from handler.context import Context
from handler.utils import (
    send_error,
    is_user_mememanager,
    is_guild_owner,
    user_check_self,
    is_meme_manager,
    string_to_delta,
    get_relative_time, utc_to_local,
    Emojis)
from handler.errors import NotEnoughMembers, NotFound, ItemNotFound, BadRequest
from handler.economy import Economy, NotEnoughCoins, DataDoesNotExists
from handler.pagination import SimpleEmbedPages, EmbedFormatter

# logger
log = logging.getLogger("pepebot")


class PointsLeaderboard(EmbedFormatter):
    def __init__(self, title: str, bot: PepeBot, ctx: Context):
        super().__init__(
            name=title)
        self.bot = bot
        self.ctx = ctx

    def formate_lines(self, current_index: int, value) -> str:
        formate = (f"{current_index}. "
                   f"{value[0]} {Emojis.coin}"
                   f" **points**: {value[1]}")
        return formate


class economy(commands.Cog):
    """ economy cog class for the bot
    """
    bot: PepeBot

    def __init__(self, bot: PepeBot) -> None:
        self.bot = bot
        self.economy = Economy(bot=bot)

    async def cog_check(self, ctx: Context):
        return await self.economy.is_turned_on(ctx.guild.id)

    @is_meme_manager()
    @commands.command(name='add', aliases=['add_points'])
    async def add_points(
            self, ctx: Context, member: discord.Member, points: float = 0.1):
        """ add given points to user inventory """

        og_points = points
        # check is a user has booster item in their inventory or not
        # HasBooster: boolean value, true if user has booster
        # boost: return the booster data, for example name, cost
        has_booster, booster_item = await self.economy.has_booster(user=member)
        if has_booster:
            points = booster_item['threshold'] * points
            if points < 0:
                points = 0
        try:
            total_points = await self.economy.add_user_points(
                user=member, points=points)
        except BadRequest as error:
            # raised if given negative value
            await ctx.error_embed(
                title="BadRequest", description=error.message)
            return

        embed = discord.Embed(title='``points added!``')
        embed.description = f"""
        >>> {self.bot.right} **user:**{member.mention} 
            ⭐ **multiplier:** {booster_item["threshold"] 
            if has_booster else "none"} 
            {self.bot.coin} **points given:** {og_points}
            {" -> " + str(points) if has_booster else ""} \
            {self.bot.emoji.basket} **total points:** {total_points} """
        await ctx.send(embed=embed)

    @is_meme_manager()
    @commands.command(name='set_points', aliases=['set_coins', 'set'])
    async def set_coins(
            self, ctx: Context, member: discord.Member, point: float):
        """set user points to given points"""
        if point < 0:
            await ctx.error_embed(
                description="points must be greater than zero or zero")
            return
        total = await self.economy.set_user_points(member, points=point)
        embed = discord.Embed()
        embed.description = f"""
            >>> {self.bot.right} User points has been set to
            ``{total}`` {self.bot.emoji.coin}"""
        await ctx.send(embed=embed)

    @is_meme_manager()
    @commands.command(name='remove', aliases=['remove_points', 'remove_coins'])
    async def remove_points(
        self, ctx: Context, member: discord.Member, points: float = 1
    ):

        """ remove given points to user inventory """
        embed = discord.Embed()
        try:
            total_coins = await self.economy.remove_user_points(
                user=member, points=points)
        except NotEnoughCoins:
            embed.description = (
                f'{self.bot.right} this user has no points to remove')
            await ctx.send(embed=embed)
            return

        embed.title = '``points removed!``'
        embed.description = f"""
        >>> {self.bot.right} **user:**{member.mention} 
            {self.bot.emoji.coin} **points removed:** {points} 
            {self.bot.emoji.basket} **total points:** {total_coins}"""
        await ctx.send(embed=embed)

    @is_meme_manager()
    @commands.command(name='reset', aliases=["reset_points"])
    async def reset_points(self, ctx: Context, member: discord.Member):
        """ reset user points to zero """
        # set user coins to 0
        await self.economy.set_user_points(user=member)
        embed = discord.Embed(title='``points reset!``')
        embed.description = f"""
        >>> {self.bot.right} **user:**{member.mention} 
            {self.bot.emoji.coin} **points removed:** all 
            {self.bot.emoji.basket} **total points:** 0"""
        await ctx.send(embed=embed)

    @commands.cooldown(1, 5, BucketType.user)
    @commands.command(name='give', aliases=['transfer'])
    async def give_points(
        self, ctx: Context, member: discord.Member, points: float
    ):
        """ give your inventory points to another user """
        if points < 0:
            points = 0
        try:
            (total_member_coins,
             total_author_coins) = await self.economy.give_points(
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
            {self.bot.right} now you have {total_author_coins} {self.bot.coin}
        """
        await ctx.send(embed=embed)

    @commands.cooldown(1, 3, BucketType.member)
    @commands.command(name='balance', aliases=['bal', 'points'])
    async def balance(self, ctx: Context, user: discord.Member = None):
        """ check inventory points and user stats in the guild """
        member = user if user is not None else ctx.author
        embed = discord.Embed(
            title='``stats``', colour=discord.Colour.blurple(),
            timestamp=discord.utils.utcnow())

        # get the stats parameters
        try:
            (top_rank,
             user_position,
             user_points) = await self.economy.get_user_stats(member)
        except (DataDoesNotExists, NotEnoughMembers):
            embed.description = (
                f'>>> {self.bot.right} user: {member.mention} \n' 
                f'{self.bot.emoji.coin} **total points:** 0')
            await ctx.send(embed=embed)
            return
        message = f"{self.bot.right} user: {member.mention} \n"
        if user is None:
            message = ""
        embed.description = f"""
        >>>  {message}{self.bot.emoji.coin} **total points:** {user_points} 
             {self.bot.emoji.iconsword} **rank:#**{user_position} 
             {self.bot.emoji.samurai} **{user if user else ""} is top:** {top_rank}
        """
        if not user:
            embed.title = "``balance``"
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', aliases=['lb'])
    async def points_leaderboard(self, ctx: Context):
        """ fetch the users order by maximum coins """
        user_list = await self.economy.get_all_users(
            ctx.guild.id,
            filter_by="""order by points desc
            fetch first 100 rows only"""
        )
        if len(user_list) == 0:
            await ctx.error_embed(
                description='the leaderboard for this '
                            'guild is currently not available')
            return

        users = []
        # fetches all members by id that was returned to the list
        for i in user_list:
            user = ctx.guild.get_member(i['user_id'])
            if user:
                users.append([user, round(i['points'], 2)])
        if len(users) != 0:
            embed_formatter = PointsLeaderboard(
                bot=self.bot, ctx=ctx,
                title=f'Leaderboard for {ctx.guild.name} : ``{len(users)}``'
            )
            points_leaderboard_pages = SimpleEmbedPages(
                bot=self.bot, ctx=ctx, formatter=embed_formatter, data=users,
                max_per_page=10, timeout=datetime.timedelta(minutes=10)
            )
            await points_leaderboard_pages.send()
        else:
            await ctx.error_embed(
                description='the leaderboard for this guild '
                            'is currently not available')
            return

    @is_guild_owner()
    @commands.command(name='add_item')
    async def add_items(
        self, ctx: Context, cost: float, emoji: str,
        expiration_time: str = None, *, name: str
    ):
        """add a new item to shop.

        Parameters
        ----------
        name:
            what's the new item will be called
        cost:
            the cost of new item
        emoji:
            the emoji that will present the item
        expiration_time:
            expiration date of new item
        """
        if cost < 0:
            await ctx.error_embed(description="cost must be greater than 0")
            return
        delta = None
        if expiration_time != '0':
            delta = string_to_delta(expiration_time)
        await self.economy.add_shop_item(
            guild_id=ctx.guild.id, name=name.lower(),
            cost=cost, emoji=emoji,
            seconds=delta.total_seconds() if delta else None
        )
        embed = discord.Embed(title="``item added!``")
        embed.description = f"""
        >>> {self.bot.emoji.right} **item name** : {name} 
            **cost**: ``{cost}`` 
            {self.bot.emoji.right} **emoji**: {emoji}
            {f"**expires in**: {get_relative_time(delta)}" if delta else ""}"""
        await ctx.send(embed=embed)

    @is_meme_manager()
    @commands.command(name='remove_user_item')
    async def remove_user_item(
            self, ctx: Context, member: discord.Member,
            forced: Literal['true', 'false'] = 'true', *, item_name: str):
        """ remove given item to user inventory
            :param forced: whether you want to refund coins or not
        """
        forced = True if forced == 'true' else False
        try:
            await self.economy.remove_user_items(
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
    @is_guild_owner()
    async def shop_remove(self, ctx: Context, *, item_name: str):
        """ remove given item from the shop """
        try:
            await self.economy.remove_shop_items(
                guild_id=ctx.guild.id, item_name=item_name)
        except NotFound:
            await ctx.error_embed(description="the item already not in list")
            return

        embed = discord.Embed()
        embed.description = (
            f">>> {self.bot.right} item `{item_name}` removed from the shop")
        await ctx.send(embed=embed)

    # show shop items
    @commands.command(name='shop')
    @commands.cooldown(1, 5, BucketType.member)
    async def shop(self, ctx: Context):
        """ show the list of item that shop"""

        booster = await self.economy.get_booster(guild_id=ctx.guild.id)
        # get the list of items
        try:
            items = await self.economy.get_shop_items(guild_id=ctx.guild.id)
        except NotFound:
            await ctx.error_embed(description="this guild doesnt have a shop")
            return
        shop_items = []
        # formate the list
        for item in items:
            # check if item is the item is point booster
            is_booster = await self.economy.is_point_booster(
                item_name=item["items"], guild_id=ctx.guild.id)

            threshold = None
            if is_booster:
                threshold = booster["threshold"]
            booster_message = f" threshold: {threshold}X"

            expiry_time = item["expired"]
            relative_time = None

            if expiry_time is not None:
                relative_time = get_relative_time(expiry_time)
            expiry_message = f"expires after {relative_time}"
            if relative_time is None:
                expiry_message = ""

            shop_items.append(
                f'{item["emoji"]} **{item["items"]}**'
                f'{booster_message if is_booster else ""}'
                f'``cost``: {item["cost"]} {self.bot.coin}'
                f'{expiry_message}\n'
            )
        if shop_items is None or len(shop_items) == 0:
            await ctx.error_embed(
                description="there is no items in the shop!")
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
            purchased_data = await self.economy.buy_item(
                user=ctx.author, item_name=item, bot=self.bot)
        except ItemNotFound:
            embed.description = (
                f'{self.bot.right} item {item} doesnt not exists' 
                f',pls check ``{await self.bot.get_prefix(ctx.message)}shop``')
            await ctx.send(embed=embed)
            return
        except BadRequest:
            embed.description = (
                f'{self.bot.right} you cant buy more than one item')
            await ctx.send(embed=embed)
            return
        except (DataDoesNotExists, NotEnoughCoins):
            embed.description = f'{self.bot.right} ' \
                                f'you dont have enough coins to buy {item}'
            await ctx.send(embed=embed)
            return

        expired = purchased_data["expire_time"]
        point_booster = purchased_data["is_booster_item"]
        threshold = purchased_data["threshold"]
        total = purchased_data["total"]
        item_emoji = purchased_data["emoji"]
        future = expired + datetime.datetime.now() if expired else None

        if point_booster:
            embed.description = (
                f"{self.bot.right} successfully purchased point booster "
                f"{item_emoji} **{item}** "
                f"now you will get {threshold}x coins item will "
                f"expire <t:{round(time.mktime(future.timetuple()))}:R")
            await ctx.send(embed=embed)
            return

        future_time_message = ''
        if future is not None:
            future_time_message = (
                f"item will expire {discord.utils.format_dt(future,style='R')}"
            )

        embed.description = (
            f'{self.bot.right} you successfully purchased {item_emoji} '
            f'**{item}** ' 
            f'now you have {total} '
            f'{self.bot.coin} coins \n {future_time_message}'
        )
        await ctx.send(embed=embed)

    @commands.command(name='inventory', aliases=['inv'])
    @commands.cooldown(1, 5, BucketType.user)
    async def inventory(self, ctx: Context, user: discord.Member = None):
        """ show the all items available in user inventory """
        User = user if user else ctx.author
        embed = discord.Embed()
        try:
            inv = await self.economy.get_user_items(User, row=True)
        except DataDoesNotExists:
            embed.description = (
                f'{self.bot.right} ' 
                f'{"this user has" if user else "you have "}' 
                f' no items')
            await ctx.send(embed=embed)
            return

        shop_items = []
        for i in inv:
            item = await self.economy.get_item_named(
                item_name=i["items"], guild_id=ctx.guild.id)
            timestamp = ""
            expiring = ""
            if i["expired"] is not None:
                timestamp = discord.utils.format_dt(
                    utc_to_local(i['expired']),
                    style="R"
                )
                expiring = f"expire {timestamp}"
            shop_items.append(f'{item["emoji"]} **{i["items"]}** {expiring}\n')

        embed.title = '``inventory``'
        embed.description = f'{self.bot.right} {User.mention}' if user else None
        embed.add_field(
            name=f"{self.bot.emoji.treasure} items",
            value=f">>> {''.join(shop_items)}")
        await ctx.send(embed=embed)

    @commands.command(name='add_booster')
    @is_guild_owner()
    async def add_booster(
        self, ctx: Context, threshold: float, *, item_name: str
    ):

        """ add booster to guild """
        try:
            booster = await self.economy.insert_Booster(
                name=item_name, threshold=threshold, guild_id=ctx.guild.id)
        except BadRequest as error:
            await ctx.error_embed(description=error.message)
            return
        except ItemNotFound as error:
            await ctx.error_embed(description=error.message)
            return
        embed = discord.Embed()
        embed.title = "``booster added!``"
        expired_on = get_relative_time(booster["expired"])
        embed.description = f"""
            >>> {self.bot.right} **name**: {booster["item_name"]}
            **threshold**: ``{booster["threshold"]}``
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
            return

        embed = discord.Embed(title="``booster removed!``")
        embed.description = "the booster item has been removed successfully"
        await ctx.send(embed=embed)


async def setup(bot: PepeBot) -> None:
    await bot.add_cog(
        economy(bot))
