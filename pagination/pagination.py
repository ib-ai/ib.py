from typing import Tuple
import discord
from discord.ext import commands
from discord import ui

from utils.uguild import truncate

class Pagination(ui.View):
    def __init__(self, ctx: commands.Context, entries, description = "", step = 10):
        super().__init__(timeout = 60)
        self.ctx = ctx
        self.entries = entries
        self.description = description
        self.step = step
        self.embeds = []
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
    
    def build_field(self, embed: discord.Embed, index, value):
        value = truncate(value, 512)
        embed.add_field(name="Entry #{}".format(index), value=value, inline=False)

    def build_embed(self):
        embed = discord.Embed(description=self.description)

        for index, value in enumerate(self.entries):
            if index != 0 and index % self.step == 0:
                self.embeds.append(embed)
                embed = discord.Embed(description=self.description)
            
            self.build_field(embed, index + 1, value)

        self.embeds.append(embed)

        for index, selected_embed in enumerate(self.embeds):
            selected_embed.set_footer(text="Page {}/{}".format(index + 1, len(self.embeds)))

    async def return_paginated_embed(self) -> Tuple[discord.Embed, discord.ui.View | None]:
        if not self.entries:
            no_data_embed = discord.Embed(description="No data available.")
            return [no_data_embed, None]

        self.build_embed()

        if len(self.embeds) < 2: # Don't add reactions if there's only one embed
            for i in self.children:
                i.disabled = True

        return self.embeds[self.current_page], self

       