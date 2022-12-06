import discord
from discord.ext import commands


class Public(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.command(aliases=['av'])
    async def avatar(self, ctx: commands.Context):
        """
        Display a user's avatar.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.command()
    async def banner(self, ctx: commands.Context):
        """
        Display a user's banner.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.command()
    async def opt(self, ctx: commands.Context):
        """
        Toggle user's access to a channel.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.command()
    async def ping(self, ctx: commands.Context):
        """
        Measure latency.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.command(aliases=['si'])
    async def serverinfo(self, ctx: commands.Context):
        """
        Present server information.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.command(aliases=['ui'])
    async def userinfo(self, ctx: commands.Context):
        """
        Present user information.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Public(bot))