import discord
from discord.ext import commands


class Public(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.hybrid_command(aliases=['av'])
    async def avatar(self, ctx: commands.Context, user: discord.User = None):
        """
        Display a user's avatar.
        """ 
        user = user or ctx.author
        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f'{user.name}\'s avatar', icon_url=user.display_avatar.url)
        embed.set_image(url=user.display_avatar.url)
    
    @commands.hybrid_command()
    async def banner(self, ctx: commands.Context, user: discord.User = None):
        """
        Display a user's banner.
        """ 
        user = user or ctx.author
        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f'{user.name}\'s banner', icon_url=user.display_avatar.url)
        embed.set_image(url=user.banner.url if user.banner else None)
    
    @commands.hybrid_command()
    async def opt(self, ctx: commands.Context):
        """
        Toggle user's access to a channel.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_command()
    async def ping(self, ctx: commands.Context):
        """
        Measure latency.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_command(aliases=['si'])
    async def serverinfo(self, ctx: commands.Context):
        """
        Present server information.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_command(aliases=['ui'])
    async def userinfo(self, ctx: commands.Context):
        """
        Present user information.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Public(bot))