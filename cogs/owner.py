from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from typing import TYPE_CHECKING
from handler.pagination import SimpleEmbedPages, EmbedFormatter
if TYPE_CHECKING:
    from pepebot import PepeBot
    from handler.context import Context


async def setup(bot: PepeBot):
    await bot.add_cog(Config(bot))


class Config(commands.Cog):
    def __init__(self, bot: PepeBot):
        self.bot = bot

    async def cog_check(self, ctx: Context) -> bool:
        if await ctx.bot.is_owner(ctx.author):
            return True
        raise commands.NotOwner()

    @staticmethod
    def is_owner(interaction: discord.Interaction):
        return interaction.client.application.owner.id == interaction.user.id

    botconfig = app_commands.Group(
        name="botconfig",
        guild_ids=[939208771929014372],
        description="commands to manage the bot"
    )

    @botconfig.command(name="cog_reload")
    async def reload_cog(self):
        ...

    @botconfig.command(name="cog_load")
    async def load_cog(self) -> None:
        ...

    @botconfig.command(name="cog_remove")
    async def cog_remove(self):
        ...

    @commands.command(name="get_logs")
    @commands.is_owner()
    async def send_logs(self, ctx: Context, lines_lentgh: int = 500, to_channel=False, file=False):
        file = discord.File(fp=f"{self.bot.logger.filename}")
        lines = [line.decode('utf-8') for line in file.fp.readlines()]
        pages = SimpleEmbedPages(
            bot=self.bot, ctx=ctx, formatter=EmbedFormatter(name="logs"),
            data=lines, max_per_page=5
        )

        await pages.send()
        await ctx.send(file=file)




