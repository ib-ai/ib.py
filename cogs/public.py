import discord
from discord.ext import commands
from discord.app_commands import describe

from utils.commands import available_subcommands

class Public(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.hybrid_group()
    async def avatar(self, ctx: commands.Context):
        """
        Display a user's avatar.
        """
        await available_subcommands(ctx)

    @avatar.command()
    @describe(member='The user to display the avatar of.')
    async def guild(self, ctx: commands.Context, member: discord.Member = None):
        """
        Display a user\'s guild-specific avatar, if available.
        """ 
        member = member or ctx.author

        if not member.guild_avatar:
            return await ctx.send(f'{member} has no guild avatar.')

        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f"{member.name}'s avatar")
        embed.set_image(url=member.guild_avatar.url)
        await ctx.send(embed=embed)

    @avatar.command(name='global')
    @describe(member='The user to display the avatar of.')
    async def _global(self, ctx: commands.Context, member: discord.Member = None):
        """
        Display a user\'s global avatar.
        """
        member = member or ctx.author
        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_author(name=f"{member.name}'s avatar")
        embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await ctx.send(embed=embed)
    
    @commands.hybrid_command()
    @describe(user='The user to display the banner of.')
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
        embed = discord.Embed(title=f"{ctx.guild.name} ({ctx.guild.id})", color=discord.Color.green())
        creation_date = ctx.guild.created_at
        # unix timestamp
        timestamp = discord.utils.format_dt(creation_date, style="F")
        relative = discord.utils.format_dt(creation_date, style="R")
        embed.add_field(name="**Creation Date**", value=f"{timestamp} ({relative})", inline=False)

        num_boosts = ctx.guild.premium_subscription_count
        embed.add_field(name="**Boosts**", value=f"{num_boosts}")
        embed.add_field(name="**Verification Level**", value=f"{str(ctx.guild.verification_level).capitalize()}")
        embed.add_field(name="**Owner**", value=f"{ctx.guild.owner.name}")

        txt = len(ctx.guild.text_channels)
        vc = len(ctx.guild.voice_channels)
        ctg = len(ctx.guild.categories)
        stg = len(ctx.guild.stage_channels)
        frm = len(ctx.guild.forums)
        total = txt + vc + ctg + stg + frm
        embed.add_field(name="**Channels**", value=f"{txt} text, {vc} voice, {ctg} categories, {stg} stage, {frm} forum. {total} total.", inline=False)

        guild = await self.bot.fetch_guild(ctx.guild.id, with_counts=True)
        online = guild.approximate_presence_count
        members = guild.approximate_member_count
        embed.add_field(name="**Members**", value=f"{online} online, {members} total.")

        num_roles = len(ctx.guild.roles)
        embed.add_field(name="**Roles**", value=f"{num_roles}")

        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)
        
    @commands.hybrid_command(aliases=['ui'])
    @describe(member='The user to display the information of.')
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """
        Present user information.
        """
        member = member or ctx.author
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=f'{member.name}\'s information', icon_url=member.display_avatar.url)
        embed.add_field(name='**Nickname**', value=f'{member.display_name}', inline=False)
        embed.add_field(name='**Server join date**', value=f'{member.joined_at.strftime("%c")}')
        embed.add_field(name='**Account creation date**', value=f'{member.created_at.strftime("%c")}', inline=False)
        embed.add_field(name='**Discord ID**', value=f'{member.id}')
        embed.add_field(name='**Status**', value=f'{member.status}')
        roles = [role.mention for role in member.roles if not role.is_default()]
        if roles:
            rolestext = ', '.join(roles)
        else:
            rolestext = 'No roles'
        embed.add_field(name='**Roles**', value=rolestext, inline=False)
        if member.premium_since:
            embed.add_field(name='**Nitro boosting since**', value=f'{member.premium_since.strftime("%c")}', inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Public(bot))