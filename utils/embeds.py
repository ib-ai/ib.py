from typing import List, Optional
import discord

class EmbedGenerator():
    def __init__(self, entries: List, title: Optional[str] = "", description: Optional[str] = "", step: Optional[int] = 10):
       self.entries = entries
       self.title = title
       self.description = description
       self.step = step

    def build_field(self, embed: discord.Embed, index: int, value: str):
        value = f'{value:.512}{"..." if len(value) > 512 else ""}'
        embed.add_field(name=f"Entry #{index}", value=value, inline=False)

    def build_embed(self) -> List[discord.Embed]:
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