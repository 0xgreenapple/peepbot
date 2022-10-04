"""
economy class for peepbot
~~~~~~~~~~~~~~~~~~~
:copyright: (c) xgreenapple(green apple)
:license: MIT see LICENSE for more details
"""
import typing
import discord

from handler.database import database
from handler.errors import (
    UserHasNotEnoughCoins,
    NotEnoughMembers,
    DataDoesNotExists, NotFound
)


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
    async def GetShopItems(self):
        ...

    # return item with its name
    async def GetItemNamed(self, item: str):
        item = await self.database.Select(
            item,
            return_everything=True,
            table="test.shop",
            condition="items = $1",
            columns="items,cost"
        )
        if not item:
            raise NotFound("this item doesnt exist")
        return item

    # get User items
    async def getUserItems(self, user: discord.Member, itemname: str):
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

    # add items to the shop
    async def addShopItem(self, name: str, cost: int, emoji: str):

        return await self.database.Insert(
            name,
            cost,
            emoji,
            table="test.shop",
            columns="items,cost,emoji",
            values="$1,$2,$3",
            on_Conflicts="""(items) DO
            UPDATE SET cost = $2,emoji = $3"""
        )

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

    async def removeShopItems(self):
        ...
