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

    @patch("ib_py.db.cached.get_all_tags.cache_clear")
    @patch("ib_py.db.models.StaffTag.filter")
    async def test_tag_delete_exists(self, mock_filter, mock_cache_clear):
        trigger = MagicMock()
        trigger.__str__.return_value = "hello"
        trigger.pattern = "hello"

        fake_tag = MagicMock()
        fake_tag.output = "world"
        fake_tag.delete = AsyncMock()  # Make delete awaitable

        mock_filter.return_value.get_or_none = AsyncMock(return_value=fake_tag)

        # Act
        await self.cog.tag_delete(self, self.ctx, trigger)

        # Assert
        fake_tag.delete.assert_awaited_once()
        mock_cache_clear.assert_called_once()
        self.ctx.send.assert_awaited_once_with(
            f"Deleted tag `{trigger}` with output `{fake_tag.output}`."
        )

    @patch("ib_py.db.cached.get_all_tags.cache_clear")
    @patch("ib_py.cogs.tags.StaffTag.filter")
    async def test_tag_delete_not_exists(self, mock_filter, mock_cache_clear):
        # Arrange
        trigger = MagicMock()
        trigger.__str__.return_value = "hello"
        trigger.pattern = "hello"

        mock_filter.return_value.get_or_none = AsyncMock(return_value=None)

        # Act
        await self.cog.tag_delete(self, self.ctx, trigger)

        # Assert
        mock_filter.assert_called_once_with(trigger=trigger)
        mock_cache_clear.assert_not_called()
        self.ctx.send.assert_awaited_once_with(
            f"Tag `{trigger}` does not exist."
        )
    
    @patch("ib_py.cogs.tags.available_subcommands", new_callable=AsyncMock)
    async def test_tag_invokes_available_subcommands(self, mock_available_subcommands):
        # Act
        await self.cog.tag(self, self.ctx)

        # Assert
        mock_available_subcommands.assert_awaited_once_with(self.ctx)

    @patch("ib_py.cogs.tags.paginated_embed_menus")
    @patch("ib_py.cogs.tags.PaginationView")
    @patch("ib_py.cogs.tags.get_all_tags", new_callable=AsyncMock)
    async def test_tag_list(self, mock_get_all_tags, mock_pagination_view, mock_paginated_embed_menus):
        # Setup mocks for tags returned by get_all_tags
        mock_get_all_tags.return_value = [
            MagicMock(trigger="tag1", output="output1", disabled=False),
            MagicMock(trigger="tag2", output="output2", disabled=True),
        ]

        # paginated_embed_menus returns a list of embeds
        mock_paginated_embed_menus.return_value = ["embed1", "embed2"]

        # Setup PaginationView mock instance with async method
        pagination_instance = MagicMock()
        pagination_instance.return_paginated_embed_view = AsyncMock(return_value=("tag_embed", "tag_view"))

        # When PaginationView(...) is called, return the mock instance
        mock_pagination_view.return_value = pagination_instance

        # Call your method
        await self.cog.tag_list(self, self.ctx)

        # Assert ctx.send called with correct embed and view
        self.ctx.send.assert_awaited_once_with(embed="tag_embed", view="tag_view")

if __name__ == "__main__":
    unittest.main()
