from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "cassowary" (
    "cassowary_id" SERIAL NOT NULL PRIMARY KEY,
    "label" VARCHAR(256) NOT NULL,
    "penguin" BOOL NOT NULL  DEFAULT False
);
CREATE TABLE IF NOT EXISTS "cassowary_roles" (
    "category_role_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "role_id" BIGINT NOT NULL,
    "cassowary_id_id" INT NOT NULL UNIQUE REFERENCES "cassowary" ("cassowary_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "guild_data" (
    "guild_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "prefix" VARCHAR(1),
    "modlog_id" BIGINT,
    "modlog_staff_id" BIGINT,
    "updates_id" BIGINT,
    "logs_id" BIGINT,
    "mute_id" BIGINT,
    "moderator_id" BIGINT,
    "helper_id" BIGINT,
    "filtering" BOOL NOT NULL  DEFAULT False,
    "removal" BOOL NOT NULL  DEFAULT False,
    "monitoring" BOOL NOT NULL  DEFAULT False,
    "monitor_user_log_id" BIGINT,
    "monitor_message_log_id" BIGINT
);
CREATE TABLE IF NOT EXISTS "snapshot" (
    "snapshot_id" SERIAL NOT NULL PRIMARY KEY,
    "category_id" BIGINT NOT NULL,
    "channel_type" VARCHAR(5) NOT NULL,
    "channel_list" int[] NOT NULL
);
COMMENT ON COLUMN "snapshot"."channel_type" IS 'TEXT: text\nVOICE: voice';
CREATE TABLE IF NOT EXISTS "vote_ladder" (
    "vote_ladder_id" SERIAL NOT NULL PRIMARY KEY,
    "vote_ladder_label" VARCHAR(256) NOT NULL,
    "vote_ladder_roles" int[] NOT NULL,
    "channel_id" BIGINT NOT NULL,
    "threshold" INT NOT NULL,
    "minimum" INT NOT NULL,
    "timeout" INT NOT NULL
);
CREATE TABLE IF NOT EXISTS "vote" (
    "vote_id" SERIAL NOT NULL PRIMARY KEY,
    "message_id" BIGINT NOT NULL,
    "message" TEXT NOT NULL,
    "positive" INT NOT NULL  DEFAULT 0,
    "negative" INT NOT NULL  DEFAULT 0,
    "expiry" INT NOT NULL  DEFAULT 604800,
    "finished" BOOL NOT NULL  DEFAULT False,
    "vote_ladder_id_id" INT NOT NULL UNIQUE REFERENCES "vote_ladder" ("vote_ladder_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "helper_message" (
    "helper_message_id" SERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL,
    "message_id" BIGINT NOT NULL,
    "role_id" BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS "member_opt" (
    "opt_id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "channel_id" BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS "member_reminder" (
    "reminder_id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "message" VARCHAR(1024) NOT NULL,
    "timestamp" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "member_role" (
    "user_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "role_ids" int[] NOT NULL
);
CREATE TABLE IF NOT EXISTS "filter" (
    "filter_id" SERIAL NOT NULL PRIMARY KEY,
    "trigger" VARCHAR(1024) NOT NULL,
    "notify" BOOL NOT NULL  DEFAULT False
);
CREATE TABLE IF NOT EXISTS "monitor_message" (
    "monitor_message_id" SERIAL NOT NULL PRIMARY KEY,
    "message" VARCHAR(1000) NOT NULL
);
CREATE TABLE IF NOT EXISTS "monitor_user" (
    "monitor_user_id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS "note" (
    "note_id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" BIGINT NOT NULL,
    "author_id" BIGINT NOT NULL,
    "note" VARCHAR(1024) NOT NULL,
    "timestamp" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "punishment" (
    "punishment_id" SERIAL NOT NULL PRIMARY KEY,
    "punishment_type" VARCHAR(7) NOT NULL,
    "user_display" VARCHAR(256) NOT NULL,
    "user_id" BIGINT NOT NULL,
    "staff_display" VARCHAR(256) NOT NULL,
    "staff_id" BIGINT NOT NULL,
    "reason" VARCHAR(1024) NOT NULL,
    "redacted" BOOL NOT NULL  DEFAULT False,
    "message_id" BIGINT NOT NULL,
    "message_staff_id" BIGINT NOT NULL,
    "expiry" TIMESTAMPTZ
);
COMMENT ON COLUMN "punishment"."punishment_type" IS 'KICK: kick\nMUTE: mute\nBAN: ban\nUNKNOWN: unknown';
CREATE TABLE IF NOT EXISTS "reaction" (
    "reaction_id" SERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL,
    "message_id" BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS "buttonrole" (
    "button_role_id" SERIAL NOT NULL PRIMARY KEY,
    "emoji_id" BIGINT NOT NULL,
    "label" VARCHAR(256) NOT NULL,
    "role_ids" int[] NOT NULL,
    "reaction_id_id" INT NOT NULL UNIQUE REFERENCES "reaction" ("reaction_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "tag" (
    "tag_id" SERIAL NOT NULL PRIMARY KEY,
    "trigger" VARCHAR(256) NOT NULL,
    "output" VARCHAR(1024) NOT NULL,
    "disabled" BOOL NOT NULL  DEFAULT False
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
