from __future__ import annotations


"""
economy class for peepbot
~~~~~~~~~~~~~~~~~~~
:copyright: (c) xgreenapple(green apple)
:license: MIT see LICENSE for more details
"""

import datetime
import typing
from typing import TYPE_CHECKING, Optional, Tuple
import discord

from handler.database import database
from handler.errors import (
    NotEnoughCoins,
    NotEnoughMembers,
    DataDoesNotExists,
    NotFound,
    ItemNotFound,
    BadRequest
)

if TYPE_CHECKING:
    from pepebot import pepebot


# Economy base class, some useful methods that we will use later
class Economy:
    def __init__(self, Bot: pepebot):
        self.database: database = Bot.Database

        self.economy_table: str = "peep.economy"
        self.coin_column = "points"
        self.user_details = "peep.user_details"
        self.bot_cache = Bot.cache

    # returns total points that a user has
    async def getUserPoints(self, user: discord.Member) -> Optional[float]:

        total_points = await self.database.Select(
            user.guild.id, user.id,
            table=self.user_details,
            columns=self.coin_column,
            condition="""guild_id = $1
            AND user_id = $2"""
        )
        return round(total_points, 2) if total_points else 0

    # add points to user inventory
    async def addUserPoints(self, user: discord.Member, points: float = 1.0) -> Optional[float]:
        if points <= 0:
            raise BadRequest("points must be greater than 0")
        total = await self.database.Insert(
            user.guild.id,
            user.id,
            points,
            table=self.user_details,
            columns="guild_id,user_id,points",
            values="$1,$2,$3",
            on_Conflicts="""(guild_id,user_id) DO
            UPDATE SET points = COALESCE(user_details.points, 0) + $3""",
            returning_columns=["points"]
        )
        return round(total, 2)

    # reset user coins
    async def setUserPoints(self, user: discord.Member, points: float = 0) -> Optional[float]:
        points = abs(points)
        total = await self.database.Insert(
            user.guild.id,
            user.id,
            points,
            table=self.user_details,
            columns="guild_id,user_id,points",
            values="$1,$2,$3",
            on_Conflicts="""(guild_id,user_id) DO
                    UPDATE SET points =  $3""",
            returning_columns=["points"]
        )
        return round(total, 2)

    # remove user coins
    async def removeUserPoints(self, user: discord.Member, points: float = 1) -> Optional[float]:

        total = await self.getUserPoints(user)
        if points < 0:
            points = total
        if total == 0:
            raise NotEnoughCoins("user already has 0 coins")

        sub_points = round(total - points, 2)
        sub_points = sub_points if sub_points >= 0 else 0
        total = await self.setUserPoints(user=user, points=sub_points)
        return round(total, 2)

    # give points to other users
    async def GivePoints(self, author: discord.Member, user: discord.Member,
                         points: float) -> Optional[Tuple[float, float]]:
        if points < 0:
            points = 0
        author_points = await self.getUserPoints(author)
        if author_points == 0 or author_points is None or points > author_points:
            raise NotEnoughCoins("you don't have enough coins to give")

        # add coins to user
        member_total = await self.addUserPoints(user=user, points=points)
        # remove coins to author
        author_total = await self.removeUserPoints(user=author, points=points)

        return round(member_total, 2), round(author_total, 2)

    # get all users inventory coins sorted my maximum coins
    async def getAll_users(self, Guild_id: int, Fetch_row: bool = False, Filter: str = ""):
        List = await self.database.Select(
            Guild_id,
            table=self.user_details,
            columns="user_id, points" if not Fetch_row else "*",
            condition="guild_id = $1",
            return_everything=True,
            Filter=Filter
        )
        return List

    # get stats of a user
    async def getUser_stats(self, User: discord.Member):
        """
        :param User: the User whose stats you want to see
        :return: User top percentile, user position and likes
        """

        UserList = await self.getAll_users(User.guild.id,Filter="ORDER BY points DESC")
        if not UserList or len(UserList) == 0:
            raise NotEnoughMembers(" this guild leaderboard is currently unavailable")

        User_position: int = 0
        User_points: int = 0

        # Find the user in async List
        for i in UserList:
            User_position += 1
            if User.id == i['user_id']:
                User_points = i['points']
                break

        # check is user position or likes is None
        if User_points == 0:
            raise DataDoesNotExists(User)

        percent = User_position / len(UserList)
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

        return top_rank, User_position, round(User_points, 2)

    """Get shop Related stuffs"""

    # get shop items
    async def GetShopItems(self, guild_id: int, Column: str = "*"):
        raw_items = await self.database.Select(
            guild_id,
            table="peep.shop",
            columns=Column,
            condition="guild_id = $1",
            return_everything=True
        )
        if raw_items is None:
            raise NotFound()
        return raw_items

    # return item with its name
    async def GetItemNamed(self, guild_id: int, item: str, column: str = "items,cost,emoji,expired"):

        item = await self.database.Select(
            item,
            guild_id,
            return_everything=True,
            table="peep.shop",
            condition="items = $1 AND guild_id = $2",
            columns=column
        )
        if not item or not len(item):
            raise NotFound("this item doesnt exist")
        return item[0]

    # get a item from user
    async def getUserItem(self, user: discord.Member, item_name: str, columns: str = "items"):

        items = await self.database.Select(
            item_name,
            user.id,
            user.guild.id,
            table="peep.inventory",
            condition="items = $1 AND user_id = $2 AND guild_id = $3",
            columns=columns
        )
        return items

    # get a item from user
    async def getUserItems(self, user: discord.Member, row: bool = False):
        items = await self.database.Select(
            user.id,
            user.guild.id,
            table="peep.inventory",
            condition=" user_id = $1 AND guild_id = $2 ",
            columns="items, expired",
            return_everything=row
        )
        if items is None or len(items) == 0:
            raise DataDoesNotExists()
        return items

    # add items to the shop
    async def addShopItem(
            self, guild_id: int, name: str, cost: float, emoji: str = None,
            seconds: typing.Optional[int] = None):

        expired = datetime.timedelta(seconds=seconds) if seconds else None
        return await self.database.Insert(
            guild_id,
            name,
            cost,
            emoji,
            expired,
            table="peep.shop",
            columns="guild_id,items,cost,emoji,expired",
            values="$1,$2,$3,$4,$5",
            on_Conflicts="""(items) DO
            UPDATE SET cost = $3,emoji = $4, expired = $5"""
        )

    # add items to user inventory
    async def addItemToInv(self, user: discord.Member, item_name: str):
        item = await self.GetItemNamed(
            guild_id=user.guild.id, item=item_name, column='expired,items')
        await self.database.Insert(
            user.id,
            user.guild.id,
            item['items'],
            item['expired'] + datetime.datetime.utcnow() if item['expired'] else None,
            table="peep.inventory",
            columns="user_id,guild_id,items,expired",
            values="$1,$2,$3,$4")

    async def removeUserItems(self, user: discord.Member, item_name: str, forced: bool = True):
        items = await self.GetItemNamed(guild_id=user.guild.id, item=item_name)
        UserHasItem = await self.getUserItem(item_name=item_name, user=user)
        if not UserHasItem:
            raise BadRequest("item already not in user inventory")

        await self.database.Delete(
            item_name,
            user.id,
            user.guild.id,
            table="peep.inventory",
            condition="items = $1 AND user_id = $2 AND guild_id = $3"
        )
        if not forced:
            await self.addUserPoints(
                user=user,
                points=items['cost']
            )
        return items

    # remove item from the shop
    async def removeShopItems(self, guild_id: int, item_name: str):
        # check if item exists in the list if not raise not found error
        await self.GetItemNamed(guild_id=guild_id, item=item_name)
        await self.database.Delete(
            item_name.lower(),
            guild_id,
            table="peep.shop",
            condition="items = $1 AND guild_id = $2"
        )

    # buy a item from the shop
    async def BuyItem(self, user: discord.Member, item_name: str, bot: pepebot):

        PointBooster = await self.isPoint_booster(item_name=item_name, guild_id=user.guild.id)
        User_Coin = await self.getUserPoints(user)
        User_inv = await self.getUserItem(user=user, item_name=item_name)

        if User_Coin is None:
            raise DataDoesNotExists()
        if User_inv:
            raise BadRequest("cant buy more than 1 item")
        try:
            rawItem = await self.GetItemNamed(
                item=item_name.lower(), column='items,cost,emoji,expired',guild_id=user.guild.id)
            cost = rawItem['cost']
            emoji = rawItem['emoji']
            expired = rawItem['expired']
        except NotFound:
            raise ItemNotFound()
        threshold = 0
        if User_Coin < cost:
            raise NotEnoughCoins
        if PointBooster:
            expired, threshold = await self.AddBooster(user=user)
        else:
            await self.addItemToInv(user=user, item_name=item_name)

        if expired:
            # gets current running task data from the class
            current_data = bot.taskrunner.current_data
            await bot.taskrunner.SetTasks()
            # checks if current running task is older than this task
            if current_data and current_data['expired'] > \
                    expired + datetime.datetime.utcnow():
                await bot.taskrunner.ReloadTask()
        # remove coins from the user
        total = await self.removeUserPoints(user=user, points=cost)
        return cost, emoji, total, expired, PointBooster, threshold

    # adds booster item to user inventory
    async def AddBooster(self, user: discord.Member):
        data = await self.GetBooster(guild_id=user.guild.id)
        await self.database.Insert(
            user.id,
            user.guild.id,
            data['item_name'],
            data['expired'] + datetime.datetime.utcnow() if data['expired'] else None,
            table="peep.inv",
            columns="user_id,guild_id,items,expired",
            values="$1,$2,$3,$4")
        return data['expired'], data['threshold']

    async def cacheBooster(self, guild_id: int):
        data = await self.database.Select(
            guild_id,
            table="peep.booster",
            columns="item_name,expired,threshold",
            condition="guild_id = $1",
            row=True
        )
        self.bot_cache.Insert(guild_id, value={})
        self.bot_cache[guild_id]["boosterCache"] = data
        print(self.bot_cache)

        return data

    async def GetBooster(self, guild_id: int):
        if guild_id in self.bot_cache:
            data = self.bot_cache[guild_id]["boosterCache"]
        else:
            data = await self.cacheBooster(guild_id=guild_id)
        return data

    # check if user has booster item
    async def HasBooster(self, user: discord.Member):
        Guild_id = user.guild.id
        Booster = await self.GetBooster(Guild_id)
        if Booster:
            HasItem = await self.getUserItem(user=user, item_name=Booster["item_name"])
            return HasItem is not None, Booster
        return False, Booster

    # check if item is a point booster
    async def isPoint_booster(self, item_name: str, guild_id: int) -> bool:
        booster = await self.GetBooster(guild_id=guild_id)
        if not booster:
            return False
        if booster["item_name"] == item_name:
            return True
        return False

    async def UpdateShopBooster(self, guild_id: int, cost: float, emoji: str):
        """ insert/update booster from the database """
        # get the boosters data from the list
        data = await self.GetBooster(guild_id=guild_id)
        if not data:
            raise ItemNotFound
        # get the expires time of the booster
        expired: datetime.timedelta = data['expired']
        total_seconds = expired.total_seconds()
        await self.addShopItem(
            guild_id=guild_id, name=data["item_name"], seconds=int(total_seconds),
            cost=cost, emoji=emoji)

    async def Insert_Booster(self, name: str, guild_id: int, threshold: float, expired: datetime.timedelta):
        await self.database.Insert(
            guild_id,
            name,
            threshold,
            expired,
            table='peep.booster',
            columns='guild_id,item_name,threshold,expired',
            values='$1,$2,$3,$4',
            on_Conflicts=
            """(guild_id) DO
            UPDATE SET item_name = $2,threshold=$3,expired=$4
            """
        )
        await self.cacheBooster(guild_id=guild_id)

