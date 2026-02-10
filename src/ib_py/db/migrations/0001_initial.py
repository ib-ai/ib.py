from tortoise import fields, migrations
from tortoise.contrib.postgres.fields import ArrayField
from tortoise.fields.base import OnDelete
from tortoise.migrations import operations as ops

from ib_py.db.models import PunishmentType


class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name="GuildCassowary",
            fields=[
                (
                    "cassowary_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("label", fields.CharField(max_length=256)),
                (
                    "penguin",
                    fields.BooleanField(
                        default=False, generated=False, null=False, unique=False
                    ),
                ),
            ],
            options={"table": "cassowary", "app": "models", "pk_attr": "cassowary_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="GuildCassowaryRoles",
            fields=[
                (
                    "category_role_id",
                    fields.BigIntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("role_id", fields.BigIntField()),
                (
                    "cassowary_id",
                    fields.OneToOneField(
                        "models.GuildCassowary",
                        source_field="cassowary_id_id",
                        db_constraint=True,
                        to_field="cassowary_id",
                        on_delete=OnDelete.CASCADE,
                    ),
                ),
            ],
            options={
                "table": "cassowary_roles",
                "app": "models",
                "pk_attr": "category_role_id",
            },
            bases=["Model"],
        ),
        ops.CreateModel(
            name="GuildData",
            fields=[
                (
                    "guild_id",
                    fields.BigIntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("prefix", fields.CharField(null=True, max_length=1)),
                ("modlog_id", fields.BigIntField(null=True)),
                ("modlog_staff_id", fields.BigIntField(null=True)),
                ("updates_id", fields.BigIntField(null=True)),
                ("logs_id", fields.BigIntField(null=True)),
                ("mute_id", fields.BigIntField(null=True)),
                ("moderator_id", fields.BigIntField(null=True)),
                ("helper_id", fields.BigIntField(null=True)),
                (
                    "filtering",
                    fields.BooleanField(
                        default=False, generated=False, null=False, unique=False
                    ),
                ),
                (
                    "removal",
                    fields.BooleanField(
                        default=False, generated=False, null=False, unique=False
                    ),
                ),
                (
                    "suppressed_channels",
                    ArrayField(null=True, default=list, element_type="BIGINT"),
                ),
                (
                    "monitoring_user",
                    fields.BooleanField(
                        default=False, generated=False, null=False, unique=False
                    ),
                ),
                (
                    "monitoring_message",
                    fields.BooleanField(
                        default=False, generated=False, null=False, unique=False
                    ),
                ),
                ("monitor_user_log_id", fields.BigIntField(null=True)),
                ("monitor_message_log_id", fields.BigIntField(null=True)),
            ],
            options={"table": "guild_data", "app": "models", "pk_attr": "guild_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="GuildSnapshot",
            fields=[
                (
                    "snapshot_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("category_id", fields.BigIntField()),
                ("channel_list", ArrayField(null=True, default=list, element_type="BIGINT")),
            ],
            options={"table": "snapshot", "app": "models", "pk_attr": "snapshot_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="GuildVoteLadder",
            fields=[
                (
                    "vote_ladder_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("vote_ladder_label", fields.CharField(max_length=256)),
                ("vote_ladder_roles", ArrayField(element_type="INT")),
                ("channel_id", fields.BigIntField()),
                ("threshold", fields.IntField()),
                ("minimum", fields.IntField()),
                ("timeout", fields.IntField()),
            ],
            options={"table": "vote_ladder", "app": "models", "pk_attr": "vote_ladder_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="GuildVote",
            fields=[
                (
                    "vote_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("message_id", fields.BigIntField()),
                ("message", fields.TextField(unique=False)),
                ("positive", fields.IntField(default=0)),
                ("negative", fields.IntField(default=0)),
                ("expiry", fields.IntField(default=604800)),
                (
                    "finished",
                    fields.BooleanField(
                        default=False, generated=False, null=False, unique=False
                    ),
                ),
                (
                    "vote_ladder_id",
                    fields.OneToOneField(
                        "models.GuildVoteLadder",
                        source_field="vote_ladder_id_id",
                        db_constraint=True,
                        to_field="vote_ladder_id",
                        on_delete=OnDelete.CASCADE,
                    ),
                ),
            ],
            options={"table": "vote", "app": "models", "pk_attr": "vote_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="HelperMessage",
            fields=[
                (
                    "helper_message_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("channel_id", fields.BigIntField()),
                ("message_id", fields.BigIntField()),
                ("role_id", ArrayField(element_type="BIGINT")),
            ],
            options={
                "table": "helper_message",
                "app": "models",
                "pk_attr": "helper_message_id",
            },
            bases=["Model"],
        ),
        ops.CreateModel(
            name="MemberOpt",
            fields=[
                (
                    "opt_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("user_id", fields.BigIntField()),
                ("channel_id", fields.BigIntField()),
            ],
            options={"table": "member_opt", "app": "models", "pk_attr": "opt_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="MemberReminder",
            fields=[
                (
                    "reminder_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("user_id", fields.BigIntField()),
                ("message", fields.CharField(max_length=1024)),
                ("timestamp", fields.DatetimeField(auto_now=False, auto_now_add=False)),
            ],
            options={"table": "member_reminder", "app": "models", "pk_attr": "reminder_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="MemberRole",
            fields=[
                (
                    "sticky_role_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("guild_id", fields.BigIntField()),
                ("user_id", fields.BigIntField()),
                ("role_ids", ArrayField(default=list, element_type="BIGINT")),
            ],
            options={"table": "member_role", "app": "models", "pk_attr": "sticky_role_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="StaffFilter",
            fields=[
                (
                    "filter_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("trigger", fields.CharField(max_length=1024)),
                (
                    "notify",
                    fields.BooleanField(
                        default=False, generated=False, null=False, unique=False
                    ),
                ),
            ],
            options={"table": "filter", "app": "models", "pk_attr": "filter_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="StaffMonitorMessage",
            fields=[
                (
                    "monitor_message_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                (
                    "disabled",
                    fields.BooleanField(
                        default=False, generated=False, null=False, unique=False
                    ),
                ),
                ("message", fields.CharField(max_length=1000)),
            ],
            options={
                "table": "monitor_message",
                "app": "models",
                "pk_attr": "monitor_message_id",
            },
            bases=["Model"],
        ),
        ops.CreateModel(
            name="StaffMonitorMessageGroups",
            fields=[
                (
                    "group_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("name", fields.CharField(max_length=256)),
                (
                    "disabled",
                    fields.BooleanField(
                        default=False, generated=False, null=False, unique=False
                    ),
                ),
                (
                    "monitor_messages",
                    fields.ManyToManyField(
                        "models.StaffMonitorMessage",
                        unique=True,
                        db_constraint=True,
                        through="monitor_message_groups_monitor_message",
                        forward_key="staffmonitormessage_id",
                        backward_key="monitor_message_groups_id",
                        related_name="groups",
                        on_delete=OnDelete.CASCADE,
                    ),
                ),
            ],
            options={
                "table": "monitor_message_groups",
                "app": "models",
                "pk_attr": "group_id",
            },
            bases=["Model"],
        ),
        ops.CreateModel(
            name="StaffMonitorUser",
            fields=[
                (
                    "monitor_user_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("user_id", fields.BigIntField()),
            ],
            options={"table": "monitor_user", "app": "models", "pk_attr": "monitor_user_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="StaffNote",
            fields=[
                (
                    "note_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("user_id", fields.BigIntField()),
                ("author_id", fields.BigIntField()),
                ("note", fields.CharField(max_length=1024)),
                ("timestamp", fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={"table": "note", "app": "models", "pk_attr": "note_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="StaffPunishment",
            fields=[
                (
                    "punishment_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                (
                    "punishment_type",
                    fields.CharEnumField(
                        description="WARN: warn\nKICK: kick\nTIMEOUT: timeout\nMUTE: mute\nBAN: ban\nUNKNOWN: unknown",
                        enum_type=PunishmentType,
                        max_length=7,
                    ),
                ),
                ("guild_id", fields.BigIntField()),
                ("user_display", fields.CharField(max_length=256)),
                ("user_id", fields.BigIntField()),
                ("staff_display", fields.CharField(max_length=256)),
                ("staff_id", fields.BigIntField()),
                ("reason", fields.CharField(max_length=1024)),
                (
                    "redacted",
                    fields.BooleanField(
                        default=False, generated=False, null=False, unique=False
                    ),
                ),
                ("message_id", fields.BigIntField(null=True)),
                ("message_staff_id", fields.BigIntField(null=True)),
                ("timestamp", fields.DatetimeField(auto_now=False, auto_now_add=True)),
                (
                    "expiry",
                    fields.DatetimeField(null=True, auto_now=False, auto_now_add=False),
                ),
                (
                    "expiry_complete",
                    fields.BooleanField(
                        default=True, generated=False, null=False, unique=False
                    ),
                ),
            ],
            options={"table": "punishment", "app": "models", "pk_attr": "punishment_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="StaffReaction",
            fields=[
                (
                    "reaction_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("channel_id", fields.BigIntField()),
                ("message_id", fields.BigIntField()),
            ],
            options={"table": "reaction", "app": "models", "pk_attr": "reaction_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="StaffButtonRole",
            fields=[
                (
                    "button_role_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("emoji_id", fields.BigIntField()),
                ("label", fields.CharField(max_length=256)),
                ("role_ids", ArrayField(element_type="INT")),
                (
                    "reaction_id",
                    fields.OneToOneField(
                        "models.StaffReaction",
                        source_field="reaction_id_id",
                        db_constraint=True,
                        to_field="reaction_id",
                        on_delete=OnDelete.CASCADE,
                    ),
                ),
            ],
            options={"table": "buttonrole", "app": "models", "pk_attr": "button_role_id"},
            bases=["Model"],
        ),
        ops.CreateModel(
            name="StaffTag",
            fields=[
                (
                    "tag_id",
                    fields.IntField(
                        generated=True, primary_key=True, unique=True, db_index=True
                    ),
                ),
                ("trigger", fields.CharField(max_length=256)),
                ("output", fields.CharField(max_length=1024)),
                (
                    "disabled",
                    fields.BooleanField(
                        default=False, generated=False, null=False, unique=False
                    ),
                ),
            ],
            options={"table": "tag", "app": "models", "pk_attr": "tag_id"},
            bases=["Model"],
        ),
    ]
