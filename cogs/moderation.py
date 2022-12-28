from typing import Union

import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.User, discord.Member]):
        """
        Publish ban to mod-log.
        """
        ...

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        Publish kick to mod-log.
        """
        ...

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """
        Publish unban to mod-log.
        """
        ...

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Publish mutes and unmutes to mod-log.
        """
        ...

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Log message edits.
        """
        ...

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """
        Log message deletes.
        """
        ...


    @commands.hybrid_command()
    async def logs(self, ctx: commands.Context):
        """
        Set a channel for log messages.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_command()
    async def moderators(self, ctx: commands.Context):
        """
        Set a role for moderators.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @commands.hybrid_group()
    async def modlog(self, ctx: commands.Context):
        """
        Commands for setting channels to publish punishment updates to.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @modlog.command()
    async def server(self, ctx: commands.Context):
        """
        Set a channel for punishment updates to be sent to publicly.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @modlog.command()
    async def staff(self, ctx: commands.Context):
        """
        Set a channel for punishment updates to be sent internally.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_command()
    async def muterole(self, ctx: commands.Context):
        """
        Set a role for mutes.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    
    @commands.hybrid_command()
    async def ban(self, ctx: commands.Context, user: discord.User, *, reason: str):
        """
        Ban a user (including those that are not in the server).
        """ 
        await ctx.guild.ban(user, reason=reason)
        await ctx.reply(f'Banned {user} for {reason}.', delete_after=5)
    
    @commands.hybrid_command()
    async def expire(self, ctx: commands.Context):
        """
        Set a duration for a punishment. Equivalently, schedule the revokement of a punishment.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_command()
    async def history(self, ctx: commands.Context):
        """
        Display a user's punishment history.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_command()
    async def lookup(self, ctx: commands.Context):
        """
        Retrieve punishment case by case number.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_command()
    async def note(self, ctx: commands.Context):
        """
        Save a note on a user.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.hybrid_group(invoke_without_command=False)
    async def purge(self, ctx: commands.Context):
        """
        Commands for bulk deletion.
        """
        pass
    
    @purge.command()
    async def message(self, ctx: commands.Context, number: int):
        """
        Bulk delete messages.
        """ 
        async for message in ctx.channel.history(limit=number):
            try:
                await message.delete()
            except: # Just in case Discord poops itself and the API returns an error, we don't want to crash the command.
                pass
        await ctx.reply(f'Deleted {number} messages.', delete_after=5)
    
    @purge.command()
    async def reaction(self, ctx: commands.Context, number: int):
        """
        Bulk delete reactions.
        """ 
        async for message in ctx.channel.history(limit=number):
            try:
                await message.clear_reactions()
            except:
                pass
        await ctx.reply(f'Cleared all reactions from the previous {number} messages.', delete_after=5)

    @commands.hybrid_command()
    async def reason(self, ctx: commands.Context):
        """
        Set a reason for a punishment case.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))