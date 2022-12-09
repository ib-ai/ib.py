import discord
from discord.ext import commands
import json


class Embeds(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command()
    async def embed(self, ctx: commands.Context):
        """
        Interactively construct a Discord embed.
        """
        raise NotImplementedError(
            'Command requires implementation and permission set-up.')

    @commands.command()
    async def embedraw(self, ctx: commands.Context, *, embedData):
        """
        Create a Discord embed via raw JSON input.
        """
        try:
            embedBody = json.loads(embedData)
            embed = discord.Embed.from_dict(embedBody)
            await ctx.send(embed=embed)
        except Exception as ex:
            print(ex)
            await ctx.send("An Error Occurred")


async def setup(bot: commands.Bot):
    await bot.add_cog(Embeds(bot))