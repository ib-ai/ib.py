from tortoise.models import Model
from tortoise.contrib.postgres.fields import ArrayField
from tortoise import fields
import enum

# Enums

class PunishmentType(str, enum.Enum):
    KICK = "kick"
    MUTE = "mute"
    BAN = "ban"
    UNKNOWN = "unknown"

class ChannelType(str, enum.Enum):
    TEXT = "text"
    VOICE = "voice"

# Guild Tables

class GuildData(Model):
    class Meta():
        table = "guild_data"

    guild_id = fields.BigIntField(pk=True, unique=True)
    prefix = fields.CharField(max_length=1, null=True)
    modlog_id = fields.BigIntField(null=True)
    modlog_staff_id = fields.BigIntField(null=True)
    updates_id = fields.BigIntField(null=True)
    logs_id = fields.BigIntField(null=True)
    mute_id = fields.BigIntField(null=True)
    moderator_id = fields.BigIntField(null=True)
    helper_id = fields.BigIntField(null=True)
    filtering = fields.BooleanField(default=False)
    removal = fields.BooleanField(default=False)
    monitoring_user = fields.BooleanField(default=False)
    monitoring_message = fields.BooleanField(default=False)
    monitor_user_log_id = fields.BigIntField(null=True)
    monitor_message_log_id = fields.BigIntField(null=True)

class GuildSnapshot(Model):
    class Meta():
        table = "snapshot"
    
    snapshot_id = fields.IntField(pk=True)
    category_id = fields.BigIntField()
    channel_type = fields.CharEnumField(ChannelType)
    channel_list = ArrayField()

class GuildCassowary(Model):
    class Meta():
        table = "cassowary"
    
    cassowary_id = fields.IntField(pk=True)
    label = fields.CharField(max_length=256)
    penguin = fields.BooleanField(default=False)

class GuildCassowaryRoles(Model):
    class Meta():
        table = "cassowary_roles"
    
    category_role_id = fields.BigIntField(pk=True)
    role_id = fields.BigIntField()
    cassowary_id = fields.OneToOneField('models.GuildCassowary')

class GuildVoteLadder(Model):
    class Meta():
        table = "vote_ladder"
    
    vote_ladder_id = fields.IntField(pk=True)
    vote_ladder_label = fields.CharField(max_length=256)
    vote_ladder_roles = ArrayField()
    channel_id = fields.BigIntField()
    threshold = fields.IntField()
    minimum = fields.IntField()
    timeout = fields.IntField()

class GuildVote(Model):
    class Meta():
        table = "vote"
    
    vote_id = fields.IntField(pk=True)
    message_id = fields.BigIntField()
    message = fields.TextField()
    positive = fields.IntField(default=0)
    negative = fields.IntField(default=0)
    expiry = fields.IntField(default=604800) # 1 week in seconds
    finished = fields.BooleanField(default=False)
    vote_ladder_id = fields.OneToOneField('models.GuildVoteLadder')

# Staff Tables

class StaffTag(Model):
    class Meta():
        table = "tag"

    tag_id = fields.IntField(pk=True)
    trigger = fields.CharField(max_length=256)
    output = fields.CharField(max_length=1024)
    disabled = fields.BooleanField(default=False)

class StaffNote(Model):
    class Meta():
        table = "note"

    note_id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    author_id = fields.BigIntField()
    note = fields.CharField(max_length=1024)
    timestamp = fields.DatetimeField(auto_now_add=True)

class StaffMonitorUser(Model):
    class Meta():
        table = "monitor_user"

    monitor_user_id = fields.IntField(pk=True)
    user_id = fields.BigIntField()

class StaffMonitorMessageGroups(Model):
    class Meta():
        table = "monitor_message_groups"

    group_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=256)
    disabled = fields.BooleanField(default=False)
    monitor_messages: fields.ManyToManyRelation["StaffMonitorMessage"] = fields.ManyToManyField('models.StaffMonitorMessage', related_name="groups")

class StaffMonitorMessage(Model):
    class Meta():
        table = "monitor_message"

    monitor_message_id = fields.IntField(pk=True)
    disabled = fields.BooleanField(default=False)
    message = fields.CharField(max_length=1000)
    groups: fields.ManyToManyRelation[StaffMonitorMessageGroups]    

class StaffFilter(Model):
    class Meta():
        table = "filter"

    filter_id = fields.IntField(pk=True)
    trigger = fields.CharField(max_length=1024)
    notify = fields.BooleanField(default=False)

class StaffReaction(Model):
    class Meta():
        table = "reaction"

    reaction_id = fields.IntField(pk=True)
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField()

class StaffButtonRole(Model):
    class Meta():
        table = "buttonrole"

    button_role_id = fields.IntField(pk=True)
    emoji_id = fields.BigIntField()
    label = fields.CharField(max_length=256)
    role_ids = ArrayField()
    reaction_id = fields.OneToOneField('models.StaffReaction')

class StaffPunishment(Model):
    class Meta():
        table = "punishment"

    punishment_id = fields.IntField(pk=True)
    punishment_type = fields.CharEnumField(PunishmentType)
    user_display = fields.CharField(max_length=256)
    user_id = fields.BigIntField()
    staff_display = fields.CharField(max_length=256)
    staff_id = fields.BigIntField()
    reason = fields.CharField(max_length=1024)
    redacted = fields.BooleanField(default=False)
    message_id = fields.BigIntField()
    message_staff_id = fields.BigIntField() 
    expiry = fields.DatetimeField(null=True)

# Helper Tables

class HelperMessage(Model):
    class Meta():
        table = "helper_message"

    helper_message_id = fields.IntField(pk=True)
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField()
    role_id = fields.BigIntField()

# Member Tables

class MemberRole(Model):
    class Meta():
        table = "member_role"

    user_id = fields.BigIntField(pk=True)
    role_ids = ArrayField()

class MemberOpt(Model):
    class Meta():
        table = "member_opt"

    opt_id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    channel_id = fields.BigIntField()

class MemberReminder(Model):
    class Meta():
        table = "member_reminder"

    reminder_id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    message = fields.CharField(max_length=1024)
    timestamp = fields.DatetimeField()
