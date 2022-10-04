from discord.ext import commands
import discord

from db.models import MemberOpt

class GuildListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        opt_list = await MemberOpt.query.where(MemberOpt.user_id == member.id).gino.all()
        channels = [member.guild.get_channel(opt.channel_id) for opt in opt_list]

        for channel in channels:
            if not channel:
                return
            
            await channel.set_permissions(member, read_messages=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(GuildListener(bot))