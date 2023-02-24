"""
Peepbot main runner
~~~~~~~~~~~~~~~~~~~
starter of the peep bot for discord py
:copyright: (C) 2022-present xgreenapple
 (c) 2015 Rapptz
:license: MIT.
"""

from __future__ import annotations


import math

import discord
from discord.ui import Item

from datetime import timedelta
from typing import TYPE_CHECKING, Any, Dict, Optional, List

if TYPE_CHECKING:
    from pepebot import PepeBot
    from handler.context import Context


# errors

class PagesNotImplemented(Exception):
    pass


class PageSource:

    def __init__(self, data: List[any], max_per_page: int):
        self.last_index = 0
        self.first_index = 0
        self.data = data
        self.max_per_page = max_per_page
        self.current_page = 0
        self.current_entry = None
        self.max_pages = 0
        self.data_length = 0

    def initialise(
            self, data: List[any] = None, max_per_page: int = None
    ):
        if data is not None:
            self.data = data
        if max_per_page is not None:
            self.max_per_page = max_per_page
        self.data_length = len(self.data)
        self.max_pages = math.ceil(len(self.data) / self.max_per_page)
        self.get_page(0)

    def get_first_index(self):
        return self.current_page * self.max_per_page

    def get_last_index(self):
        return (self.current_page + 1) * self.max_per_page

    def get_page(self, page_num: int):
        self.current_page = page_num
        self.current_entry = self.get_entry()
        return self.current_entry

    def get_max_pages(self):
        return self.max_pages

    def get_current_entry(self):
        return self.current_entry

    def get_entry(self):
        self.first_index = self.get_first_index()
        self.last_index = self.get_last_index()
        return self.data[self.first_index:self.last_index]

    def clear(self):
        self.data = None
        self.current_entry = None
        self.current_page = 0
        self.max_pages = 0
        self.data_length = 0


class EmbedFormatter:
    def __init__(self, name: str):
        self.embed = discord.Embed(title=name)

    def get_formate_embed(
            self, current_page: int, max_pages: int, current_entry_num: int,
            entry: List[any]
    ):
        self.embed.description = "\n"
        formatted_value = []
        for i, value in enumerate(entry, start=current_entry_num + 1):
            formatted_value.append(self.formate_lines(i, value))
        self.embed.description = self.embed.description.join(formatted_value)
        self.embed.set_footer(text=f"page: {current_page + 1}/{max_pages}")
        return self.embed

    @staticmethod
    def formate_lines(current_index: int, value) -> str:
        return f"{current_index}: {value}"

    def clean(self):
        self.embed = discord.Embed()


class SimpleEmbedPages(PageSource):
    def __init__(
            self,
            bot: PepeBot,
            ctx: Context,
            formatter: Any[EmbedFormatter],
            data: List[any],
            max_per_page: int = 5,
            timeout: Optional[timedelta] = timedelta(seconds=180)
    ):
        super().__init__(data=data, max_per_page=max_per_page)
        self.bot = bot
        self.view_timeout = timeout
        self.ctx = ctx
        self.formatter = formatter
        self.embed = formatter.embed
        self.message: Optional[discord.Message] = None

    async def send(self):
        view = PepePages(
            page_source=self, timeout=self.view_timeout.seconds)
        await view.initialise()
        self.embed = view.load_embed()
        self.message = await self.ctx.send(embed=self.embed, view=view)
        view.message = self.message


class PepePages(discord.ui.View):
    def __init__(
            self,
            page_source: SimpleEmbedPages,
            timeout: float = 180
    ):
        super().__init__(timeout=timeout)
        self.bot = page_source.bot
        self.page_source = page_source
        self.current_page = 0
        self.message: Optional[discord.Message] = None
        self.embed = self.page_source.embed
        self.is_ready = False

    async def initialise(self):
        self.next.emoji = self.bot.emoji.right
        self.prev.emoji = self.bot.emoji.left
        self.last.emoji = self.bot.emoji.doubleright
        self.first.emoji = self.bot.emoji.doubleleft
        self.page_source.initialise()
        self.handle_button_state()
        self.is_ready = True

    @discord.ui.button(style=discord.ButtonStyle.blurple)
    async def prev(
            self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        previous_embed_page = self.get_prev_page()
        self.handle_button_state()
        await interaction.response.edit_message(
            embed=previous_embed_page, view=self)

    @discord.ui.button(style=discord.ButtonStyle.blurple)
    async def first(
            self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        first_embed_page = self.get_first_page()
        self.handle_button_state()
        await interaction.response.edit_message(
            embed=first_embed_page, view=self)

    @discord.ui.button(style=discord.ButtonStyle.blurple)
    async def last(
            self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        last_embed_page = self.get_last_page()
        self.handle_button_state()
        await interaction.response.edit_message(
            embed=last_embed_page, view=self
        )

    @discord.ui.button(style=discord.ButtonStyle.blurple)
    async def next(
            self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        next_embed_page = self.get_next_page()
        self.handle_button_state()
        await interaction.response.edit_message(
            embed=next_embed_page, view=self)

    def handle_button_state(self):
        max_indexes = self.page_source.max_pages
        current_index = self.current_page
        if current_index >= max_indexes - 1:
            if not self.next.disabled:
                self.next.disabled = True
            if not self.last.disabled:
                self.last.disabled = True
        else:
            if self.next.disabled:
                self.next.disabled = False
            if self.last.disabled:
                self.last.disabled = False
        if current_index <= 0:
            if not self.first.disabled:
                self.first.disabled = True
            if not self.prev.disabled:
                self.prev.disabled = True
        else:
            if self.first.disabled:
                self.first.disabled = False
            if self.prev.disabled:
                self.prev.disabled = False

    def load_embed(self):
        embed = self.page_source.formatter.get_formate_embed(
            self.current_page,
            self.page_source.max_pages,
            self.page_source.first_index,
            entry=self.page_source.get_current_entry())
        return embed

    def get_custom_page(self, page_num: int):
        self.current_page = page_num
        self.page_source.get_page(self.current_page)
        return self.load_embed()

    def get_next_page(self):
        self.current_page += 1
        self.page_source.get_page(self.current_page)
        return self.load_embed()

    def get_prev_page(self):
        self.current_page -= 1
        self.page_source.get_page(self.current_page)
        return self.load_embed()

    def get_first_page(self):
        self.current_page = 0
        self.page_source.get_page(self.current_page)
        return self.load_embed()

    def get_last_page(self):
        self.current_page = self.page_source.max_pages - 1
        self.page_source.get_page(self.current_page)
        return self.load_embed()

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)

    async def on_error(
            self, interaction: discord.Interaction, error: Exception,
            item: Item[Any]
    ) -> None:
        await interaction.response.send_message(
            "something went wrong", ephemeral=True)
