import io
import logging
import textwrap
import contextlib
from typing import Literal, Optional

import discord
from discord.ext import commands

from utils.checks import cogify, admin_command
from utils.commands import available_subcommands


logger = logging.getLogger(__name__)


def ext_converter(argument: str):
    """
    A converter for an extension name.
    """
    argument = argument.strip()
    if not argument.startswith("cogs."):
        argument = f"cogs.{argument}"
    return argument


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    cog_check = cogify(admin_command())

    @commands.command()
    async def guilddata(self, ctx: commands.Context):
        """
        Display all guild data.
        """
        raise NotImplementedError("Command requires implementation and permission set-up.")

    @commands.command(name="eval")
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
            "message": ctx.message,
        }

        stdout = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout):
                exec(
                    f"async def func():\n{textwrap.indent(code, '    ')}",
                    local_variables,
                )

                obj = await local_variables["func"]()
                result = f"{stdout.getvalue()}\n-- {obj}\n"
        except Exception as e:
            raise RuntimeError(e)

        await ctx.send(result[0:2000])

    @commands.command()
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
    ) -> None:
        """
        Syncs app commands to Discord.
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

    @commands.group(aliases=['ext'])
    async def extensions(self, ctx: commands.Context):
        """
        Utilities for managing loaded extensions.
        """
        if ctx.invoked_subcommand is None:
            await available_subcommands(ctx)

    @extensions.command(name="list")
    async def ext_list(self, ctx: commands.Context):
        """
        Lists currently loaded extensions.
        """
        ext_list = "\n".join(f"- {ext}" for ext in self.bot.extensions)
        await ctx.send(f"List of loaded extensions:\n{ext_list}")

    @extensions.command(name="load")
    async def ext_load(self, ctx: commands.Context, ext_name: ext_converter):
        """
        Loads an extension.
        """
        logger.info(f"Loading extension {ext_name}")
        await self.bot.load_extension(ext_name)
        await ctx.send(f"Successfully loaded extension `{ext_name}`")

    @extensions.command(name="unload")
    async def ext_unload(self, ctx: commands.Context, ext_name: ext_converter):
        """
        Unloads an extension.
        """
        logger.info(f"Unloading extension {ext_name}")
        await self.bot.unload_extension(ext_name)
        await ctx.send(f"Successfully unloaded extension `{ext_name}`")

    @extensions.command(name="reload")
    async def ext_reload(self, ctx: commands.Context, ext_name: ext_converter):
        """
        Reloads an extension.
        """
        logger.info(f"Reloading extension {ext_name}")
        await self.bot.reload_extension(ext_name)
        await ctx.send(f"Successfully reloaded extension `{ext_name}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(Dev(bot))
