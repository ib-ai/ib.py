import io
import textwrap
import contextlib
from typing import Literal, Optional

import discord
from discord.ext import commands

from db.models import GuildData

class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.command()
    async def guilddata(self, ctx: commands.Context):
        """
        Display all guild data.
        """
        guild_data = await GuildData.get_or_none(guild_id=ctx.guild.id)
        if not guild_data:
            await ctx.send('No data set for this guild!')
        setcase = lambda x, c: f"set to ID of <{c}{x}>" if x else "not set"
        ablecase = lambda x: '`disabled`' if x else '`enabled`'
        message = f"""
        Prefix set to `{guild_data.prefix}`.
        Public moderation log entries channel {setcase(guild_data.modlog_id, "#")}.
        Internal moderation log entries channel {setcase(guild_data.modlog_staff_id, "#")}.
        Updates channel {setcase(guild_data.updates_id, "#")}.
        Logs channel {setcase(guild_data.logs_id, "#")}.
        Mute role {setcase(guild_data.mute_id, "@&")}.
        Moderator role {setcase(guild_data.moderator_id, "@&")}.
        Helper role {setcase(guild_data.helper_id, "@&")}.
        Filter is {ablecase(guild_data.filtering)}.
        User monitoring is {ablecase(guild_data.monitoring_user)}.
        Message monitoring is {ablecase(guild_data.monitoring_message)}.
        User monitor log channel {setcase(guild_data.monitor_user_log_id, "#")}.
        Message monitor log channel {setcase(guild_data.monitor_message_log_id, "#")}.
        """
        embed_data = dict(
            title = f'Guild Data for {ctx.guild.name}',
            description = message
        )
        embed = discord.Embed.from_dict(embed_data)
        await ctx.send(embed=embed)
    
    @commands.command(name='eval')
    async def evaluate(self, ctx: commands.Context, *, code: str):
        """
        Run python code.
        """
        local_variables = {
            "discord": discord,
            "commands": commands,
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message
        }

        stdout = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout):
                exec(
                    f"async def func():\n{textwrap.indent(code, '    ')}", local_variables,
                )

                obj = await local_variables["func"]()
                result = f"{stdout.getvalue()}\n-- {obj}\n"
        except Exception as e:
            raise RuntimeError(e)
        
        await ctx.send(result[0:2000])
    
    @commands.command()
    async def sync(self, ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        """
        List your reminders.
        """ 
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Dev(bot))