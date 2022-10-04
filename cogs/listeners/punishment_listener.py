import re
from typing import Union
from discord.ext import commands
import discord
from db.models import PunishmentType, StaffPunishment, StaffTag

from utils.uguild import get_guild_data

class PunishmentListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: Union[discord.User, discord.Member]):
        await query_audit_log(self.bot, guild, user, discord.AuditLogAction.ban, PunishmentType.BAN, False)
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        await query_audit_log(self.bot, guild, user, discord.AuditLogAction.unban, PunishmentType.BAN, True)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await query_audit_log(self.bot, member.guild, member, discord.AuditLogAction.kick, PunishmentType.KICK, False)
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        mute_role_id = await get_guild_data(before.guild, "mute_id")

        if not before.get_role(mute_role_id) and after.get_role(mute_role_id):
            await query_audit_log(self.bot, before.guild, after, discord.AuditLogAction.member_role_update, PunishmentType.MUTE, False)
        elif before.get_role(mute_role_id) and not after.get_role(mute_role_id):
            await query_audit_log(self.bot, before.guild, after, discord.AuditLogAction.member_role_update, PunishmentType.MUTE, True)

async def query_audit_log(bot: commands.Bot, guild: discord.Guild, user: Union[discord.Member, discord.User], action: discord.AuditLogAction, punishment_type: PunishmentType, revocation: bool):
    server_modlog_channel = guild.get_channel(await get_guild_data(guild, "modlog_id"))
    staff_modlog_channel = guild.get_channel(await get_guild_data(guild, "modlog_staff_id"))

    if not server_modlog_channel:
        return
    
    # TODO Logger

    async for entry in guild.audit_logs(limit=10, action=action):        
        if entry.target.id == user.id:
            staff: discord.User = entry.user
            reason = entry.reason

            redacted = False

            # Ignore if bot added/removed roles
            if not revocation and action == discord.AuditLogAction.member_role_update and staff.id == bot.user.id:
                return

            if not reason and ("-redact" in reason.lower() or "-redacted" in reason.lower()):
                redacted = True
                reason = reason.replace("-redact", "").replace("-redacted", "")
            
            punishment = StaffPunishment.create(
                punishment_type = punishment_type,
                user_display = str(user),
                user_id = user.id,
                staff_display = str(staff),
                staff_id = staff.id,
                reason = reason,
                redacted = redacted,
            )

            if revocation:
                revocation_log = get_log_revocation(punishment)

                await server_modlog_channel.send(revocation_log)

                if not staff_modlog_channel:
                    return
                
                await staff_modlog_channel.send(revocation_log)

            else:
                await punishment.create()

                server_modlog = await server_modlog_channel.send(get_log_punishment(punishment, redacted))
                await punishment.update(message_id=server_modlog.id).apply()

                if not staff_modlog_channel:
                    return
                
                staff_modlog = await staff_modlog_channel.send(get_log_punishment(punishment))
                await punishment.update(message_staff_id=staff_modlog.id).apply()

def get_log_punishment(punishment: StaffPunishment, redacted: bool = False):
    modlog = "**Case: #{} | {}**\n**Offender: **{} (User: {}, ID: {})\n**Moderator: **{} (ID: {})\n**Reason: **{}".format(
        punishment.punishment_id,
        get_punishment_type_display(punishment.punishment_type),
        "[REDACTED]" if redacted else f"<@{punishment.user_id}>",
        "[REDACTED]" if redacted else punishment.user_display,
        "[REDACTED]" if redacted else punishment.user_id,
        punishment.staff_display,
        punishment.staff_id,
        f"Use `/reason {punishment.punishment_id} <reason>` to specify a reason."
    )

    if len(modlog) > 2000:
        modlog = modlog[0:2000]
    
    return modlog

def get_punishment_type_display(punishment_type: PunishmentType, revocation: bool = False):
    match punishment_type:
        case PunishmentType.BAN:
            if revocation: return "Unban :angel:"
            return "Ban :hammer:"
        case PunishmentType.KICK:
            return "Kick :boot:"
        case PunishmentType.MUTE:
            if revocation: return "Unmute :speaking_head:"
            return "Mute :zipper_mouth:"
        case PunishmentType.UNKNOWN:
            return "???"

def get_log_revocation(punishment: StaffPunishment):
    return "**{}**\n**Pardoned: **{} (User: {}, ID: {})\n**Moderator: **{} (ID: {})".format(
        get_punishment_type_display(punishment.punishment_type, True),
        f"<@{punishment.user_id}>",
        punishment.user_display,
        punishment.user_id,
        punishment.staff_display,
        punishment.staff_id,
    )

async def setup(bot: commands.Bot):
    await bot.add_cog(PunishmentListener(bot))