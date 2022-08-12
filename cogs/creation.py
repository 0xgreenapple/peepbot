import asyncio
import io
import os
import random
import typing
from io import BytesIO
import re

import aiohttp
import discord
from PIL import Image
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
    emojis = re.findall(r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>', message.content)
    sticlers = message.stickers

    image = None
    if attachments:
        for attachment in attachments:
            if attachment.content_type.lower().startswith('image'):
                image = attachment
            break
    elif embeds:
        for embed in embeds:

            if embed.type == 'image' or embed.type == 'gifv':
                image = embed
            break
    elif len(emojis):
        is_animated = True if emojis[0][0].lower() == 'a' else False
        first_emoji = discord.PartialEmoji(name=emojis[0][1],id=emojis[0][2],animated=is_animated)
        if not first_emoji.is_unicode_emoji():
            image = first_emoji
    elif len(sticlers):
        image = sticlers[0]

    return image


async def get_attachments(ctx: Context):
    # command message
    message = ctx.message

    # ref message
    refmessage = message.reference
    result = None
    if refmessage and isinstance(refmessage.resolved, discord.Message):
        resolved = refmessage.resolved

        attachment = await image_or_embed(resolved)
        print(attachment)

        if attachment is not None:
            if isinstance(attachment, (discord.Embed,discord.PartialEmoji,discord.StickerItem)):
                print('yes')
                result = attachment
            elif attachment.content_type.lower().startswith('image'):
                result = attachment


        return result

    elif not refmessage:
        attachment = await image_or_embed(ctx.message)
        if attachment is not None:
            if isinstance(attachment, (discord.Embed,discord.PartialEmoji,discord.StickerItem)):
                result = attachment
            elif attachment.content_type.lower().startswith('image'):
                result = attachment
        else:
            messages = ctx.channel.history(limit=100)
            async for i in messages:
                i: discord.Message
                message = await image_or_embed(i)
                if message:
                    result = message
                    break

        return result
    else:
        a = await ctx.channel.history(limit=100)
        for i in a:
            i: discord.Message
            message = await image_or_embed(i)
            if message:
                break


async def get_image(header: str, url: str, bot: pepebot = None):
    atachment_url = url

    session: aiohttp.ClientSession = bot.aiohttp_session
    base_url = f"https://api.jeyy.xyz/image/{header}?image_url={atachment_url}"
    res = await session.get(url=base_url)

    return res


async def caption_image(
        proxy_url: str, *, top_text: str = None,
        bottom_text: str = None, height: int = None,
        width: int = None, bot: pepebot):
    # client session
    session: aiohttp.ClientSession = bot.aiohttp_session
    if not top_text and not bottom_text and not height and not width:
        return None

    if top_text:
        top_text = top_text.replace(' ', '_').replace('#', '~h')
    else:
        top_text = '_'
    if bottom_text:
        bottom_text = bottom_text.replace(' ', '_').replace('#', '~h')
    else:
        bottom_text = '_'

    ext = '.png'
    if proxy_url.endswith('gif'):
        ext = '.gif'

    H = None
    w = None
    if height:
        H = height
    if width:
        w = width

    base_url = f'https://api.memegen.link/images/custom/{top_text}/{bottom_text}{ext}?background={proxy_url}'
    response = await session.get(url=base_url)

    if response.status != 200:
        return None
    if response.content_type.lower().endswith('gif'):
        ext = '.gif'

    _bytes = await response.read()

    file = discord.File(fp=io.BytesIO(_bytes), filename=f'meme{ext}')

    return file


async def handle_process(
        ctx: Context, type: str, bot: pepebot, *, file: discord.Attachment = None,
        embed: typing.Union[discord.Attachment, discord.Embed] = None):
    randomemoji = random.choice([bot.spongebob, bot.doge])

    if file:
        message = await ctx.send(f'this will take some time {randomemoji}')
        response = await get_image(header=type, url=file.proxy_url, bot=bot)
        a = await response.read()
        try:
            image = Image.open(io.BytesIO(a))
        except:
            await message.edit(content=f'something went wrong {bot.spongebob}')
            return

        if image.is_animated:
            file = discord.File(fp=io.BytesIO(a), filename='meme.gif')
        else:
            file = discord.File(fp=io.BytesIO(a), filename='meme.png')
        await message.edit(content=None, attachments=[file])
        return

    elif embed:
        message = await ctx.send(f'this will take some time {randomemoji}')

        if isinstance(embed, (discord.Embed,discord.PartialEmoji,discord.StickerItem)):
            response = await get_image(header=type, url=embed.url, bot=bot)
            ab = await response.read()
            try:
                image = Image.open(io.BytesIO(ab))
            except:
                await message.edit(content=f'something went wrong {bot.spongebob}')
                return

            if image.is_animated:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
            else:
                file = discord.File(fp=io.BytesIO(ab), filename='meme.png')
            await message.edit(content=None, attachments=[file])
            return

        response = await get_image(header=type, url=embed.proxy_url, bot=bot)
        ab = await response.read()
        try:
            image = Image.open(io.BytesIO(ab))
        except:
            await message.edit(content=f'something went wrong {bot.spongebob}')
            return

        if image.is_animated:
            file = discord.File(fp=io.BytesIO(ab), filename='meme.gif')
        else:
            file = discord.File(fp=io.BytesIO(ab), filename='meme.png')

        await message.edit(content=None, attachments=[file])
        return


class creation(commands.Cog):
    def __init__(self, bot: pepebot) -> None:
        self.bot = bot

    async def errorr(self):
        a = 1 / 0
        return a



    @commands.command(name='meme')
    @commands.cooldown(1, 3, BucketType.user)
    async def meme(self, ctx: Context, file: typing.Optional[discord.Attachment], *, caption: str):

        randomemoji = random.choice([self.bot.spongebob, self.bot.doge])
        a = await get_attachments(ctx=ctx)

        if not a and file:
            await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
            return
        if file:

            if not file.content_type.lower().startswith('image'):
                await ctx.send(content=f'{self.bot.spongebob} give me something to edit, must be image or gif')
                return
        first_caption = '_'
        second_caption = '_'
        m = caption.split(',')

        if len(m) >= 2:
            first_caption = m[0]
            second_caption = m[1]
        else:
            first_caption = m[0]
        message = await ctx.send(f'this will take some time {randomemoji}')

        if file:
            file = await caption_image(
                proxy_url=file.proxy_url,
                top_text=first_caption, bottom_text=second_caption, bot=self.bot)

            if file is not None:
                await message.edit(content=None, attachments=[file])
            else:
                await message.edit(content=f'something went wrong {self.bot.spongebob}')
            return

        elif a:
            if isinstance(a, discord.Embed):
                file = await caption_image(proxy_url=a.url, top_text=first_caption, bottom_text=second_caption,
                                           bot=self.bot)
                if file is not None:
                    await message.edit(content=None, attachments=[file])
                else:
                    await message.edit(content=f'something went wrong {self.bot.spongebob}')

                return
            file = await caption_image(proxy_url=a.proxy_url, top_text=first_caption, bottom_text=second_caption,
                                       bot=self.bot)

            if file is not None:
                await message.edit(content=None, attachments=[file])
            else:
                await message.edit(content=f'something went wrong {self.bot.spongebob}')
            return

        await message.edit(content=f'something went wrong {self.bot.spongebob}')

    @commands.command(name='ripple')
    @commands.cooldown(1, 3, BucketType.user)
    async def ripple(self, ctx: Context, file: typing.Optional[discord.Attachment]):
        a = await get_attachments(ctx=ctx)
        type = 'spin'
        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='cube')
    @commands.cooldown(1, 3, BucketType.user)
    async def cube(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)
        type = 'cube'
        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='sphere')
    @commands.cooldown(1, 3, BucketType.user)
    async def sphere(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'globe'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='burn')
    @commands.cooldown(1, 3, BucketType.user)
    async def brun(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'burn'
        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='boil')
    @commands.cooldown(1, 3, BucketType.user)
    async def boil(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'boil'
        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='bomb')
    @commands.cooldown(1, 3, BucketType.user)
    async def bomb(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'bomb'
        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='patpat')
    @commands.cooldown(1, 3, BucketType.user)
    async def patpat(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'patpat'
        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='shock')
    @commands.cooldown(1, 3, BucketType.user)
    async def shock(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'shock'
        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='canny')
    @commands.cooldown(1, 3, BucketType.user)
    async def canny(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'canny'
        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='fire')
    @commands.cooldown(1, 3, BucketType.user)
    async def fire(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'fire'
        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='balls')
    @commands.cooldown(1, 3, BucketType.user)
    async def balls(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'balls'
        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='infinity')
    @commands.cooldown(1, 3, BucketType.user)
    async def infinity(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'infinity'
        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='bubble')
    @commands.cooldown(1, 3, BucketType.user)
    async def bubble(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'bubble'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='cloth')
    @commands.cooldown(1, 3, BucketType.user)
    async def cloth(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'cloth'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='cow')
    @commands.cooldown(1, 3, BucketType.user)
    async def cow(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'cow'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='wall')
    @commands.cooldown(1, 3, BucketType.user)
    async def wall(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'wall'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command(name='paint')
    @commands.cooldown(1, 3, BucketType.user)
    async def paint(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'paint'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def ripple(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'ripple'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def blur(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'blur'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def cartoon(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'cartoon'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def shoot(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'shoot'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def tv(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'tv'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def print(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'print'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def matrix(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'matrix'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def sensitive(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'sensitive'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def dilate(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'dilate'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def pattern(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'pattern'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def logoff(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'logoff'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def fan(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'fan'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def cracks(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'cracks'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def endless(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'endless'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def spikes(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'spikes'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def blocks(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'blocks'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def phone(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'phone'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def laundry(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'laundry'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def shred(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'shred'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def poly(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'poly'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def lines(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'lines'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def ipcam(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'ipcam'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def reflection(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'reflection'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def kanye(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'kanye'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def letters(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'letters'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def wiggle(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'wiggle'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def paparazzi(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'paparazzi'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def math(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'equations'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def clock(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'clock'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def wrap(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'wrap'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def optics(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'optics'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def abstract(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'abstract'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def neon(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'neon'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)

    @commands.command()
    @commands.cooldown(1, 3, BucketType.user)
    async def flush(self, ctx: Context, file: typing.Optional[discord.Attachment]):

        a = await get_attachments(ctx=ctx)

        type = 'flush'

        if not file and not a:
            await ctx.send('give me something to edit must be image or gif')
            return
        if file:
            if not file.content_type.startswith('image'):
                await ctx.send('give me something to edit must be image or gif')
                return

        await handle_process(ctx, type, self.bot, file=file, embed=a)


async def setup(bot: pepebot) -> None:
    await bot.add_cog(
        creation(bot))
