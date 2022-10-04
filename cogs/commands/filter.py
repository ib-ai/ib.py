from discord.ext import commands
from db.models import StaffFilter

from pagination.pagination import Pagination
from utils.ucommand import reply_unknown_syntax
from utils.uguild import assert_regex, get_guild_data, mods_or_manage_guild

class Filter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.group(invoke_without_command=True)
    @mods_or_manage_guild()
    @commands.guild_only()
    async def filter(self, ctx: commands.Context):
        await ctx.send(reply_unknown_syntax(ctx.command))
    
    @filter.command()
    @commands.has_guild_permissions(manage_guild=True)
    @commands.guild_only()
    async def toggle(self, ctx: commands.Context):
        guild_data = await get_guild_data(ctx.guild)

        try:
            await guild_data.update(filtering = not guild_data.filtering).apply()
        except Exception as e:
            print(e)
            return

        success_message = "disabled" if not guild_data.filtering else "enabled"
        
        await ctx.send("`filtering` has been successfully {}.".format(success_message))
    
    @filter.command(name='create', aliases=['add'])
    @mods_or_manage_guild()
    @commands.guild_only()
    async def filter_create(self, ctx: commands.Context, *, pattern: str):
        assert_regex(pattern)
        
        try:
            filtered_message = await StaffFilter.query.where(StaffFilter.trigger == pattern).gino.first()

            if filtered_message is not None:
                await ctx.send("The pattern (`{}`) is already being filtered.".format(pattern))
                return

            filtered_message = StaffFilter(trigger=pattern)
            await filtered_message.create()
        except Exception as e:
            print(e)
            
        await ctx.send("The pattern (`{}`) has been successfully added to filter.".format(pattern))
    
    @filter.command(name='remove', aliases=['delete'])
    @mods_or_manage_guild()
    @commands.guild_only()
    async def filter_remove(self, ctx: commands.Context, *, pattern: str):
        try:
            filtered_message = await StaffFilter.query.where(StaffFilter.trigger == pattern).gino.first()

            if filtered_message is None:
                await ctx.send("The pattern (`{}`) is not being filtered.".format(pattern))
                return

            await filtered_message.delete()
        except Exception as e:
            print(e)

        await ctx.send("The pattern (`{}`) has been successfully removed from filter.".format(pattern))

    @filter.command(name='notify')
    @mods_or_manage_guild()
    @commands.guild_only()
    async def filter_notify(self, ctx: commands.Context, *, pattern: str):
        filtered_message = await StaffFilter.query.where(StaffFilter.trigger == pattern).gino.first()

        if filtered_message is None:
            await ctx.send("The filter (`{}`) does not exist.".format(pattern))
            return
        
        try:
            await filtered_message.update(notify = not filtered_message.notify).apply()
        except Exception as e:
            print(e)
            return
        
        success_message = "disabled" if not filtered_message.notify else "enabled"
        
        await ctx.send("Notifying for filter (`{}`) has been successfully {}.".format(pattern, success_message))

    @filter.command()
    @mods_or_manage_guild()
    @commands.guild_only()
    async def list(self, ctx: commands.Context):
        formatted_messages = [pattern.trigger for pattern in await StaffFilter.query.gino.all()]

        filter_embed, filter_view = Pagination(ctx, formatted_messages, "Here is a list of entries.", 10).return_paginated_embed()

        await ctx.send(embed=filter_embed, view=filter_view)
    
    async def cog_command_error(self, ctx, error: commands.CommandError):
        # ! More robust error checking
        await ctx.send(error)

async def setup(bot: commands.Bot):
    await bot.add_cog(Filter(bot))