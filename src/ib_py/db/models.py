import enum

from tortoise import fields
from tortoise.contrib.postgres.fields import ArrayField
from tortoise.models import Model

# Enums


class PunishmentType(str, enum.Enum):
    WARN = "warn"
    KICK = "kick"
    TIMEOUT = "timeout"
    MUTE = "mute"
    BAN = "ban"
    UNKNOWN = "unknown"


# Guild Tables


class GuildData(Model):
    class Meta:
        table = "guild_data"

    guild_id = fields.BigIntField(primary_key=True, unique=True)
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
    suppressed_channels = ArrayField(element_type="bigint", null=True, default=list)
    monitoring_user = fields.BooleanField(default=False)
    monitoring_message = fields.BooleanField(default=False)
    monitor_user_log_id = fields.BigIntField(null=True)
    monitor_message_log_id = fields.BigIntField(null=True)


class GuildSnapshot(Model):
    class Meta:
        table = "snapshot"

    snapshot_id = fields.IntField(primary_key=True)
    category_id = fields.BigIntField()
    channel_list = ArrayField(element_type="bigint", null=True, default=list)


class GuildCassowary(Model):
    class Meta:
        table = "cassowary"

    cassowary_id = fields.IntField(primary_key=True)
    label = fields.CharField(max_length=256)
    penguin = fields.BooleanField(default=False)


class GuildCassowaryRoles(Model):
    class Meta:
        table = "cassowary_roles"

    category_role_id = fields.BigIntField(primary_key=True)
    role_id = fields.BigIntField()
    cassowary_id = fields.OneToOneField("models.GuildCassowary")


class GuildVoteLadder(Model):
    class Meta:
        table = "vote_ladder"

    vote_ladder_id = fields.IntField(primary_key=True)
    vote_ladder_label = fields.CharField(max_length=256)
    vote_ladder_roles = ArrayField()
    channel_id = fields.BigIntField()
    threshold = fields.IntField()
    minimum = fields.IntField()
    timeout = fields.IntField()


class GuildVote(Model):
    class Meta:
        table = "vote"

    vote_id = fields.IntField(primary_key=True)
    message_id = fields.BigIntField()
    message = fields.TextField()
    positive = fields.IntField(default=0)
    negative = fields.IntField(default=0)
    expiry = fields.IntField(default=604800)  # 1 week in seconds
    finished = fields.BooleanField(default=False)
    vote_ladder_id = fields.OneToOneField("models.GuildVoteLadder")


# Staff Tables


class StaffTag(Model):
    class Meta:
        table = "tag"

    tag_id = fields.IntField(primary_key=True)
    trigger = fields.CharField(max_length=256)
    output = fields.CharField(max_length=1024)
    disabled = fields.BooleanField(default=False)


class StaffNote(Model):
    class Meta:
        table = "note"

    note_id = fields.IntField(primary_key=True)
    user_id = fields.BigIntField()
    author_id = fields.BigIntField()
    note = fields.CharField(max_length=1024)
    timestamp = fields.DatetimeField(auto_now_add=True)


class StaffMonitorUser(Model):
    class Meta:
        table = "monitor_user"

    monitor_user_id = fields.IntField(primary_key=True)
    user_id = fields.BigIntField()


class StaffMonitorMessageGroups(Model):
    class Meta:
        table = "monitor_message_groups"

    group_id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=256)
    disabled = fields.BooleanField(default=False)
    monitor_messages: fields.ManyToManyRelation["StaffMonitorMessage"] = (
        fields.ManyToManyField("models.StaffMonitorMessage", related_name="groups")
    )


class StaffMonitorMessage(Model):
    class Meta:
        table = "monitor_message"

    monitor_message_id = fields.IntField(primary_key=True)
    disabled = fields.BooleanField(default=False)
    message = fields.CharField(max_length=1000)


class StaffFilter(Model):
    class Meta:
        table = "filter"

    filter_id = fields.IntField(primary_key=True)
    trigger = fields.CharField(max_length=1024)
    notify = fields.BooleanField(default=False)


class StaffReaction(Model):
    class Meta:
        table = "reaction"

    reaction_id = fields.IntField(primary_key=True)
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField()


class StaffButtonRole(Model):
    class Meta:
        table = "buttonrole"

    button_role_id = fields.IntField(primary_key=True)
    emoji_id = fields.BigIntField()
    label = fields.CharField(max_length=256)
    role_ids = ArrayField()
    reaction_id = fields.OneToOneField("models.StaffReaction")


class StaffPunishment(Model):
    class Meta:
        table = "punishment"

    punishment_id = fields.IntField(primary_key=True)
    punishment_type = fields.CharEnumField(PunishmentType)
    guild_id = fields.BigIntField()
    user_display = fields.CharField(max_length=256)
    user_id = fields.BigIntField()
    staff_display = fields.CharField(max_length=256)
    staff_id = fields.BigIntField()
    reason = fields.CharField(max_length=1024)
    redacted = fields.BooleanField(default=False)
    message_id = fields.BigIntField(null=True)
    message_staff_id = fields.BigIntField(null=True)
    timestamp = fields.DatetimeField(auto_now_add=True)
    expiry = fields.DatetimeField(null=True)
    expiry_complete = fields.BooleanField(default=True)


# Helper Tables


class HelperMessage(Model):
    class Meta:
        table = "helper_message"

    helper_message_id = fields.IntField(primary_key=True)
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField()
    role_id = ArrayField(element_type="bigint")


# Member Tables


class MemberRole(Model):
    class Meta:
        table = "member_role"

    sticky_role_id = fields.IntField(primary_key=True)
    guild_id = fields.BigIntField()
    user_id = fields.BigIntField()
    role_ids = ArrayField(element_type="bigint", default=list)


class MemberOpt(Model):
    class Meta:
        table = "member_opt"

    opt_id = fields.IntField(primary_key=True)
    user_id = fields.BigIntField()
    channel_id = fields.BigIntField()


class MemberReminder(Model):
    class Meta:
        table = "member_reminder"

    reminder_id = fields.IntField(primary_key=True)
    user_id = fields.BigIntField()
    message = fields.CharField(max_length=1024)
    timestamp = fields.DatetimeField()
