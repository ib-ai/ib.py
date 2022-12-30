import discord
from discord.ext import commands


class ChannelOrder(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.hybrid_group(aliases=['co'])
    async def channelorder(self, ctx: commands.Context):
        """
        Commands for discord channel arrangement within categories.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @channelorder.command()
    async def snapshot(self, ctx: commands.Context):
        """
        Save the arrangement of channels in a category.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @channelorder.command(aliases=['r'])
    async def rollback(self, ctx: commands.Context):
        """
        Revert the arrangement of channels in a category.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelOrder(bot))