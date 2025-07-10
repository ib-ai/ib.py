import unittest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
from discord.ext import commands
from ib_py.cogs.tags import Tags

class TestTagsCog(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        intents = discord.Intents.all()
        self.bot = commands.Bot(command_prefix="&", intents=intents)
        self.cog = Tags(self.bot)
        self.ctx = MagicMock()
        self.ctx.send = AsyncMock()

    @patch("ib_py.db.models.StaffTag.update_or_create", new_callable=AsyncMock)
    @patch("ib_py.db.cached.get_all_tags.cache_clear")
    async def test_tag_create_valid(self, mock_cache_clear, mock_update_or_create):
        # Simulate a valid trigger/output pair
        trigger = MagicMock()
        trigger.__str__.return_value = "hello"  # So f"{trigger}" returns "hello"
        trigger.pattern = "hello"
        output = "world"

        await self.cog.tag_create(self, self.ctx, trigger=trigger, output=output)

        # Check DB update call
        mock_update_or_create.assert_awaited_once_with(
            {"output": output}, trigger=trigger
        )

        # Check cache cleared
        mock_cache_clear.assert_called_once()

        # Check message sent
        self.ctx.send.assert_awaited_once_with(
            f"Created tag `{trigger}` with output `{output}`."
        )

    @patch("ib_py.db.models.StaffTag.update_or_create", new_callable=AsyncMock)
    async def test_tag_create_too_long_trigger(self, mock_update_or_create):
        long_trigger = "a" * 300  # Over limit
        output = "valid output"

        await self.cog.tag_create(self, self.ctx, long_trigger, output)

        self.ctx.send.assert_awaited_once()
        self.assertIn("trigger is too long", self.ctx.send.await_args[0][0])
        mock_update_or_create.assert_not_called()

    @patch("ib_py.db.models.StaffTag.update_or_create", new_callable=AsyncMock)
    async def test_tag_create_too_long_output(self, mock_update_or_create):
        trigger = "valid"
        long_output = "a" * 3000  # Over limit

        await self.cog.tag_create(self, self.ctx, trigger, long_output)

        self.ctx.send.assert_awaited_once()
        self.assertIn("output is too long", self.ctx.send.await_args[0][0])
        mock_update_or_create.assert_not_called()

if __name__ == "__main__":
    unittest.main()
