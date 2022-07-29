import asyncio
import io
import random
from io import BytesIO

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from handler.Context import Context
from handler.view import duel_button
from pepebot import pepebot
import logging


class duel(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot

    @commands.command(name='duel')
    @commands.guild_only()
    async def duel(self, ctx: Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.error_embed(error_name='duel command error', error_dis='you cant duel your self, lmfao')

        response_msg = await ctx.send(f"{member.mention} has been invited for meme duel, status: waiting...")

        try:
            channel = await member.create_dm()
            view = duel_button(message=response_msg, member=member, user=ctx.author, bot=self.bot)
            await channel.send(f'you have been invited for meme duel ``{member.name}``', view=view)

        except discord.Forbidden or discord.HTTPException:
            second_response = await response_msg.edit(content='failed to send message to user creating embed....')
            await asyncio.sleep(3)
            response2 = await second_response.edit(
                content=f"{member.mention} you have 20 min to accept the invite type on "
                        f"accept y")
    @commands.command(name='test')
    async def test(self,ctx:Context):
        message = await ctx.send('helo')
        await message.add_reaction("👍")
        await asyncio.sleep(3)
        message = await ctx.channel.fetch_message(message.id)
        count = 0
        for reaction in message.reactions:
            if reaction.emoji == "👍":
                count = reaction.count
                break

        print(count)


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        duel(bot))
