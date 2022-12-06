import discord
from discord.ext import commands


class Updates(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.group()
    async def update(self, ctx: commands.Context):
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @update.command()
    async def set(self, ctx: commands.Context):
        """
        Set an updates channel.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @update.command(aliases=['add'])
    async def create(self, ctx: commands.Context):
        """
        Create an update entry.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @update.command(aliases=['remove'])
    async def delete(self, ctx: commands.Context):
        """
        Delete an update entry.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Updates(bot))