import asyncio
from datetime import datetime
from discord.ext import commands
import discord
from discord import app_commands
from db.models import MemberReminder
from pagination.pagination import Pagination

from utils.utime import parse_duration

class Reminder(commands.GroupCog, name = "reminder"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()
    
    @app_commands.command(name = "create", description="Creates a reminder.")
    @app_commands.guild_only()
    async def reminder_create(self, interaction: discord.Interaction, date: str, reminder: str):
        timestamp = parse_duration(date)
        await MemberReminder.create(text=reminder, time=timestamp, user_id=interaction.user.id)

        await interaction.response.send_message("Reminder has been set. You will be notifed at <t:{}>.".format(int(timestamp.timestamp())))

        await schedule_reminder(interaction.user, timestamp, reminder)
    
    @app_commands.command(name = "delete", description="Deletes a reminder.")
    @app_commands.guild_only()
    async def reminder_delete(self, interaction: discord.Interaction, id: int):
        reminder = await MemberReminder.get(id)

        if reminder.user_id != interaction.user.id or reminder.time > datetime.utcnow():
            await interaction.response.send("Cannot delete reminder due to invalid ID.")
            return

        await reminder.delete()

        await interaction.response.send_message("Reminder with ID {} has been deleted.".format(id))

    @app_commands.command(name = "list", description="Lists your reminders.")
    @app_commands.guild_only()
    async def reminder_list(self, interaction: discord.Interaction):
        reminders_list = await MemberReminder.query.where(MemberReminder.user_id == interaction.user.id).where(MemberReminder.time > datetime.utcnow()).gino.all()

        reminders_embed = discord.Embed(description="Here is a list of your active reminders.")

        # TODO Pagination

        for reminder in reminders_list:
            reminders_embed.add_field(
                name="<t:{}> (ID: {})".format(int(reminder.time.timestamp()), reminder.reminder_id),
                value=reminder.text,
                inline=False
            )
        
        await interaction.response.send_message(embed=reminders_embed)

async def schedule_reminder(user: discord.User, timestamp: datetime, reminder: str):
    await asyncio.sleep(int(timestamp.timestamp()) - int(datetime.utcnow().timestamp()))
    await user.send("You asked me to remind you of: {}".format(reminder))
        
async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))