from typing import Union

import discord
from discord.ext import commands
from discord.app_commands import describe

from db.cached import get_guild_data

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
        utilities = f"[21 Jump Street]({after.jump_url})\n" \
                  + f"User: {after.author.mention}"
        embed_data = dict(
            author = dict(
                name = f'{after.author.name}#{after.author.discriminator} (ID: {after.author.id}) edited in #{after.channel.name}',
            ),
            color = discord.Colour.yellow().value,
            fields = [
                dict(name="From", value=before.content),
                dict(name="To", value=after.content),
                dict(name="Utilities", value=utilities)
            ]
        )
        embed = discord.Embed.from_dict(embed_data)

        guild_data = await get_guild_data(guild_id=after.guild.id)
        if not guild_data:
            return
        
        log_channel = self.bot.get_channel(guild_data.logs_id)
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """
        Log message deletes.
        """
        utilities = f"User: {message.author.mention}"
        embed_data = dict(
            author = dict(
                name = f'{message.author.name}#{message.author.discriminator} (ID: {message.author.id}) edited in #{message.channel.name}',
            ),
            color = discord.Colour.red().value,
            description = message.content,
            fields = [
                dict(name="Utilities", value=utilities)
            ]
        )
        embed = discord.Embed.from_dict(embed_data)

        guild_data = await get_guild_data(guild_id=message.guild.id)
        if not guild_data:
            return
        
        log_channel = self.bot.get_channel(guild_data.logs_id)
        await log_channel.send(embed=embed)


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
    
    @commands.group(invoke_without_command=True)
    async def purge(self, ctx: commands.Context):
        """
        Commands for bulk deletion.
        """
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