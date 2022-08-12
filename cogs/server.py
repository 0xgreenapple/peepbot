import asyncio
import io
import os
import random
from io import BytesIO
import re
import aiohttp
import discord
from discord import errors
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from handler.Context import Context
from handler.constant import topic1

from handler.pagination import SimplePages
from handler.view import duel_button
from pepebot import pepebot
import logging


class leaderboard(SimplePages):
    def __init__(self, entries: list, *, ctx: Context, per_page: int = 12, title: str = None):
        converted = entries
        print(entries)
        super().__init__(converted, per_page=per_page, ctx=ctx)


class utlis(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot
        self.topicss = topic1

    @commands.command(name='deadchat')
    @commands.cooldown(1,3600,type=BucketType.guild)
    async def deadchat(self,ctx:Context):
        is_active = await self.bot.db.fetchval(
            """SELECT active FROM test.utils WHERE guild_id1 = $1""",ctx.guild.id
        )

        role = await self.bot.db.fetchval(
            """SELECT role_id1 FROM test.utils WHERE guild_id1 = $1""",ctx.guild.id
        )
        if is_active:
            if role:
                role = ctx.guild.get_role(role)
                await ctx.send(f'{role.mention} make this chat active,** {random.choice(topic1)}**')




async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        utlis(bot))
