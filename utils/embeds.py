from typing import List, Optional
import discord

class EmbedGenerator():
    """
    A class that generates embeds from a list of entries.
    """
    def __init__(self, entries: List, title: Optional[str] = "", description: Optional[str] = "", step: Optional[int] = 10):
        """
        Parameters
        ----------
        entries : List
            List of entries to be displayed in the embed. Usually a list of strings.
        title : Optional[str]
            Title of the embed.
        description : Optional[str]
            Description of the embed.
        step : Optional[int]
            Number of entries to be displayed per embed (default 10). 
        """
        self.entries = entries
        self.title = title
        self.description = description
        self.step = step
    
    @staticmethod
    def build_field(embed: discord.Embed, index: int, value: str):
        """
        Builds a field for the embed.

        Parameters
        ----------
        embed : discord.Embed
            Embed to add the field to.
        index : int
            Index of the entry.
        value : str
            Value of the entry.
        """
        value = f'{value:.512}{"..." if len(value) > 512 else ""}'
        embed.add_field(name=f"Entry #{index}", value=value, inline=False)

    def build_embed(self) -> List[discord.Embed]:
        """
        Builds embeds with specified step and returns list of embeds.
        """
        if not self.entries:
            return [discord.Embed(title=self.title, description="No entries found.")]

        embeds: List[discord.Embed] = []
        
        split_items = [self.entries[i:i + self.step] for i in range(0, len(self.entries), self.step)]

        for embed_index, slice in enumerate(split_items):
            embed = discord.Embed(title=self.title, description=self.description)

            for index, value in enumerate(slice):
                self.build_field(embed, (self.step * embed_index) + index + 1, value)

            embed.set_footer(text=f"Page {embed_index + 1}/{len(split_items)}")

            embeds.append(embed)

        return embeds