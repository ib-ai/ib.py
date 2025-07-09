from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "member_reminder" ALTER COLUMN "timestamp" TYPE TIMESTAMPTZ USING "timestamp"::TIMESTAMPTZ;
        ALTER TABLE "member_reminder" ALTER COLUMN "timestamp" TYPE TIMESTAMPTZ USING "timestamp"::TIMESTAMPTZ;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "member_reminder" ALTER COLUMN "timestamp" TYPE TIMESTAMPTZ USING "timestamp"::TIMESTAMPTZ;
        ALTER TABLE "member_reminder" ALTER COLUMN "timestamp" TYPE TIMESTAMPTZ USING "timestamp"::TIMESTAMPTZ;"""
