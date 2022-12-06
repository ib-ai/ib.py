import discord
from discord.ext import commands


class Voting(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, message: discord.Message):
        """
        Increment vote count when reaction is added.
        """
        pass

    @commands.Cog.listener()
    async def on_raw_reaction_delete(self, message: discord.Message):
        """
        Decrement vote count when reaction is deleted.
        """
        pass
    
    @commands.group()
    async def voteladder(self, ctx: commands.Context):
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @voteladder.command()
    async def channel(self, ctx: commands.Context):
        """
        Assign a channel to a voteladder.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @voteladder.command(aliases=['add'])
    async def create(self, ctx: commands.Context):
        """
        Create a voteladder.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @voteladder.command(aliases=['delete'])
    async def delete(self, ctx: commands.Context):
        """
        Delete a voteladder.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @voteladder.command()
    async def duration(self, ctx: commands.Context):
        """
        Assign a vote duration to a voteladder.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @voteladder.command()
    async def minimum(self, ctx: commands.Context):
        """
        Assign a minimum upvote count for passing to a voteladder.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @voteladder.command()
    async def role(self, ctx: commands.Context):
        """
        Assign a role to the voteladder.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @voteladder.command()
    async def threshold(self, ctx: commands.Context):
        """
        Assign a vote passing theshold to a voteladder.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @voteladder.command()
    async def list(self, ctx: commands.Context):
        """
        List available voteladders.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @commands.command()
    async def vote(self, ctx: commands.Context):
        """
        Hold a vote within a particular voteladder.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Voting(bot))