import discord
from discord.ext import commands


class Filter(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Delete messages that match a filter's pattern.
        """
        pass


    @commands.group()
    async def filter(self, ctx: commands.Context):
        """
        Commands for filtering unwanted message patterns.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @filter.command(aliases=['add'])
    async def create(self, ctx: commands.Context):
        """
        Create a filter.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @filter.command(aliases=['remove'])
    async def delete(self, ctx: commands.Context):
        """
        Delete a filter.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @filter.command()
    async def list(self, ctx: commands.Context):
        """
        List all filters.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @filter.command()
    async def notify(self, ctx: commands.Context):
        """
        Toggle if a filter triggers a ping.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @filter.command()
    async def toggle(self, ctx: commands.Context):
        """
        Toggle if a filter is active.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Filter(bot))