import discord
from discord.ext import commands
from utils.checks import cogify, admin_command


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    cog_check = cogify(admin_command())

    @commands.hybrid_command()
    async def giverole(self, ctx: commands.Context, existing_role: discord.Role, new_role: discord.Role):
        """
        Assign a new role to all members with a specific role.
        """
        if existing_role is None or new_role is None:
            return await ctx.send("Please provide both the existing and new role.")
        role_members = [member for member in ctx.guild.members if existing_role in member.roles]
        for member in role_members:
            try:
                await member.add_roles(new_role)
            except discord.Forbidden:
                return await ctx.send("I do not have permission to add roles to members.")
            except discord.HTTPException:
                await ctx.send(f"Could not add role to {member.name}")
        await ctx.send("Successfully added roles.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))