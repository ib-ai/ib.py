import discord

from discord.ext import commands
from db.models import ChannelType, GuildSnapshot

from utils.ucommand import reply_unknown_syntax
from utils.uguild import mods_or_manage_guild

class ChannelOrder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.group(invoke_without_command=True, name='channelorder', aliases=['co'])
    @mods_or_manage_guild()
    @commands.guild_only()
    async def channel_order(self, ctx: commands.Context):
        await ctx.send(reply_unknown_syntax(ctx.command))
    
    @channel_order.command(name='snapshot')
    @mods_or_manage_guild()
    @commands.guild_only()
    async def snapshot(self, ctx: commands.Context, category: discord.CategoryChannel = None):
        category_list = []
        channel_order_embed = discord.Embed(title="Order Of Channels")

        if category:
            # Check if member has permissions to view channel
            if not category.permissions_for(ctx.author).view_channel:
                await ctx.send("You do not have sufficient permissions to execute this command.")
                return

            category_list = [category]
        else:
            # Severe rate limiting and so limited to Admins
            if not ctx.author.guild_permissions.manage_guild:
                await ctx.send("You do not have sufficient permissions to execute this command.")
                return

            category_list = ctx.guild.categories

        try:
            for cat in category_list:
                text_channels = cat.text_channels
                voice_channels = cat.voice_channels

                print(text_channels)
                print(voice_channels)

                if text_channels:
                    category_row_text = await GuildSnapshot.query.where(GuildSnapshot.category_id == cat.id).where(GuildSnapshot.channel_type == ChannelType.TEXT).gino.first()

                    if category_row_text is None:
                        category_row_text = await GuildSnapshot.create(category_id=cat.id, channel_type=ChannelType.TEXT)
                    
                    channel_list_ids = [channel.id for channel in text_channels]

                    await category_row_text.update(channel_list=channel_list_ids).apply()

                    channel_names = ", ".join([channel.name for channel in text_channels])

                    channel_order_embed.add_field(name="Text Channels ({})".format(cat.name), value=channel_names, inline=False)

                if voice_channels:
                    category_row_voice = await GuildSnapshot.query.where(GuildSnapshot.category_id == cat.id).where(GuildSnapshot.channel_type == ChannelType.VOICE).gino.first()

                    if category_row_voice is None:
                        category_row_voice = await GuildSnapshot.create(category_id=cat.id, channel_type=ChannelType.VOICE)
                    
                    channel_list_ids = [channel.id for channel in voice_channels]

                    await category_row_voice.update(channel_list=channel_list_ids).apply()

                    channel_names = ", ".join([channel.name for channel in voice_channels])

                    channel_order_embed.add_field(name="Voice Channels ({})".format(cat.name), value=channel_names, inline=False)
                    
        except Exception as e:
            raise RuntimeError(e)
            
        await ctx.send(embed=channel_order_embed)
    
    @channel_order.command(name='rollback', aliases=['r'])
    @mods_or_manage_guild()
    @commands.guild_only()
    async def rollback(self, ctx: commands.Context, category: discord.CategoryChannel = None):
        category_list = []

        if category:
            # Check if member has permissions to view channel
            if not category.permissions_for(ctx.author).view_channel:
                await ctx.send("You do not have sufficient permissions to execute this command.")
                return

            category_list = [category]
        else:
            # Severe rate limiting and so limited to Admins
            if not ctx.author.guild_permissions.manage_guild:
                await ctx.send("You do not have sufficient permissions to execute this command.")
                return

            category_list = ctx.guild.categories

        try:
            for cat in category_list:
                category_row_text = await GuildSnapshot.query.where(GuildSnapshot.category_id == cat.id).where(GuildSnapshot.channel_type == ChannelType.TEXT).gino.first()
                category_row_voice = await GuildSnapshot.query.where(GuildSnapshot.category_id == cat.id).where(GuildSnapshot.channel_type == ChannelType.VOICE).gino.first()

                await rollback_channels(category_row_text, ctx.guild)
                await rollback_channels(category_row_voice, ctx.guild)
                    
        except Exception as e:
            print(e)
            
        await ctx.send("Consider it done.")

    @channel_order.command()
    @mods_or_manage_guild()
    @commands.guild_only()
    async def list(self, ctx: commands.Context, category: discord.CategoryChannel = None):
        category_list = []
        channel_order_embed = discord.Embed(title="Order Of Channels")

        if category:
            # Check if member has permissions to view channel
            if not category.permissions_for(ctx.author).view_channel:
                await ctx.send("You do not have sufficient permissions to execute this command.")
                return

            category_list = [category]
        else:
            # Severe rate limiting and so limited to Admins
            if not ctx.author.guild_permissions.manage_guild:
                await ctx.send("You do not have sufficient permissions to execute this command.")
                return

            category_list = ctx.guild.categories

        try:
            for cat in category_list:
                # Text Channels

                category_row_text = await GuildSnapshot.query.where(GuildSnapshot.category_id == cat.id).where(GuildSnapshot.channel_type == ChannelType.TEXT).gino.first()

                if category_row_text is not None:
                    text_channels = [ctx.guild.get_channel(id) for id in category_row_text.channel_list]

                    channel_names = ", ".join([channel.name if channel else "`None`" for channel in text_channels])

                    channel_order_embed.add_field(name="Text Channels ({})".format(cat.name), value=channel_names, inline=False)

                # Voice Channels

                category_row_voice = await GuildSnapshot.query.where(GuildSnapshot.category_id == cat.id).where(GuildSnapshot.channel_type == ChannelType.VOICE).gino.first()

                if category_row_voice is not None:                    
                    voice_channels = [ctx.guild.get_channel(id) for id in category_row_voice.channel_list]

                    channel_names = ", ".join([channel.name if channel else "`None`" for channel in voice_channels])

                    channel_order_embed.add_field(name="Voice Channels ({})".format(cat.name), value=channel_names, inline=False)
                    
        except Exception as e:
            print(e)
            
        await ctx.send(embed=channel_order_embed)
    
    async def cog_command_error(self, ctx, error: commands.CommandError):
        # ! More robust error checking
        await ctx.send(error)

async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelOrder(bot))

async def rollback_channels(category_row: GuildSnapshot, guild: discord.Guild):
    if category_row is not None:     
        for index, channel_id in enumerate(category_row.channel_list):
            channel = guild.get_channel(channel_id)
            print(channel.name)
            if channel:
                await channel.edit(position=index)