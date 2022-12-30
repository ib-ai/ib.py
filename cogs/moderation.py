from typing import Union

import discord
from discord.ext import commands
from discord.app_commands import describe

from utils.commands import available_subcommands


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
    @describe(user='User to ban', reason='Reason for ban')
    async def blacklist(self, ctx: commands.Context, user: discord.User, *, reason: str):
        """
        Blacklist a user that is not in the server.
        """ 
        if user in ctx.guild.members:
            await ctx.send("User is in the server. Please use Discord's built-in moderation tools.")
            return

        await ctx.guild.ban(user, reason=reason)
        await ctx.send(f'Banned {user} for `{reason}`.')
    
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
    
    @commands.group()
    async def purge(self, ctx: commands.Context):
        """
        Commands for bulk deletion.
        """
        if not ctx.invoked_subcommand:
            await available_subcommands(ctx)
    
    @purge.command()
    async def message(self, ctx: commands.Context, number: int):
        """
        Bulk delete messages.
        """ 
        async for message in ctx.channel.history(limit=number):
            try:
                await message.delete()
            except discord.Forbidden:
                await ctx.send('I do not have permission to delete messages.')
                return
            except discord.HTTPException:
                await ctx.send('An error occurred while deleting messages.')
                return
        await ctx.send(f'Deleted {number} messages.', delete_after=5)
    
    @purge.command()
    async def reaction(self, ctx: commands.Context, channel: discord.TextChannel, message_id: int, emoji: discord.Emoji):
        """
        Bulk delete reactions.
        """ 
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send('Message not found.')
            return
        except discord.Forbidden:
            await ctx.send('I do not have permission to read messages in that channel.')
            return
        except discord.HTTPException:
            await ctx.send('An error occurred while fetching the message.')
            return

        try:
            await message.clear_reaction(emoji)
        except discord.Forbidden:
            await ctx.send('I do not have permission to delete reactions.')
            return
        except discord.NotFound:
            await ctx.send('The emoji you specifiied was not found.')
            return
        except TypeError:
            await ctx.send('The emoji you specified is invalid.')
            return
        except discord.HTTPException:
            await ctx.send('An error occurred while deleting reactions.')
            return
        
        await ctx.send(f'Deleted reactions to {message_id} with emoji {emoji}.')

    @commands.hybrid_command()
    async def reason(self, ctx: commands.Context):
        """
        Set a reason for a punishment case.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))