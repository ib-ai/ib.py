import discord
from discord.ext import commands


class Embeds(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.command()
    async def embed(self, ctx: commands.Context):
        """
        Interactively construct a Discord embed.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.command()
    async def embedraw(self, ctx: commands.Context):
        """
        Create a Discord embed via raw JSON input.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Embeds(bot))