import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord
from discord.ext import commands

from ib_py.cogs.monitor import Monitor


class TestMonitorCog(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        intents = discord.Intents.all()
        self.bot = commands.Bot(command_prefix="&", intents=intents)
        self.cog = Monitor(self.bot)
        self.ctx = MagicMock()
        self.ctx.send = AsyncMock()
    
    @patch("ib_py.cogs.monitor.get_guild_data", new_callable=AsyncMock)
    @patch("ib_py.cogs.monitor.get_all_monitor_users", new_callable=AsyncMock)
    @patch("ib_py.cogs.monitor.get_all_monitor_messages", new_callable=AsyncMock)
    @patch("ib_py.cogs.monitor.log_suspicious_message", new_callable=AsyncMock)
    async def test_on_message_monitored_pattern(
        self,
        mock_log_suspicious_message,
        mock_get_all_monitor_messages,
        mock_get_all_monitor_users,
        mock_get_guild_data
    ):
        # Mock message
        message = MagicMock()
        message.guild = MagicMock(id=123)
        message.author.bot = False
        message.author.id = 456 
        message.content = "suspicious phrase here"

        # Mock guild data
        guild_data = MagicMock()
        guild_data.monitoring_user = False
        guild_data.monitor_user_log_id = None
        guild_data.monitoring_message = True
        guild_data.monitor_message_log_id = 999
        mock_get_guild_data.return_value = guild_data

        # Mock monitor messages
        pattern_mock = MagicMock(message="suspicious phrase", disabled=False)
        mock_get_all_monitor_messages.return_value = [pattern_mock]

        # Act
        await self.cog.on_message(message)

        # Assert
        mock_log_suspicious_message.assert_awaited_once_with(999, message)