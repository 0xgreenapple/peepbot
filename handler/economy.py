from __future__ import annotations

"""
economy class for peepbot
~~~~~~~~~~~~~~~~~~~
:copyright: (c) xgreenapple(green apple)
:license: MIT see LICENSE for more details
"""
import datetime
import typing
from typing import TYPE_CHECKING
import discord

from handler.database import database
from handler.errors import (
    UserHasNotEnoughCoins,
    NotEnoughMembers,
    DataDoesNotExists, NotFound, ItemNotFound, BadRequest
)
if TYPE_CHECKING:
    from pepebot import pepebot


# Economy base class, some useful methods that we will use later
class Economy:
    def __init__(self, Database: database):
        self.database: database = Database
        self.economy_table: str = "test.economy"
        self.coin_column = "points"

    # return user coins
    async def getUserCoins(self, user: discord.Member) -> typing.Optional[int]:
        total_coins = await self.database.Select(
            user.guild.id, user.id,
            table=self.economy_table,
            columns=self.coin_column,
            condition="""guild_id = $1
            AND user_id = $2"""
        )
        return round(total_coins, 2) if total_coins else 0

    # add user coins
    async def addUserCoins(self, user: discord.Member, coins: float = 1):
        coins = abs(coins)
        await self.database.Insert(
            user.guild.id,
            user.id,
            coins,
            table=self.economy_table,
            columns="guild_id,user_id,points",
            values="$1,$2,$3",
            on_Conflicts="""(guild_id,user_id) DO
            UPDATE SET points = COALESCE(economy.points, 0) + $3""",
        )
        total = await self.getUserCoins(user=user)
        return round(total, 2)

    # remove user coins
    async def removeUserCoins(self, user: discord.Member, coins: float = 1):
        total = await self.getUserCoins(user)
        if total == 0:
            return 0
        sub_points = round(total - coins, 2)
        sub_points = sub_points if sub_points >= 0 else 0

        await self.setUserCoins(user=user, coins=sub_points)
        total = await self.getUserCoins(user)
        return round(total, 2)

    # reset user coins
    async def setUserCoins(self, user: discord.Member, coins: float = 0):
        coins = abs(coins)
        await self.database.Insert(
            user.guild.id,
            user.id,
            coins,
            table=self.economy_table,
            columns="guild_id,user_id,points",
            values="$1,$2,$3",
            on_Conflicts="""(guild_id,user_id) DO
                    UPDATE SET points =  $3""",
        )
        total = await self.getUserCoins(user=user)
        return round(total, 2)

    # give points to other users
    async def GivePoints(self, author: discord.Member, user: discord.Member, coins: float):
        author_coins = await self.getUserCoins(author)
        user_coins = await self.getUserCoins(user)

        if author_coins == 0 or author_coins is None:
            raise UserHasNotEnoughCoins("the user has 0 coins")
        if coins > author_coins:
            raise UserHasNotEnoughCoins(
                "user has not enough coins to give")

        # add coins to user
        member_total = await self.addUserCoins(user=user, coins=coins)
        # remove coins to author
        author_total = await self.removeUserCoins(user=author, coins=coins)

        return round(member_total, 2), round(author_total)

    # get all users sorted my maximum
    async def getAll_users(self, Guild_id: int, Fetch_row: bool = False, Filter: str = ""):

        List = await self.database.Select(
            Guild_id,
            table="test.economy",
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

        UserList = await self.getAll_users(User.guild.id)
        print(UserList)
        if not UserList or len(UserList) == 0:
            raise NotEnoughMembers(" this guild leaderboard is currently not available")

        print("12 ", UserList)

        User_position: int = 0
        User_likes: int = 0

        # Find the user in asynpg List
        for i in UserList:
            User_position += 1
            if User.id == i['user_id']:
                User_likes = i['points']
                break

        # check is user position or likes is None
        if User_likes == 0:
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

        return top_rank, User_position, round(User_likes, 2)

    """Get shop Related stuffs"""

    # get shop items
    async def GetShopItems(self, Column: str = "*"):
        raw_items = await self.database.Select(
            table="test.shop",
            columns=Column,
            return_everything=True
        )
        if raw_items is None:
            raise NotFound()
        return raw_items

    # return item with its name
    async def GetItemNamed(self, item: str, column: str = "items,cost,emoji"):
        item = await self.database.Select(
            item,
            return_everything=True,
            table="test.shop",
            condition="items = $1",
            columns=column
        )
        if not item or not len(item):
            raise NotFound("this item doesnt exist")
        print('item ; ',item)
        return item[0]

    # get a item from user
    async def getUserItem(self, user: discord.Member, itemname: str):
        items = await self.database.Select(
            itemname,
            user.id,
            user.guild.id,
            table="test.inv",
            condition="items = $1 AND user_id = $2 AND guild_id = $3",
            columns="items"
        )
        if not user:
            raise NotFound()
        return items

        # get a item from user

    async def getUserItems(self, user: discord.Member):
        items = await self.database.Select(
            user.id,
            user.guild.id,
            table="test.inv",
            condition=" user_id = $1 AND guild_id = $2",
            columns="items"
        )
        if items is None or len(items) == 0:
            raise DataDoesNotExists()

        if not user:
            raise NotFound()
        return items

    # add items to the shop
    async def addShopItem(self, name: str, cost: float, emoji: str, seconds: typing.Optional[int] = None):
        expired = datetime.timedelta(seconds=seconds) if seconds else None
        return await self.database.Insert(
            name,
            cost,
            emoji,
            expired,
            table="test.shop",
            columns="items,cost,emoji,expired",
            values="$1,$2,$3,$4",
            on_Conflicts="""(items) DO
            UPDATE SET cost = $2,emoji = $3, expired = $4"""
        )

    # add items to user inventory
    async def addItemtoInv(self, user: discord.Member, itemname: str):
        item = await self.GetItemNamed(itemname, column='expired,items')
        await self.database.Insert(
            user.id,
            user.guild.id,
            item['items'],
            item['expired'] + datetime.datetime.now() if item['expired'] else None,
            table="test.inv",
            columns="user_id,guild_id,items,expired",
            values="$1,$2,$3,$4")


    async def removeUserItems(self, user: discord.Member, itemname: str, forced: bool = True):
        items = await self.GetItemNamed(item=itemname)

        await self.database.Delete(
            itemname,
            user.id,
            user.guild.id,
            table="test.inv",
            condition="items = $1 AND user_id = $2 AND guild_id = $3"
        )
        if not forced:
            await self.removeUserCoins(
                user=user,
                coins=items[0]['cost']
            )
        return items

    # remove item from the shop
    async def removeShopItems(self, itemname: str):
        # check if item exists in the list if not raise not found error
        await self.GetItemNamed(item=itemname)
        await self.database.Delete(
            itemname.lower(),
            table="test.shop",
            condition="items = $1"
        )

    # buy a item from the shop
    async def Buyitem(self, user: discord.Member, item_name: str, bot:pepebot):
        items = await self.GetShopItems(Column="items,cost,emoji")
        PointBooster = await self.isPoint_booster(item_name=item_name, guild_id=user.guild.id)

        User_Coin = await self.getUserCoins(user)
        User_inv = await self.getUserItem(user=user, itemname=item_name)

        if User_Coin is None:
            raise DataDoesNotExists()
        if User_inv:
            raise BadRequest("cant buy more than 1 item")
        try:
            rawItem = await self.GetItemNamed(
                item_name.lower(), column='items,cost,emoji,expired')
            print('raw item :' ,rawItem)
            cost = rawItem['cost']
            emoji = rawItem['emoji']
            expired = rawItem['expired']
        except NotFound:
            raise ItemNotFound()
        threshold = 0
        if User_Coin < cost:
            raise UserHasNotEnoughCoins
        if PointBooster:
            cost, expired, threshold = await self.AddBooster(user=user)
        if expired:
            await bot.taskrunner.ReloadTask()
        else:
            await self.addItemtoInv(user=user, itemname=item_name)

        total = await self.removeUserCoins(user=user, coins=cost)
        return cost, emoji, total, expired, PointBooster, threshold

    async def AddBooster(self, user: discord.Member):
        """ adds  item to user inventory """
        data = await self.GetBooster(guild_id=user.guild.id)
        await self.database.Insert(
            user.id,
            user.guild.id,
            data['item_name'],
            data['expired'] + datetime.datetime.now() if data['expired'] else None,
            table="test.inv",
            columns="user_id,guild_id,items,expired",
            values="$1,$2,$3,$4")
        return data['cost'], data['expired'], data['threshold']

    async def GetBooster(self, guild_id: int):
        data = await self.database.Select(
            guild_id,
            table="test.booster",
            columns="item_name,cost,expired",
            condition="guild_id = $1"
        )
        if not data:
            raise NotFound('booster for this guild does not exists')
        return data

    async def isPoint_booster(self, item_name: str, guild_id: int) -> bool:
        data = await self.database.Select(
            guild_id,
            item_name,
            table="test.booster",
            columns='item_name',
            condition='guild_id = $1 AND item_name = $2'
        )
        if data:
            raise True
        else:
            return False

    async def UpdateShopBooster(self, guild_id: int, name: str, cost: float,emoji:str):
        data = await self.GetBooster(guild_id=guild_id)
        expired: typing.Optional[datetime.timedelta] = data['expired'] if data['expired'] else None
        total_seconds = expired.total_seconds() if expired else None
        await self.addShopItem(name=name, seconds=total_seconds, cost=cost, emoji=emoji)

    async def Insert_Booster(self, name: str, guild_id: int, threshold: float, expired: datetime.timedelta):
        await self.database.Insert(
            guild_id,
            name,
            threshold,
            expired,
            table='test.booster',
            columns='guild_id,item_name,threshold,expired',
            values='$1,$2,$3,$4',
            on_Conflicts=
            """(guild_id) DO
            UPDATE SET item_name = $2,threshold=$3,expired=$4
            """
        )
