from typing import Union

import discord
from discord.ext import commands


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, message: discord.Message):
        """
        Increment vote count when reaction is added.
        """
        ...

    @commands.Cog.listener()
    async def on_raw_reaction_delete(self, message: discord.Message):
        """
        Decrement vote count when reaction is deleted.
        """
        ...


    @commands.hybrid_command()
    async def buttonroles(self, ctx: commands.Context):
        """
        Send a message with buttons that add roles.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @commands.hybrid_group()
    async def cassowary(self, ctx: commands.Context):
        """
        Commands for handling cassowaries.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @cassowary.command()
    async def create(self, ctx: commands.Context):
        """
        Create a cassowary.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @cassowary.command()
    async def delete(self, ctx: commands.Context):
        """
        Delete a cassowary.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @cassowary.command()
    async def list(self, ctx: commands.Context):
        """
        List all cassowaries.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')


    @commands.hybrid_command()
    async def giverole(self, ctx: commands.Context):
        """
        Assign a new role to all members with a specific role.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')


    @commands.hybrid_group()
    async def reaction(self, ctx: commands.Context):
        """
        Commands for handling reaction roles.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')

    
    @reaction.command(aliases=['add'])
    async def create(self, ctx: commands.Context):
        """
        Create a reaction role.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @reaction.command(aliases=['remove'])
    async def delete(self, ctx: commands.Context):
        """
        Delete a reaction role.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))