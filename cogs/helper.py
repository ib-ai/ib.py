import discord
from discord.ext import commands


class Helper(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Update helper message based on user helper/dehelper.
        """
        pass
    
    @commands.hybrid_command()
    async def helpermessage(self, ctx: commands.Context):
        """
        Send an updating list of helpers for a subject.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_command()
    async def pin(self, ctx: commands.Context):
        """
        Pin a message to a channel.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_command()
    async def unpin(self, ctx: commands.Context):
        """
        Unpin a message from a channel.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Helper(bot))