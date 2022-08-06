import asyncio
import io
import os
import random
import typing
from io import BytesIO

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

from handler.Context import Context
from handler.pagination import SimplePages
from handler.view import duel_button
from pepebot import pepebot
import logging


class leaderboard(SimplePages):
    def __init__(self, entries: list, *, ctx: Context, per_page: int = 12, title: str = None):
        converted = entries

        super().__init__(converted, per_page=per_page, ctx=ctx)


async def image_or_embed(message: discord.Message):
    embeds = message.embeds
    attachments = message.attachments
    if attachments:

        image = None
        for attachment in attachments:
            if attachment.content_type.lower().startswith('image'):
                image = attachment
            break
        return image

    elif embeds:

        image = None

        for embed in embeds:

            if embed.type == 'image' or embed.type == 'gifv':
                image = embed

            break
        return image
    else:
        return None


async def get_attachments(ctx: Context):
    # command message
    message = ctx.message

    # ref message
    refmessage = message.reference
    result = None
    if refmessage and isinstance(refmessage.resolved, discord.Message):
        resolved = refmessage.resolved

        attachment = await image_or_embed(resolved)

        if attachment is not None:
            if isinstance(attachment, discord.Embed):
                result = attachment
            elif attachment.content_type.lower().startswith('image'):
                result = attachment
        return result

    else:
        attachment = await image_or_embed(ctx.message)
        if attachment is not None:
            if isinstance(attachment, discord.Embed):
                result = attachment
            elif attachment.content_type.lower().startswith('image'):

                result = attachment

        return result


async def get_image(header:str, url:str, bot: pepebot = None):
    atachment_url = url

    session: aiohttp.ClientSession = bot.aiohttp_session
    base_url = f"https://api.jeyy.xyz/image/{header}?image_url={atachment_url}"

    res = await session.get(url=base_url)
    print(res.content_type)

    return res



class creation(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot

    async def errorr(self):
        a = 1 / 0
        return a

    @commands.command(name='cube')
    @commands.cooldown(1,3,BucketType.user)
    async def cube(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'cube'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response =  await get_image(header=type,url=file.proxy_url,bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None,attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response =await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab),filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='sphere')
    @commands.cooldown(1, 3, BucketType.user)
    async def sphere(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'globe'

        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='burn')
    @commands.cooldown(1, 3, BucketType.user)
    async def brun(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'burn'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='boil')
    @commands.cooldown(1, 3, BucketType.user)
    async def boil(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'boil'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='bomb')
    @commands.cooldown(1, 3, BucketType.user)
    async def bomb(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'bomb'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='patpat')
    @commands.cooldown(1, 3, BucketType.user)
    async def patpat(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'patpat'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='shock')
    @commands.cooldown(1, 3, BucketType.user)
    async def shock(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'shock'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='canny')
    @commands.cooldown(1, 3, BucketType.user)
    async def canny(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'canny'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='fire')
    @commands.cooldown(1, 3, BucketType.user)
    async def fire(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'fire'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='balls')
    @commands.cooldown(1, 3, BucketType.user)
    async def balls(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'balls'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='infinity')
    @commands.cooldown(1, 3, BucketType.user)
    async def infinity(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'infinity'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='bubble')
    @commands.cooldown(1, 3, BucketType.user)
    async def bubble(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'bubble'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='cloth')
    @commands.cooldown(1, 3, BucketType.user)
    async def cloth(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'cloth'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='cow')
    @commands.cooldown(1, 3, BucketType.user)
    async def cow(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'cow'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='wall')
    @commands.cooldown(1, 3, BucketType.user)
    async def wall(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'wall'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='paint')
    @commands.cooldown(1, 3, BucketType.user)
    async def paint(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'paint'
        if file:
            print(file)
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

    @commands.command(name='spin')
    @commands.cooldown(1, 3, BucketType.user)
    async def spin(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        type = 'spin'
        if file:
            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=file.proxy_url, bot=self.bot)
            a = await response.read()

            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(a), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        elif a:
            print('aa')
            if isinstance(a, discord.Embed):
                message = await ctx.send(f'this will take some time {randomemoji}')
                response = await get_image(header=type, url=a.url, bot=self.bot)
                ab = await response.read()

                if response.content_type.lower().endswith('gif'):
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
                else:
                    file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
                await message.edit(content=None, attachments=[file])
                return

            message = await ctx.send(f'this will take some time {randomemoji}')
            response = await get_image(header=type, url=a.proxy_url, bot=self.bot)

            ab = await response.read()
            if response.content_type.lower().endswith('gif'):
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

            await message.edit(content=None, attachments=[file])
            return

        else:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return

async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        creation(bot))
