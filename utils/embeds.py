from typing import List, Optional, Iterable, Union
from collections.abc import Collection
import discord

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
        name = name[:NAME_SIZE_LIMIT-3] + '...' if len(name) >NAME_SIZE_LIMIT else name
        value = value[:VALUE_SIZE_LIMIT-3] + '...' if len(value) > VALUE_SIZE_LIMIT else value
        current.add_field(name=name, value=value, inline=inline_field)
        items += 1
    embeds.append(current)
    for page, embed in enumerate(embeds):
        embed.set_footer(text=f"Page {page+1}/{pages}")

    return embeds


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