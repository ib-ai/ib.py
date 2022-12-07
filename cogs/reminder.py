import discord
from discord.ext import commands


class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.hybrid_group()
    async def reminder(self, ctx: commands.Context):
        """
        Commands for handling reminders.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @reminder.command(aliases=['add'])
    async def create(self, ctx: commands.Context):
        """
        Create a reminder.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @reminder.command(aliases=['remove'])
    async def delete(self, ctx: commands.Context):
        """
        Delete a reminder.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @reminder.command()
    async def list(self, ctx: commands.Context):
        """
        List your reminders.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))