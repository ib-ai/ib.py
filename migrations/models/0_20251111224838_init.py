from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "cassowary" (
    "cassowary_id" SERIAL NOT NULL PRIMARY KEY,
    "label" VARCHAR(256) NOT NULL,
    "penguin" BOOL NOT NULL DEFAULT False
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
    "filtering" BOOL NOT NULL DEFAULT False,
    "removal" BOOL NOT NULL DEFAULT False,
    "suppressed_channels" BIGINT[],
    "monitoring_user" BOOL NOT NULL DEFAULT False,
    "monitoring_message" BOOL NOT NULL DEFAULT False,
    "monitor_user_log_id" BIGINT,
    "monitor_message_log_id" BIGINT
);
CREATE TABLE IF NOT EXISTS "snapshot" (
    "snapshot_id" SERIAL NOT NULL PRIMARY KEY,
    "category_id" BIGINT NOT NULL,
    "channel_type" VARCHAR(5) NOT NULL,
    "channel_list" BIGINT[]
);
COMMENT ON COLUMN "snapshot"."channel_type" IS 'TEXT: text\nVOICE: voice\nFORUM: forum';
CREATE TABLE IF NOT EXISTS "vote_ladder" (
    "vote_ladder_id" SERIAL NOT NULL PRIMARY KEY,
    "vote_ladder_label" VARCHAR(256) NOT NULL,
    "vote_ladder_roles" INT[] NOT NULL,
    "channel_id" BIGINT NOT NULL,
    "threshold" INT NOT NULL,
    "minimum" INT NOT NULL,
    "timeout" INT NOT NULL
);
CREATE TABLE IF NOT EXISTS "vote" (
    "vote_id" SERIAL NOT NULL PRIMARY KEY,
    "message_id" BIGINT NOT NULL,
    "message" TEXT NOT NULL,
    "positive" INT NOT NULL DEFAULT 0,
    "negative" INT NOT NULL DEFAULT 0,
    "expiry" INT NOT NULL DEFAULT 604800,
    "finished" BOOL NOT NULL DEFAULT False,
    "vote_ladder_id_id" INT NOT NULL UNIQUE REFERENCES "vote_ladder" ("vote_ladder_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "helper_message" (
    "helper_message_id" SERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL,
    "message_id" BIGINT NOT NULL,
    "role_id" BIGINT[] NOT NULL
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
    "timestamp" TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS "member_role" (
    "user_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "role_ids" INT[] NOT NULL
);
CREATE TABLE IF NOT EXISTS "filter" (
    "filter_id" SERIAL NOT NULL PRIMARY KEY,
    "trigger" VARCHAR(1024) NOT NULL,
    "notify" BOOL NOT NULL DEFAULT False
);
CREATE TABLE IF NOT EXISTS "monitor_message" (
    "monitor_message_id" SERIAL NOT NULL PRIMARY KEY,
    "disabled" BOOL NOT NULL DEFAULT False,
    "message" VARCHAR(1000) NOT NULL
);
CREATE TABLE IF NOT EXISTS "monitor_message_groups" (
    "group_id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(256) NOT NULL,
    "disabled" BOOL NOT NULL DEFAULT False
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
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "punishment" (
    "punishment_id" SERIAL NOT NULL PRIMARY KEY,
    "punishment_type" VARCHAR(7) NOT NULL,
    "user_display" VARCHAR(256) NOT NULL,
    "user_id" BIGINT NOT NULL,
    "staff_display" VARCHAR(256) NOT NULL,
    "staff_id" BIGINT NOT NULL,
    "reason" VARCHAR(1024) NOT NULL,
    "redacted" BOOL NOT NULL DEFAULT False,
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
    "role_ids" INT[] NOT NULL,
    "reaction_id_id" INT NOT NULL UNIQUE REFERENCES "reaction" ("reaction_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "tag" (
    "tag_id" SERIAL NOT NULL PRIMARY KEY,
    "trigger" VARCHAR(256) NOT NULL,
    "output" VARCHAR(1024) NOT NULL,
    "disabled" BOOL NOT NULL DEFAULT False
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "monitor_message_groups_monitor_message" (
    "monitor_message_groups_id" INT NOT NULL REFERENCES "monitor_message_groups" ("group_id") ON DELETE CASCADE,
    "staffmonitormessage_id" INT NOT NULL REFERENCES "monitor_message" ("monitor_message_id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_monitor_mes_monitor_a6be69" ON "monitor_message_groups_monitor_message" ("monitor_message_groups_id", "staffmonitormessage_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
    "XP0L7Mx9foDcZN08vDv+K9W18="
)
