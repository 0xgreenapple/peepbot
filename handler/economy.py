"""
economy class for peepbot
~~~~~~~~~~~~~~~~~~~
:copyright: (c) xgreenapple(green apple)
:license: MIT see LICENSE for more details
"""
import typing
import discord

from handler.database import database


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
        return round(total_coins, 2)

    # return user items
    async def getUserItems(self, user: discord.Member):
        ...

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
        return round(total,2)

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
    async def GivePoints(self, author: discord.Member, user: discord.Member , coins:float):
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

    # buy something for a price
    async def userBuyitems(self, author: discord.Member, price: float):
        ...


class UserHasNotEnoughCoins(Exception):
    def __init__(self, message: str = " user already has no coins"):
        self.message = message
        super().__init__(message)
