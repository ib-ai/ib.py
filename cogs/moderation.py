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
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        Publish kick to mod-log.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """
        Publish unban to mod-log.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Publish mutes and unmutes to mod-log.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Log message edits.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """
        Log message deletes.
        """
        raise NotImplementedError('Command requires implementation and permission set-up.')


    @commands.command()
    async def logs(self, ctx: commands.Context):
        """
        Set a channel for log messages.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.command()
    async def moderators(self, ctx: commands.Context):
        """
        Set a role for moderators.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @commands.group()
    async def modlog(self, ctx: commands.Context):
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
    
    @commands.command()
    async def muterole(self, ctx: commands.Context):
        """
        Set a role for mutes.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    
    @commands.command()
    async def blacklist(self, ctx: commands.Context):
        """
        Ban a user that is not in the server.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.command()
    async def expire(self, ctx: commands.Context):
        """
        Set a duration for a punishment. Equivalently, schedule the revokement of a punishment.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.command()
    async def history(self, ctx: commands.Context):
        """
        Display a user's punishment history.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.command()
    async def lookup(self, ctx: commands.Context):
        """
        Retrieve punishment case by case number.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.command()
    async def note(self, ctx: commands.Context):
        """
        Save a note on a user.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @commands.group()
    async def purge(self, ctx: commands.Context):
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @purge.command()
    async def message(self, ctx: commands.Context):
        """
        Bulk delete messages.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
    
    @purge.command()
    async def reaction(self, ctx: commands.Context):
        """
        Bulk delete reactions.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

    @commands.command()
    async def reason(self, ctx: commands.Context):
        """
        Set a reason for a punishment case.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))