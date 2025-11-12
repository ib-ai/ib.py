from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "snapshot" DROP COLUMN "channel_type";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "snapshot" ADD "channel_type" VARCHAR(5) NOT NULL;
        COMMENT ON COLUMN "snapshot"."channel_type" IS 'TEXT: text\nVOICE: voice\nFORUM: forum';"""


MODELS_STATE = (
    "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"
    "C2/l35Y="
)
