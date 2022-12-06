import discord
from discord.ext import commands


class Tags(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Respond to tags.
        """
        pass
    
    @commands.group()
    async def tag(self, ctx: commands.Context):
        """
        Commands for handling tags.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @tag.command(aliases=['add'])
    async def create(self, ctx: commands.Context):
        """
        Create a tag.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @tag.command(aliases=['remove'])
    async def delete(self, ctx: commands.Context):
        """
        Delete a tag.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @tag.command()
    async def find(self, ctx: commands.Context):
        """
        Find tags that match a pattern.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @tag.command()
    async def list(self, ctx: commands.Context):
        """
        List of all tags.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @tag.command()
    async def toggle(self, ctx: commands.Context):
        """
        Toggle if a tag is active.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Tags(bot))