from typing import List, Tuple
import discord
from discord.ext import commands
from discord import ui

class Pagination(ui.View):
    def __init__(self, ctx: commands.Context, embeds: List[discord.Embed]):
        super().__init__(timeout = 60)
        self.ctx = ctx
        self.embeds = embeds
        self.current_page = 0

    @ui.button(emoji=u"\u23EA", style=discord.ButtonStyle.blurple)
    async def first_page(self, interaction: discord.Interaction, button):
        self.current_page = 0
        await self.update_page(interaction)
    
    @ui.button(emoji=u"\u2B05", style=discord.ButtonStyle.blurple)
    async def before_page(self, interaction: discord.Interaction, button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_page(interaction)
    
    @ui.button(emoji=u"\u27A1", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await self.update_page(interaction)
    
    @ui.button(emoji=u"\u23E9", style=discord.ButtonStyle.blurple)
    async def last_page(self, interaction: discord.Interaction, button):
        self.current_page = len(self.embeds) - 1
        await self.update_page(interaction)
    
    async def update_page(self, interaction: discord.Interaction):
        if self.current_page == 0:
            self.children[0].disabled = True
            self.children[1].disabled = True
            self.children[-1].disabled = False
            self.children[-2].disabled = False
        elif self.current_page == len(self.embeds) - 1:
            self.children[0].disabled = False
            self.children[1].disabled = False
            self.children[-1].disabled = True
            self.children[-2].disabled = True
        else:
            for i in self.children: i.disabled = False

        await interaction.response.edit_message(
            embed = self.embeds[self.current_page],
            view = self
        )

    async def return_paginated_embed_view(self) -> Tuple[discord.Embed, discord.ui.View | None]:
        if not self.embeds:
            no_data_embed = discord.Embed(description="No data available.")
            return [no_data_embed, None]

        if len(self.embeds) < 2: # Don't add buttons if there's only one embed
            for i in self.children:
                i.disabled = True

        return self.embeds[self.current_page], self
