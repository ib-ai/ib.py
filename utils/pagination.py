from typing import Union, Optional
from collections.abc import Collection

import discord
from discord import ui
from discord.ext import commands

from utils.misc import truncate



NAME_SIZE_LIMIT = 256
VALUE_SIZE_LIMIT = 1024
def paginated_embed_menus(
        names: Collection[str],
        values: Collection[str],
        pagesize: int = 10,
        *,
        inline: Union[Collection[bool], bool] = False,
        embed_dict: Optional[dict] = None,
        empty_desc: str = 'No entries found.',
    ) -> Collection[discord.Embed]:
    """
    Generates embeds for a paginated embed view.

    Parameters
    ----------
    names: Collection[str]
        Names of fields to be added/paginated.
    values: Collection[str]
        Values of fields to be added/paginated.
    pagesize: int = 10
        Maximum number of items per page.
    inline: Union[Collection[bool], bool] = True
        Whether embed fields should be inline or not.
    embed_dict: Optional[dict] = None
        Partial embed dictionary (for setting a title, description, etc.). Footer and fields must not be set.
    empty_desc: str = 'No entries found.'
        Description to be set when names/values is empty.
    """
    N = len(names)
    if N != len(values): raise ValueError('names and values for paginated embed menus must be of equal length.')
    if isinstance(inline, bool):
        inline = [inline]*N
    elif N != len(inline): raise ValueError('"inline" must be boolean or a collection of booleans of equal length to names/values for paginated embed menus.')

    if embed_dict:
        if 'title' in embed_dict and len(embed_dict['title']) > 256: raise ValueError('title cannot be over 256 characters')
        if 'desription' in embed_dict and len(embed_dict['desription']) > 4096: raise ValueError('desription cannot be over 4096 characters')
        if 'footer' in embed_dict: raise ValueError('embed_dict "footer" key must not be set.')
        if 'fields' in embed_dict: raise ValueError('embed_dict "fields" key must not be set.')
    else:
        embed_dict = {  # default
            'description': 'Here is a list of entries.'
        }
    
    if N == 0:
        embed_dict['description'] = empty_desc
        return [discord.Embed.from_dict(embed_dict)]

    embeds: Collection[discord.Embed] = []
    current: discord.Embed = discord.Embed.from_dict(embed_dict)
    pages = 1
    items = 0
    for name, value, inline_field in zip(names, values, inline):
        if items == pagesize or len(current) + len(name) + len(value) > 5090:  # leave 10 chars for footers
            embeds.append(current)
            current = discord.Embed.from_dict(embed_dict)
            pages += 1
            items = 0

        name = truncate(name, NAME_SIZE_LIMIT)
        value = truncate(value, VALUE_SIZE_LIMIT)
        current.add_field(name=name, value=value, inline=inline_field)
        items += 1
    embeds.append(current)
    for page, embed in enumerate(embeds):
        embed.set_footer(text=f"Page {page+1}/{pages}")

    return embeds


class PaginationView(ui.View):
    """
    A class that handles pagination of embeds using Discord buttons.
    """
    def __init__(self, ctx: commands.Context, embeds: Collection[discord.Embed]):
        """
        Parameters
        ----------
        ctx : commands.Context
            Context of the command.
        embeds : List[discord.Embed]
            List of embeds to be paginated. Supplied from `EmbedGenerator`.

        Attributes
        ----------
        current_page : int
            Current page index.
        """
        super().__init__(timeout = 60)
        self.ctx = ctx
        self.embeds = embeds
        self.current_page = 0

    @ui.button(emoji=u"\u23EA", style=discord.ButtonStyle.blurple)
    async def first_page(self, interaction: discord.Interaction, _):
        """
        Goes to the first page.
        """
        self.current_page = 0
        self.update_buttons()
        await self.update_view(interaction)
    
    @ui.button(emoji=u"\u2B05", style=discord.ButtonStyle.blurple)
    async def before_page(self, interaction: discord.Interaction, _):
        """
        Goes to the previous page.
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await self.update_view(interaction)
    
    @ui.button(emoji=u"\u27A1", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, _):
        """
        Goes to the next page.
        """
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            self.update_buttons()
            await self.update_view(interaction)
    
    @ui.button(emoji=u"\u23E9", style=discord.ButtonStyle.blurple)
    async def last_page(self, interaction: discord.Interaction, _):
        """
        Goes to the last page.
        """
        self.current_page = len(self.embeds) - 1
        self.update_buttons()
        await self.update_view(interaction)

    def update_buttons(self):
        """
        Updates the buttons based on the current page.
        """
        for i in self.children: i.disabled = False
        if self.current_page == 0:
            self.children[0].disabled = True
            self.children[1].disabled = True
        if self.current_page == len(self.embeds) - 1:
            self.children[-1].disabled = True
            self.children[-2].disabled = True

    async def update_view(self, interaction: discord.Interaction):
        """
        Updates the embed and view.
        """
        await interaction.response.edit_message(
            embed = self.embeds[self.current_page],
            view = self
        )

    async def return_paginated_embed_view(self) -> tuple[discord.Embed, discord.ui.View | None]:
        """
        Returns the first embed and containing view.
        """
        if not self.embeds:
            no_data_embed = discord.Embed(description="No data available.")
            return [no_data_embed, None]

        self.update_buttons() # Disable buttons if there's only one embed

        return self.embeds[self.current_page], self
