import logging
from typing import Optional

import discord
from discord.ext import commands

from ..config import IBPyConfig
from ..db.cached import get_guild_data
from ..db.models import GuildData
from ..utils.checks import admin_command, cogify
from ..utils.commands import available_subcommands

config = IBPyConfig()
config.requires("prefix")

logger = logging.getLogger(__name__)

mention_styles = {
    'TextChannel': '#',
    'Role': '@&',
}

class SetGuildData(commands.Cog, name='Guild Settings'):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    cog_check = cogify(admin_command())


    async def cog_load(self):
        self.bot.command_prefix = self.get_prefix

    async def cog_unload(self):
        self.bot.command_prefix = config.prefix

    async def get_prefix(self, bot, message: discord.Message):
        guild_data = await get_guild_data(message.guild.id)
        if guild_data and guild_data.prefix:
            return guild_data.prefix
        return config.prefix


    @staticmethod
    def guild_data_set_factory(datatype: str, dataname: str, *, desc: Optional[str] = None):
        style = mention_styles[datatype]
        discord_type = getattr(discord, datatype)
        async def cmd(ctx: commands.Context, thing: Optional[discord_type] = None):
            f"""
            {desc}
            """
            values = {dataname: thing.id if thing else None}
            guild_data, created = await GuildData.update_or_create(values, guild_id = ctx.guild.id)
            if created:
                guild_data.prefix = config.prefix
                await guild_data.save()
            get_guild_data.cache_clear()

            if thing:
                await ctx.send(f'`{dataname}` set to ID of <{style}{thing.id}> for this guild.')
            else:
                await ctx.send(f'`{dataname}` set to `None` for this guild.')
        return cmd

    @commands.group(invoke_without_command=True)
    async def set(self, ctx: commands.Context):
        """
        Commands for setting guild data.
        """
        await available_subcommands(ctx)
    set.command(name='modlog')(guild_data_set_factory('TextChannel', 'modlog_id',
        desc='Set a public moderation log channel.'
    ))
    set.command(name='staffmodlog')(guild_data_set_factory('TextChannel', 'modlog_staff_id',
        desc='Set a staff moderation log channel.'
    ))
    set.command(name='updates')(guild_data_set_factory('TextChannel', 'updates_id',
        desc='Set an updates channel.'
    ))
    set.command(name='logs')(guild_data_set_factory('TextChannel', 'logs_id',
        desc='Set a logs channel.'
    ))
    set.command(name='mute')(guild_data_set_factory('Role', 'mute_id',
        desc='Set a mute role.'
    ))
    set.command(name='moderator')(guild_data_set_factory('Role', 'moderator_id',
        desc='Set a moderator role.'
    ))
    set.command(name='helper')(guild_data_set_factory('Role', 'helper_id',
        desc='Set a helper role.'
    ))
    set.command(name='messagemonitor')(guild_data_set_factory('TextChannel', 'monitor_user_log_id',
        desc='Set a message monitoring log channel.'
    ))
    set.command(name='usermonitor')(guild_data_set_factory('TextChannel', 'monitor_message_log_id',
        desc='Set a user monitoring log channel.'
    ))

    @set.command()
    async def prefix(self, ctx, prefix):
        """
        Set a custom bot prefix for this guild.
        """
        prefix = prefix or config.prefix
        values = {'prefix': prefix}
        guild_data, created = await GuildData.update_or_create(values, guild_id = ctx.guild.id)
        get_guild_data.cache_clear()

        await ctx.send(f'`prefix` set to ID of `{prefix}` for this guild.')


    @staticmethod
    def guild_data_toggle_factory(*datanames: str, desc: Optional[str] = None):
        async def cmd(ctx: commands.Context):
            f"""
            {desc}
            """
            guild_data = await get_guild_data(guild_id=ctx.guild.id)
            values = {dataname: not getattr(guild_data, dataname) if guild_data else True for dataname in datanames}
            await GuildData.update_or_create(values, guild_id = ctx.guild.id)
            get_guild_data.cache_clear()
            await ctx.send('\n'.join(f"`{dataname}` is {'`disabled`' if values[dataname] else '`enabled`'}" for dataname in datanames))
        return cmd

    @commands.group(invoke_without_command=True)
    async def toggle(self, ctx: commands.Context):
        """
        Commands for toggling guild data.
        """
        await available_subcommands(ctx)
    toggle.command(name='filtering')(guild_data_toggle_factory('filtering',
        desc='Toggle filtering.'
    ))
    toggle.command(name='usermonitor')(guild_data_toggle_factory('monitoring_user',
        desc='Toggle user monitoring.'
    ))
    toggle.command(name='messagemonitor')(guild_data_toggle_factory('monitoring_message',
        desc='Toggle message monitoring.'
    ))
    toggle.command(name='monitor')(guild_data_toggle_factory('monitoring_user', 'monitoring_message',
        desc='Toggle monitoring.'
    ))

    @commands.command()
    async def guilddata(self, ctx: commands.Context):
        """
        View this guild's data.
        """
        guild_data = await get_guild_data(ctx.guild.id)
        if not guild_data:
            await ctx.send("No guild data set for this guild.")
            return

        field_names = [field["name"] for field in GuildData.describe()["data_fields"]]
        max_len = max(len(name) for name in field_names)
        description = "\n".join(
            f"{key:>{max_len}} = {getattr(guild_data, key)}" for key in field_names
        )
        embed = discord.Embed(
            title=f"Guild Data for {ctx.guild.name} (ID: {ctx.guild.id})",
            color=discord.Color.dark_gray(),
            description="```" + description + "```"
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SetGuildData(bot))
