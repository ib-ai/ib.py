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
    async def giverole(self, ctx: commands.Context, existing_role: discord.Role = None, new_role: discord.Role = None):
        """
        Assign a new role to all members with a specific role.
        """
        if existing_role is None or new_role is None:
            return await ctx.send("Please provide both the existing and new role.")
        role_members = [member for member in ctx.guild.members if existing_role in member.roles]
        for member in role_members:
            try:
                await member.add_roles(new_role)
            except discord.Forbidden:
                return await ctx.send("I do not have permission to add roles to members.")
            except discord.HTTPException:
                await ctx.send(f"Could not add role to {member.name}")
        await ctx.send("Successfully added roles.")

    @commands.hybrid_command()
    async def roleswap(self, ctx: commands.Context, existing_role: discord.Role = None, new_role: discord.Role = None):
        """
        Assigns a new role and takes old role from all members with a specific role.
        """
        if existing_role is None or new_role is None:
            return await ctx.send("Please provide both the existing and new role.")
        role_members = [member for member in ctx.guild.members if existing_role in member.roles]
        for member in role_members:
            try:
                await member.remove_roles(existing_role)
                await member.add_roles(new_role)
            except discord.Forbidden:
                return await ctx.send("I do not have permission to remove/add roles to members.")
            except discord.HTTPException:
                await ctx.send(f"Could not add/remove role for {member.name}")
        await ctx.send("Successfully swapped roles.")

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