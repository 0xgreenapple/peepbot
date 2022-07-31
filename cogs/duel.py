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

    @commands.command(name='battle')
    @commands.guild_only()
    async def duel(self, ctx: Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.error_embed(
                error_name='battle command error',
                error_dis='you cant duel your self, lmfao'
            )
            return
        if (ctx.channel.type == discord.ChannelType.public_thread) or (ctx.channel.type == discord.ChannelType.private_thread):
            await ctx.error_embed(
                error_name='battle command error',
                error_dis='you cant run the battle command in a thread'
            )
            return


        response_msg = await ctx.send(f"{member.mention} has been invited for meme duel, status: waiting...")

        try:
            channel = await member.create_dm()
            view = duel_button(message=response_msg, member=member, user=ctx.author, bot=self.bot)
            embed = discord.Embed(title=f'you have been invited for meme battle by {ctx.author.name}')
            message = await channel.send(embed=embed, view=view)
            view.interaction_message = message

        except discord.Forbidden or discord.HTTPException:
            view = duel_button(message=response_msg, member=member, user=ctx.author, bot=self.bot)
            second_response = await response_msg.edit(content='failed to send message to user creating embed....')
            await asyncio.sleep(3)
            response2 = await second_response.edit(
                content=f"{member.mention} you have 20 min to accept the invite type on "
                        f"accept ",view=view)


    @commands.command(name='test')
    async def test(self,ctx:Context):
        embed = discord.Embed(title='hello',description='nooooooooooo',type='link')
        await ctx.send(embed=embed)
async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        duel(bot))
