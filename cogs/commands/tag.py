from discord.ext import commands
import discord
from db.models import StaffTag

from pagination.pagination import Pagination
from utils.ucommand import reply_unknown_syntax
from utils.uguild import assert_length, assert_regex, mods_or_manage_guild

class TagListPagination(Pagination):
    def build_field(self, embed: discord.Embed, _, value):
        embed.add_field(name=value['trigger'], value=value['value'], inline=False)

class TagFindPagination(Pagination):
    def build_field(self, embed: discord.Embed, _, value):
        embed.add_field(name="Here is a list of similar tags.", value=value, inline=False)

class Tag(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.group(invoke_without_command=True)
    @mods_or_manage_guild()
    @commands.guild_only()
    async def tag(self, ctx: commands.Context):
        await ctx.send(reply_unknown_syntax(ctx.command))
    
    @tag.command(name='create', aliases=['add'])
    @mods_or_manage_guild()
    @commands.guild_only()
    async def tag_create(self, ctx: commands.Context, trigger: str, value: str):
        assert_regex(trigger)
        assert_length(trigger, 256, "The tag trigger is too long. It is currently {} characters long (must be a maximum of 256).".format(len(trigger)))
        assert_length(value, 1024, "The tag value is too long. It is currently {} characters long (must be a maximum of 1024).".format(len(value)))

        try:
            tag = StaffTag(trigger=trigger, output=value, disabled=False)
            await tag.create()
        except Exception as e:
            print(e)
            
        await ctx.send("Consider it done: `{}` -> `{}`.".format(trigger, value))
    
    @tag.command(name='remove', aliases=['delete'])
    @mods_or_manage_guild()
    @commands.guild_only()
    async def tag_remove(self, ctx: commands.Context, *, trigger: str):
        try:
            tag = await StaffTag.query.where(StaffTag.trigger == trigger).gino.first()

            if tag is None:
                await ctx.send("The tag (`{}`) does not exist.".format(trigger))
                return

            await tag.delete()
        except Exception as e:
            print(e)

        await ctx.send("The tag has been removed.")
    
    @tag.command(name='toggle')
    @mods_or_manage_guild()
    @commands.guild_only()
    async def tag_toggle(self, ctx: commands.Context, *, trigger: str):
        try:
            tag = await StaffTag.query.where(StaffTag.trigger == trigger).gino.first()

            if tag is None:
                await ctx.send("The tag (`{}`) does not exist.".format(trigger))
                return

            await tag.update(disabled = not tag.disabled).apply()
        except Exception as e:
            print(e)
            return

        success_message = "disabled" if not tag.disabled else "enabled"
        
        await ctx.send("The tag (`{}`) has been successfully {}.".format(trigger, success_message))

    @tag.command(name='find')
    @commands.guild_only()
    async def tag_find(self, ctx: commands.Context, pattern: str, escape = "-"):
        tags = await StaffTag.query.gino.all()
        matches = [tag.trigger for tag in tags if pattern.lower() in str(tag.trigger).lower()]
        tag_matches_step = 15
        
        if escape == "-escape":
            matches = ["`{}`".format(trigger) for trigger in matches]
        
        formatted_tags = []

        for tags in [matches[i:i + tag_matches_step] for i in range(0, len(matches), tag_matches_step)]:
            formatted_tags.append(", ".join(tags))

        # TODO Add truncation

        tag_embed, tag_view = TagFindPagination(ctx, formatted_tags, step = 1).return_paginated_embed()

        await ctx.send(embed=tag_embed, view=tag_view)

    @tag.command(name='list')
    @commands.guild_only()
    async def tag_list(self, ctx: commands.Context):
        tags = []

        for tag in await StaffTag.query.gino.all():
            tags.append({
                "trigger": tag.trigger,
                "value": tag.output,
            })

        tag_embed, tag_view = TagListPagination(ctx, tags, "Here is a list of tags.", 10).return_paginated_embed()

        await ctx.send(embed=tag_embed, view=tag_view)
    
    async def cog_command_error(self, ctx, error: commands.CommandError):
        # ! More robust error checking
        await ctx.send(error)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tag(bot))