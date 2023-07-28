import discord
from discord.ext import commands
from utils.checks import cogify, admin_command
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # TODO: change back to logging.info


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    cog_check = cogify(admin_command())

    @commands.hybrid_command()
    async def giverole(self, ctx: commands.Context, existing_role: discord.Role, new_role: discord.Role):
        """
        Assign a new role to all members with a specific role.
        """
        failure_count = 0	
        role_members = [member for member in ctx.guild.members if existing_role in member.roles]
        for member in role_members:
            try:
                await member.add_roles(new_role)
            except discord.Forbidden:
                logger.info(f'Could not add role to {member.name}')
                failure_count += 1
        await ctx.send(f"Successfully added roles to {len(role_members) - failure_count} members.") 
        logger.info(f'Given {new_role.name} role to {len(role_members)-failure_count} members.')

async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))