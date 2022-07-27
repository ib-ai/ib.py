import discord
from discord.ext import commands
import asyncio

class Pagination():
    def __init__(self, ctx: commands.Context, description, entries, step = 10):
        self.ctx = ctx
        self.entries = entries
        self.description = description
        self.step = step
        self.embeds = []
    
    def build_field(self, embed: discord.Embed, index, value):
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

    async def send_paginated_embed(self):
        self.build_embed()

        buttons = [u"\u23EA", u"\u2B05", u"\u27A1", u"\u23E9"]
        current = 0
        message = await self.ctx.send(embed=self.embeds[current])
        
        for button in buttons:
            await message.add_reaction(button)
            
        while True:
            try:
                reaction, user = await self.ctx.bot.wait_for("reaction_add", check=lambda reaction, user: user == self.ctx.author and reaction.emoji in buttons, timeout=60.0)

            except asyncio.TimeoutError:
                await message.clear_reactions()

                timed_out_embed = discord.Embed(description="Embed has timed out.")
                await message.edit(embed=timed_out_embed)

            else:
                previous_page = current
                if reaction.emoji == u"\u23EA":
                    current = 0
                    
                elif reaction.emoji == u"\u2B05":
                    if current > 0:
                        current -= 1
                        
                elif reaction.emoji == u"\u27A1":
                    if current < len(self.embeds)-1:
                        current += 1

                elif reaction.emoji == u"\u23E9":
                    current = len(self.embeds) - 1

                for button in buttons:
                    await message.remove_reaction(button, self.ctx.author)

                if current != previous_page:
                    await message.edit(embed=self.embeds[current])