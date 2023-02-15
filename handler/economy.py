from __future__ import annotations

import asyncio

import asyncpg

from handler.utils import record_to_dict

"""
economy class for peepbot
~~~~~~~~~~~~~~~~~~~
:copyright: (c) xgreenapple(green apple)
:license: MIT see LICENSE for more details
"""

import datetime
from datetime import timedelta, datetime
import typing
from typing import TYPE_CHECKING, Optional, Tuple, List, Union
import discord

from handler.database import Database, get_guild_settings
from handler.errors import (
    NotEnoughCoins,
    NotEnoughMembers,
    DataDoesNotExists,
    NotFound,
    ItemNotFound,
    BadRequest
)

if TYPE_CHECKING:
    from pepebot import PepeBot


# Economy base class, some useful methods that we will use later
class Economy:
    def __init__(self, bot: PepeBot):
        self.database: Database = bot.database

        self.economy_table: str = "peep.economy"
        self.coin_column = "points"
        self.user_details = "peep.user_details"
        self.bot_cache = bot.cache
        self.bot = bot

    async def get_user_points(self, user: discord.Member) -> Optional[float]:
        """ return total points a user has """
        total_points = await self.database.select(
            user.guild.id, user.id,
            table_name=self.user_details,
            columns=self.coin_column,
            conditions="""guild_id = $1
            AND user_id = $2"""
        )
        return round(total_points, 2) if total_points else 0

    async def add_user_points(
            self, user: discord.Member, points: float = 1.0
    ) -> Optional[float]:

        """ add given coins to user inventory and
            return total coins user has """
        if points <= 0:
            raise BadRequest("points must be greater than 0")
        total = await self.database.insert(
            user.guild.id,
            user.id,
            points,
            table=self.user_details,
            columns="guild_id,user_id,points",
            values="$1,$2,$3",
            on_conflicts="""(guild_id,user_id) DO
            UPDATE SET points = COALESCE(user_details.points, 0) + $3""",
            returning_columns=["points"]
        )
        return round(total, 2)

    # reset user coins
    async def set_user_points(
            self, user: discord.Member, points: float = 0
    ) -> Optional[float]:

        """ set user points to given value points """
        points = abs(points)
        await self.database.insert(
            user.guild.id,
            user.id,
            points,
            table=self.user_details,
            columns="guild_id,user_id,points",
            values="$1,$2,$3",
            on_conflicts="""(guild_id,user_id) DO
                    UPDATE SET points =  $3""",
        )
        return round(points, 2)

    # remove user coins
    async def remove_user_points(
            self, user: discord.Member, points: float = 1
    ) -> Optional[float]:

        """ remove points from user inventory """

        total = await self.get_user_points(user)
        if points < 0:
            points = total
        if total == 0:
            raise NotEnoughCoins("user already has 0 coins")

        sub_points = round(total - points, 2)
        sub_points = sub_points if sub_points >= 0 else 0
        total = await self.set_user_points(user=user, points=sub_points)
        return round(total, 2)

    async def give_points(
            self, author: discord.Member, user: discord.Member,
            points: float
    ) -> Optional[Tuple[float, float]]:

        """ give points to another user """

        author_points = await self.get_user_points(author)
        if not (author_points or points < author_points):
            raise NotEnoughCoins("you don't have enough coins to give")

        member_total = await self.add_user_points(
            user=user, points=points)
        author_total = await self.remove_user_points(
            user=author, points=points)
        return round(member_total, 2), round(author_total, 2)

    # get all users inventory coins sorted my maximum coins
    async def get_all_users(
            self, guild_id: int, fetch_row: bool = False, filter_by: str = ""
    ) -> Optional[List[asyncpg.Record]]:
        """ return all users in the guild """
        users = await self.database.select(
            guild_id,
            table_name=self.user_details,
            columns="user_id, points" if not fetch_row else "*",
            conditions="guild_id = $1",
            return_all_rows=True,
            filter_by=filter_by
        )
        return users

    # get stats of a user
    async def get_user_stats(
            self, user: discord.Member) -> Tuple[str, int, float]:

        """ return given user stats. """

        user_list = await self.get_all_users(
            user.guild.id, filter_by="ORDER BY points DESC")
        if user_list is None or len(user_list) == 0:
            raise NotEnoughMembers(
                " this guild leaderboard is currently unavailable")

        user_position: int = 0
        user_points: int = 0

        # Find the user in async List
        for user_data in user_list:
            user_position += 1
            if user.id == user_data['user_id']:
                user_points = user_data['points']
                break

        # check is user position or likes is None
        if user_points == 0:
            raise DataDoesNotExists(user)

        percent = user_position / len(user_list)
        if percent <= 0.1:
            top_rank = '1%'
        elif 0.1 <= percent <= 0.25:
            top_rank = '10%'
        elif 0.25 <= percent <= 0.50:
            top_rank = '25%'
        elif 0.50 <= percent <= 0.75:
            top_rank = '75%'
        else:
            top_rank = '90%'

        return top_rank, user_position, round(user_points, 2)

    async def get_shop_items(
            self, guild_id: int, column: str = "*") -> asyncpg.Record:
        """ get all shop items """
        raw_items = await self.database.select(
            guild_id,
            table_name="peep.shop",
            columns=column,
            conditions="guild_id = $1",
            return_all_rows=True
        )
        if raw_items is None:
            raise NotFound()
        return raw_items

    # return item with its name
    async def get_item_named(
        self, guild_id: int, item_name: str,
        columns: str = "items,cost,emoji,expired"
    ) -> Optional[asyncpg.Record]:

        """ return an item with given name
            if nothing is found it will return none """

        item_name = await self.database.select(
            item_name,
            guild_id,
            return_all_rows=True,
            table_name="peep.shop",
            conditions="items = $1 AND guild_id = $2",
            columns=columns
        )
        return item_name[0] if item_name else None

    # get a item from user
    async def get_user_item(
        self, user: discord.Member, item_name: str,
        columns: str = "items"
    ) -> Optional[asyncpg.Record]:

        """ get a specific item from the user """

        items = await self.database.select(
            item_name,
            user.id,
            user.guild.id,
            table_name="peep.inventory",
            conditions="items = $1 AND user_id = $2 AND guild_id = $3",
            columns=columns
        )
        return items

    # get a item from user
    async def get_user_items(
            self, user: discord.Member, row: bool = False
    ) -> asyncpg.Record:

        """ get all items from the user """

        items = await self.database.select(
            user.id,
            user.guild.id,
            table_name="peep.inventory",
            conditions=" user_id = $1 AND guild_id = $2 ",
            columns="items, expired",
            return_all_rows=row
        )
        if items is None or len(items) == 0:
            raise DataDoesNotExists()
        return items

    # add items to the shop
    async def add_shop_item(
        self, guild_id: int, name: str, cost: float,
        emoji: str = None, seconds: typing.Optional[int] = None
    ):
        """ add a item to shop """

        expired = datetime.timedelta(seconds=seconds) if seconds else None
        await self.database.insert(
            guild_id,
            name,
            cost,
            emoji,
            expired,
            table="peep.shop",
            columns="guild_id,items,cost,emoji,expired",
            values="$1,$2,$3,$4,$5",
            on_conflicts="""(items) DO
            UPDATE SET cost = $3,emoji = $4, expired = $5"""
        )

    # add items to user inventory
    async def add_item_to_inv(self, user: discord.Member, item_name: str):

        """ add item to user inventory """

        item = await self.get_item_named(
            guild_id=user.guild.id, item_name=item_name,
            columns='expired,items')
        if item is None:
            raise ItemNotFound("item doesnt exist in the shop")
        expiring_on = None
        if item['expired']:
            expiring_on = item['expired'] + datetime.utcnow()
        await self.database.insert(
            user.id,
            user.guild.id,
            item['items'],
            expiring_on,
            table="peep.inventory",
            columns="user_id,guild_id,items,expired",
            values="$1,$2,$3,$4")

    async def remove_user_items(
        self, user: discord.Member, item_name: str, forced: bool = True
    ) -> asyncpg.Record:
        """ remove an item from the user inventory"""
        items = await self.get_item_named(
            guild_id=user.guild.id, item_name=item_name)
        if items is None:
            raise NotFound
        user_has_item = await self.get_user_item(
            item_name=item_name, user=user)
        if not user_has_item:
            raise BadRequest("item already not in user inventory")

        await self.database.delete(
            item_name,
            user.id,
            user.guild.id,
            table="peep.inventory",
            condition="items = $1 AND user_id = $2 AND guild_id = $3"
        )
        if not forced:
            await self.add_user_points(
                user=user,
                points=items['cost']
            )
        return items

    async def remove_shop_items(self, guild_id: int, item_name: str):

        """ remove an item from the user shop """

        item = await self.get_item_named(
            guild_id=guild_id, item_name=item_name)
        if item is None:
            raise NotFound
        await self.database.delete(
            item_name.lower(),
            guild_id,
            table="peep.shop",
            condition="items = $1 AND guild_id = $2"
        )

    # buy a item from the shop
    async def buy_item(
        self, user: discord.Member, item_name: str, bot: PepeBot
    ) -> Tuple[float, str, float, timedelta, bool, float]:

        user_points = await self.get_user_points(user)
        # check if user has given item
        user_has_item = await self.get_user_item(
            user=user, item_name=item_name)
        is_booster_item = False
        if user_has_item:
            raise BadRequest("cant buy more than 1 item")

        item_metadata = await self.get_item_named(
            item_name=item_name.lower(), columns='items,cost,emoji,expired',
            guild_id=user.guild.id)
        booster_item = await self.get_booster(guild_id=user.guild.id)
        if item_metadata is None:
            raise ItemNotFound("item doesnt exist in the shop")

        cost = item_metadata['cost']
        emoji = item_metadata['emoji']
        expire_time = item_metadata['expired']
        threshold = 1
        if user_points < cost:
            raise NotEnoughCoins
        if booster_item is not None:
            if booster_item["item_name"] == item_metadata["items"]:
                threshold = booster_item["threshold"]
                is_booster_item = True
        await self.add_item_to_inv(user=user, item_name=item_name)

        if expire_time is not None:
            # gets current running task data from the class
            current_data = bot.taskrunner.current_data
            await bot.taskrunner.SetTasks()
            # checks if current running task is older than this task
            if (current_data and
                    current_data['expired'] > expire_time
                    + datetime.utcnow()):
                await bot.taskrunner.ReloadTask()

        # remove coins from the user
        total = await self.remove_user_points(user=user, points=cost)
        await self.log_item(guild_id=user.guild.id, user_id=user.id,
                            item=item_metadata)
        return cost, emoji, total, expire_time, is_booster_item, threshold

    async def cache_booster(
        self, guild_id: int
    ) -> Optional[Union[dict, asyncpg.Record]]:

        data = await self.database.select(
            guild_id,
            table_name="peep.booster",
            columns="item_name,threshold",
            conditions="guild_id = $1",
            return_row=True
        )
        if data is not None:
            data = record_to_dict(data)
            shop_item = await self.get_item_named(
                guild_id=guild_id, item_name=data["item_name"])
            data["expired"] = shop_item["expired"]

        self.bot_cache.Insert(guild_id, value={})
        self.bot_cache[guild_id]["boosterCache"] = data
        return data

    async def get_booster(
            self, guild_id: int
    ) -> Optional[Union[asyncpg.Record, dict]]:
        if (guild_id in self.bot_cache and
                "boosterCache" in self.bot_cache):
            data = self.bot_cache[guild_id]["boosterCache"]
        else:
            data = await self.cache_booster(guild_id=guild_id)
        return data

    # check if user has booster item
    async def has_booster(self, user: discord.Member):
        guild_id = user.guild.id
        booster = await self.get_booster(guild_id)
        if booster:
            has_item = await self.get_user_item(
                user=user, item_name=booster["item_name"])
            return has_item is not None, booster
        return False, booster

    # check if item is a point booster
    async def is_point_booster(self, item_name: str, guild_id: int) -> bool:
        booster = await self.get_booster(guild_id=guild_id)
        if not booster:
            return False
        if booster["item_name"] == item_name:
            return True
        return False

    async def update_shop_Booster(
        self, guild_id: int, cost: float, emoji: str
    ):
        """ insert/update booster from the database """
        # get the boosters data from the list
        data = await self.get_booster(guild_id=guild_id)
        if not data:
            raise ItemNotFound
        # get the expires time of the booster
        expiring_time: datetime.timedelta = data['expired']
        total_seconds = expiring_time.total_seconds()
        await self.add_shop_item(
            guild_id=guild_id, name=data["item_name"],
            seconds=int(total_seconds),
            cost=cost, emoji=emoji)

    async def insert_Booster(self, name: str, guild_id: int, threshold: float):
        """ make an item booster item """
        shop_item = await self.get_item_named(
            guild_id=guild_id, item_name=name.lower())
        if shop_item is None:
            raise ItemNotFound(message=f"item {name} doesn't exist in the shop")
        if threshold <= 1 or threshold > 5:
            raise BadRequest("threshold must be greater than 1 and less than 5")

        await self.database.insert(
            guild_id,
            name.lower(),
            threshold,
            table='peep.booster',
            columns='guild_id,item_name,threshold',
            values='$1,$2,$3',
            on_conflicts=
            """(guild_id) DO
            UPDATE SET item_name = $2,threshold=$3
            """
        )
        return await self.cache_booster(guild_id=guild_id)

    async def delete_Booster(self, guild_id: int):
        booster = await self.get_booster(guild_id=guild_id)
        if booster is None:
            raise NotFound
        await self.database.delete(
            guild_id,
            table="peep.booster",
            condition="guild_id=$1"
        )
        self.bot_cache[guild_id]["boosterCache"] = None
        return booster

    async def is_turned_on(self, guild_id: int) -> bool:
        settings = await get_guild_settings(bot=self.bot, guild_id=guild_id)
        if not settings:
            return False
        if settings["economy"]:
            return True
        return False

    async def log_item(self, guild_id: int, user_id: int, item) -> asyncio.Task:
        return self.bot.loop.create_task(self.database.insert(
            guild_id,
            user_id,
            item["items"],
            item["cost"],
            datetime.utcnow(),
            item["expired"],
            table="peep.shoplog",
            columns="guild_id,user_id,item_name,"
                    "cost,purchased_at,expired_on",
            values="$1,$2,$3,$4,$5,$6"
        ))
