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
        embed.set_author(name=f"{user.name}'s avatar", icon_url=user.display_avatar.url)
        embed.set_image(url=user.display_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command()
    async def banner(self, ctx: commands.Context, user: discord.User = None):
        """
        Display a user's banner.
        """ 
        user = user or ctx.author
        if not user.banner:
            return await ctx.send(f'{user} has no banner.')

        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f"{user.name}'s banner", icon_url=user.display_avatar.url)
        embed.set_image(url=user.banner.url)
        await ctx.send(embed=embed)
    
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
        embed = discord.Embed(description=f"I don't see how this will help you, but my ping is `{round(self.bot.latency * 1000)}ms`.", color=discord.Color.orange())
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(aliases=['si'])
    async def serverinfo(self, ctx: commands.Context):
        """
        Present server information.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_command(aliases=['ui'])
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """
        Present user information.
        """
        member = member or ctx.author
        embed = discord.Embed(title=f'{member}', color=discord.Color.random())
        embed.add_field(name='**Server join date**', value=f'{member.joined_at.strftime("%c")}')
        embed.add_field(name='**Account creation date**', value=f'{member.created_at.strftime("%c")}', inline=False)
        embed.add_field(name='**Discord ID**', value=f'{member.id}')
        if member.premium_since:
            embed.add_field(name='**Nitro boosting since**', value=f'{member.premium_since.strftime("%c")}', inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Public(bot))