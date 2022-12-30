from typing import List, Tuple
import discord
from discord.ext import commands
from discord import ui

class Pagination(ui.View):
    """
    A class that handles pagination of embeds using Discord buttons.
    """
    def __init__(self, ctx: commands.Context, embeds: List[discord.Embed]):
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

    async def return_paginated_embed_view(self) -> Tuple[discord.Embed, discord.ui.View | None]:
        """
        Returns the first embed and containing view.
        """
        if not self.embeds:
            no_data_embed = discord.Embed(description="No data available.")
            return [no_data_embed, None]

        self.update_buttons() # Disable buttons if there's only one embed

        return self.embeds[self.current_page], self
