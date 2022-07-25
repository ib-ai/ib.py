import json
import enum
from gino import Gino

db = Gino()

with open('./config.json', 'r') as config_json:
    config = json.load(config_json)

# Schema List

schemas_list = ["guild", "staff", "helper", "member"]

# Custom Enums

class PunishmentType(enum.Enum):
    KICK = enum.auto(),
    MUTE = enum.auto(),
    BAN = enum.auto(),
    UNKNOWN = enum.auto()

class ChannelType(enum.Enum):
    TEXT = enum.auto(),
    VOICE = enum.auto()

# Server tables

class GuildData(db.Model):
    __tablename__ = "guild_data"
    __table_args__ = {"schema": "guild"}

    guild_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=False)
    prefix = db.Column(db.CHAR(1))
    modlog_id = db.Column(db.BigInteger())
    modlog_staff_id = db.Column(db.BigInteger())
    updates_id = db.Column(db.BigInteger())
    logs_id = db.Column(db.BigInteger())
    mute_id = db.Column(db.BigInteger())
    moderator_id = db.Column(db.BigInteger())
    helper_id = db.Column(db.BigInteger())
    filtering = db.Column(db.Boolean(), default=False)
    removal = db.Column(db.Boolean(), default=False)
    monitoring = db.Column(db.Boolean(), default=False)
    monitor_user_log_id = db.Column(db.BigInteger())
    monitor_message_log_id = db.Column(db.BigInteger())

class GuildFilter(db.Model):
    __tablename__ = "filter"
    __table_args__ = {"schema": "guild"}

    filter_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    trigger = db.Column(db.Text())
    notify = db.Column(db.Boolean())

class GuildSnapshot(db.Model):
    __tablename__ = "snapshot"
    __table_args__ = {"schema": "guild"}

    category_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=False)
    channel_type = db.Column(db.Enum(ChannelType, schema="guild"))
    channel_list = db.Column(db.ARRAY(db.BigInteger()))

class GuildCassowary(db.Model):
    __tablename__ = "cassowary"
    __table_args__ = {"schema": "guild"}

    cassowary_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    label = db.Column(db.Text())
    penguin = db.Column(db.Boolean())

class GuildCassowaryRoles(db.Model):
    __tablename__ = "cassowary_roles"
    __table_args__ = {"schema": "guild"}

    category_role_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=False)
    role_id = db.Column(db.BigInteger())
    cassowary_id = db.Column(db.Integer(), db.ForeignKey(GuildCassowary.cassowary_id))

class GuildVoteLadder(db.Model):
    __tablename__ = "vote_ladder"
    __table_args__ = {"schema": "guild"}

    ladder_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    ladder_label = db.Column(db.Text())
    ladder_roles = db.Column(db.ARRAY(db.BigInteger()))
    channel_id = db.Column(db.Text())
    threshold = db.Column(db.Integer())
    minimum = db.Column(db.Integer())
    timeout = db.Column(db.Integer())

class GuildVote(db.Model):
    __tablename__ = "vote"
    __table_args__ = {"schema": "guild"}

    vote_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    ladder_number = db.Column(db.Integer())
    message = db.Column(db.Text())
    positive = db.Column(db.Integer(), unique=False, default=0)
    negative = db.Column(db.Integer(), unique=False, default=0)
    expiry = db.Column(db.Integer())
    finished = db.Column(db.Boolean())
    ladder_id = db.Column(db.Integer(), db.ForeignKey(GuildVoteLadder.ladder_id))

# Staff Tables

class StaffTag(db.Model):
    __tablename__ = "tag"
    __table_args__ = {"schema": "staff"}

    tag_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    trigger = db.Column(db.Text())
    output = db.Column(db.Text())
    disabled = db.Column(db.Boolean())

class StaffNote(db.Model):
    __tablename__ = "note"
    __table_args__ = {"schema": "staff"}

    note_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger())
    author_id = db.Column(db.BigInteger())
    timestamp = db.Column(db.TIMESTAMP())
    data = db.Column(db.Text())

class StaffMonitorUser(db.Model):
    __tablename__ = "monitor_user"
    __table_args__ = {"schema": "staff"}

    monitor_user_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger())

class StaffMonitorMessage(db.Model):
    __tablename__ = "monitor_message"
    __table_args__ = {"schema": "staff"}

    monitor_message_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    message = db.Column(db.Text())

class StaffReaction(db.Model):
    __tablename__ = "reaction"
    __table_args__ = {"schema": "staff"}

    reaction_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    channel_id = db.Column(db.BigInteger())
    message_id = db.Column(db.BigInteger())
    emoji_id = db.Column(db.BigInteger())

class StaffReactionRole(db.Model):
    __tablename__ = "reaction_role"
    __table_args__ = {"schema": "staff"}

    reaction_role_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    role_id = db.Column(db.BigInteger())
    positive = db.Column(db.Boolean())
    reaction_id = db.Column(db.Integer(), db.ForeignKey(StaffReaction.reaction_id))

class StaffPunishment(db.Model):
    __tablename__ = "punishment"
    __table_args__ = {"schema": "staff"}

    punishment_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    case_id = db.Column(db.Integer())
    punishment_type = db.Column(db.Enum(PunishmentType, schema="staff"))
    user_display = db.Column(db.Text())
    user_id = db.Column(db.BigInteger())
    staff_display = db.Column(db.Text())
    staff_id = db.Column(db.BigInteger())
    reason = db.Column(db.Text())
    redacted = db.Column(db.Boolean())
    message_id = db.Column(db.BigInteger())
    message_staff_id = db.Column(db.BigInteger())
    expiry = db.Column(db.Integer())

# Helper Tables

class HelperData(db.Model):
    __tablename__ = "helper_data"
    __table_args__ = {"schema": "helper"}

    user_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=False)
    inactive = db.Column(db.Boolean())

class HelperMessage(db.Model):
    __tablename__ = "helper_message"
    __table_args__ = {"schema": "helper"}

    helper_message_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    channel_id = db.Column(db.BigInteger())
    message_id = db.Column(db.BigInteger())
    role_id = db.Column(db.BigInteger())

# Member Tables

class MemberData(db.Model):
    __tablename__ = "member_data"
    __table_args__ = {"schema": "member"}

    user_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=False)
    join_override = db.Column(db.Text())

class MemberRole(db.Model):
    __tablename__ = "role"
    __table_args__ = {"schema": "member"}

    user_role_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger())
    role_id = db.Column(db.BigInteger())

class MemberOpt(db.Model):
    __tablename__ = "opt"
    __table_args__ = {"schema": "member"}

    opt_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger())
    channel_id = db.Column(db.BigInteger())

class MemberReminder(db.Model):
    __tablename__ = "reminder"
    __table_args__ = {"schema": "member"}

    reminder_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    text = db.Column(db.Text())
    time = db.Column(db.Integer())
    user_id = db.Column(db.BigInteger())

async def db_main():
    """
    Create the tables and columns if they don't already exist,
    """

    await db.set_bind('postgresql+asyncpg://{}:{}@{}:5432/{}'.format(config['db_user'], config['db_password'], config['db_host'], config['db_database']))

    # Creates the schemas
    for schema_name in schemas_list:
        sql = f"CREATE SCHEMA IF NOT EXISTS {schema_name}"
        await db.status(db.text(sql))
    
    await db.gino.create_all()