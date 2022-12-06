import discord
from discord.ext import commands


class Monitor(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Log messages that:
        - are from a monitored user.
        - match a monitor's pattern.
        """
        pass


    @commands.group()
    async def monitor(self, ctx: commands.Context):
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @monitor.group()
    async def channel(self, ctx: commands.Context):
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @channel.command()
    async def user(self, ctx: commands.Context):
        """
        Set logging channel for monitored users.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @channel.command()
    async def message(self, ctx: commands.Context):
        """
        Set logging channel for monitored message patterns.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')


    @monitor.command()
    async def cleanup(self, ctx: commands.Context):
        """
        Remove users that are no longer in the server.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @monitor.command()
    async def list(self, ctx: commands.Context):
        """
        List of monitored message patterns and monitored users.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')


    @monitor.group()
    async def message(self, ctx: commands.Context):
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @message.command(aliases=['add'])
    async def create(self, ctx: commands.Context):
        """
        Create a monitor for a message pattern.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @message.command(aliases=['remove'])
    async def delete(self, ctx: commands.Context):
        """
        Delete a monitor for a message pattern.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')

    
    @monitor.group()
    async def user(self, ctx: commands.Context):
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @user.command(aliases=['add'])
    async def create(self, ctx: commands.Context):
        """
        Create a monitor for a user.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @user.command(aliases=['remove'])
    async def delete(self, ctx: commands.Context):
        """
        Delete a monitor for a user.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Monitor(bot))