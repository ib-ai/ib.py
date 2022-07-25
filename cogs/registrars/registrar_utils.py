from discord.ext import commands
import discord

class RegistrarUtils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    @commands.guild_only()
    async def ping(self, ctx: commands.Context):
        await ctx.send("Pong! Latency is currently {}ms for WebSocket.".format(round(self.bot.latency * 1000)))

    @commands.command(aliases=['si'])
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context):
        embed = discord.Embed() \
            .set_author(name=ctx.guild.name) \
            .set_thumbnail(url=str(ctx.guild.icon_url))

        embed.add_field(name="Owner",  value=ctx.guild.owner.mention, inline=True) \
            .add_field(name="Creation Date", value="<t:{}>".format(round(ctx.guild.created_at.timestamp())), inline=True) \
            .add_field(name="Voice Region", value=ctx.guild.region, inline=True) \
            .add_field(name="# of Members", value=ctx.guild.member_count, inline=True) \
            .add_field(name="# of Bots", value=len(list(filter(lambda member: member.bot, ctx.guild.members))), inline=True) \
            .add_field(name="Currently Online", value=len(list(filter(lambda member: member.status != discord.Status.offline, ctx.guild.members))), inline=True) \
            .add_field(name="# of Roles", value=len(ctx.guild.roles), inline=True) \
            .add_field(name="# of Channels", value=len(ctx.guild.channels), inline=True) 

        await ctx.channel.send(embed=embed)
        
def setup(bot: commands.Bot):
    bot.add_cog(RegistrarUtils(bot))