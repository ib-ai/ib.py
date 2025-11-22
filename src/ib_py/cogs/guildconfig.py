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

MENTION_STYLES = {
    'TextChannel': '#',
    'Role': '@&',
}

GUILD_CONFIGURATION_DATA = {
    'modlog': {
        'datatype': 'TextChannel',
        'dataname': 'modlog_id',
        'desc': 'Set a public moderation log channel.'
    },
    'staffmodlog': {
        'datatype': 'TextChannel',
        'dataname': 'modlog_staff_id',
        'desc': 'Set a staff moderation log channel.'
    },
    'updates': {
        'datatype': 'TextChannel',
        'dataname': 'updates_id',
        'desc': 'Set an updates channel.'
    },
    'logs': {
        'datatype': 'TextChannel',
        'dataname': 'logs_id',
        'desc': 'Set a logs channel.'
    },
    'mute': {
        'datatype': 'Role',
        'dataname': 'mute_id',
        'desc': 'Set a mute role.'
    },
    'moderator': {
        'datatype': 'Role',
        'dataname': 'moderator_id',
        'desc': 'Set a moderator role.'
    },
    'helper': {
        'datatype': 'Role',
        'dataname': 'helper_id',
        'desc': 'Set a helper role.'
    },
    'usermonitor': {
        'datatype': 'TextChannel',
        'dataname': 'monitor_user_log_id',
        'desc': 'Set a message monitoring log channel.'
    },
    'messagemonitor': {
        'datatype': 'TextChannel',
        'dataname': 'monitor_message_log_id',
        'desc': 'Set a user monitoring log channel.'
    },
}
GUILD_CONFIGURATION_TOGGLES = {
    'filtering': {
        'datanames': ['filtering'],
        'desc': 'Toggle filtering.'
    },
    'usermonitor': {
        'datanames': ['monitoring_user'],
        'desc': 'Toggle user monitoring.'
    },
    'messagemonitor': {
        'datanames': ['monitoring_message'],
        'desc': 'Toggle message monitoring.'
    },
    'monitor': {
        'datanames': ['monitoring_user', 'monitoring_message'],
        'desc': 'Toggle monitoring.'
    },
}


class GuildConfig(commands.Cog, name='Guild Settings'):
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


    @commands.command()
    async def guilddata(self, ctx: commands.Context):
        """
        View this guild's data.
        """
        guild_data = await get_guild_data(ctx.guild.id)
        if not guild_data:
            await ctx.send("No guild data set for this guild.")
            return

        data = ["**prefix**: " + (guild_data.prefix or config.prefix)]
        for name, field in GUILD_CONFIGURATION_DATA.items():
            value = getattr(guild_data, field['dataname'])
            output = f"**{name}**: " + (f"<{MENTION_STYLES[field['datatype']]}{value}> (ID: {value})" if value else "Not set.")
            data.append(output)

        toggles = {}
        for field in GUILD_CONFIGURATION_TOGGLES.values():
            for name in field['datanames']:
                if name in toggles:
                    continue
                output = f"**{name}**: {'enabled' if getattr(guild_data, name) else 'disabled'}"
                toggles[name] = output

        embed = discord.Embed(
            title=f"Guild Data for {ctx.guild.name} (ID: {ctx.guild.id})",
            color=discord.Color.dark_gray(),
        )
        embed.add_field(name="Configured Data", value="\n".join(data), inline=False)
        embed.add_field(name="Toggles", value="\n".join(toggles.values()), inline=False)
        await ctx.send(embed=embed)


    @staticmethod
    def guild_data_set_factory(datatype: str, dataname: str, *, desc: Optional[str] = None):
        style = MENTION_STYLES[datatype]
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
                await ctx.send(f'`{dataname}` set to <{style}{thing.id}> (ID: {thing.id}) for this guild.')
            else:
                await ctx.send(f'`{dataname}` set to `None` for this guild.')
        return cmd

    @commands.group(invoke_without_command=True)
    async def set(self, ctx: commands.Context):
        """
        Commands for setting guild data.
        """
        await available_subcommands(ctx)

    for name, kwargs in GUILD_CONFIGURATION_DATA.items():
        set.command(name=name)(guild_data_set_factory(**kwargs))

    @set.command()
    async def prefix(self, ctx: commands.Context, prefix: Optional[str] = None):
        """
        Set a custom bot prefix for this guild.
        """
        values = {'prefix': prefix}
        await GuildData.update_or_create(values, guild_id = ctx.guild.id)
        get_guild_data.cache_clear()

        prefix = prefix or config.prefix
        await ctx.send(f'`prefix` set to `{prefix}` for this guild.')


    @staticmethod
    def guild_data_toggle_factory(datanames: list[str], desc: Optional[str] = None):
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

    for name, kwargs in GUILD_CONFIGURATION_TOGGLES.items():
        toggle.command(name=name)(guild_data_toggle_factory(**kwargs))


async def setup(bot: commands.Bot):
    await bot.add_cog(GuildConfig(bot))
