from unittest.mock import Mock

import discord


class MockMessage:
    def __init__(self, id=123456789, content="Test message", channel=None, embed=None):
        self.id = id
        self.content = content
        self.channel = channel
        self.author = None
        self.embed = embed
        self.embeds = [embed] if embed else []
        self.jump_url = f"https://discord.com/channels/111/222/{id}"
        self.reactions = []

    async def delete(self):
        pass

    async def edit(self, content=None, embed=None):
        if content is not None:
            self.content = content
        if embed is not None:
            self.embed = embed
            self.embeds = [embed]

    async def clear_reaction(self, emoji):
        self.reactions = [r for r in self.reactions if r.emoji != emoji]


class MockChannel:
    def __init__(self, id=987654321, name="test-channel", guild=None):
        self.id = id
        self.name = name
        self.guild = guild
        self.messages = []
        self._message_counter = 1000000000

    async def send(self, content=None, embed=None):
        message = MockMessage(id=self._message_counter, content=content or "", channel=self)
        self._message_counter += 1
        self.messages.append(message)
        return message

    async def fetch_message(self, message_id):
        for msg in self.messages:
            if msg.id == message_id:
                return msg

        mock_response = Mock()
        mock_response.status = 404
        raise discord.NotFound(response=mock_response, message="Message not found")

    def history(self, limit=100):
        class HistoryIterator:
            def __init__(self, messages, limit):
                self.messages = messages[:limit]
                self.index = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.index >= len(self.messages):
                    raise StopAsyncIteration
                msg = self.messages[self.index]
                self.index += 1
                return msg

        return HistoryIterator(self.messages, limit)

    async def purge(self, limit):
        to_delete = self.messages[:limit]
        self.messages = self.messages[limit:]
        return to_delete


class MockRole:
    def __init__(self, id, name="Test Role", position=1, guild=None):
        self.id = id
        self.name = name
        self.position = position
        self.mention = f"<@&{id}>"
        self.guild = guild


EVERYONE_ROLE = MockRole(id=0, name="@everyone", position=0)


class MockMember:
    def __init__(self, id=111111111, name="TestUser", guild=None, roles=None):
        self.id = id
        self.name = name
        self.display_name = name
        self.guild = guild
        self.roles = roles or []
        self.mention = f"<@{id}>"
        self.bot = False

    async def add_roles(self, *roles, reason=None):
        for role in roles:
            if role not in self.roles:
                self.roles.append(role)

    async def remove_roles(self, *roles, reason=None):
        for role in roles:
            if role in self.roles:
                self.roles.remove(role)

    @property
    def top_role(self):
        if not self.roles:
            return EVERYONE_ROLE
        return max(self.roles, key=lambda r: r.position)


class MockUser:
    def __init__(self, id=111111111, name="TestUser", bot=False):
        self.id = id
        self.name = name
        self.display_name = name
        self.mention = f"<@{id}>"
        self.bot = bot
        self.display_avatar = type(
            "obj", (object,), {"url": "https://example.com/avatar.png"}
        )()


class MockGuild:
    def __init__(self, id=123456789):
        self.id = id
        self.name = "Test Guild"
        self.members = []
        self.roles = []
        self.channels = []
        self.banned_users = []

    def get_member(self, user_id):
        for member in self.members:
            if member.id == user_id:
                return member
        return None

    def get_role(self, role_id):
        for role in self.roles:
            if role.id == role_id:
                return role
        return None

    def get_channel(self, channel_id):
        for channel in self.channels:
            if channel.id == channel_id:
                return channel
        return None

    async def ban(self, user, reason=None):
        if user in self.banned_users:
            raise Exception("User already banned")
        self.banned_users.append(user)

    async def unban(self, user, reason=None):
        if user in self.banned_users:
            self.banned_users.remove(user)


class MockContext:
    def __init__(self, guild=None, author=None, channel=None):
        self.guild = guild or MockGuild()
        self.author = author or MockUser(id=999999999, name="Moderator")
        self.channel = channel or MockChannel(guild=self.guild)
        self.messages_sent = []

    async def send(self, content=None, embed=None, delete_after=None, view=None):
        message = MockMessage(content=content or "", embed=embed)
        self.messages_sent.append(message)
        return message


class MockBot:
    def __init__(self):
        self.users = {}
        self.guilds = []

    def get_user(self, user_id):
        return self.users.get(user_id)

    async def fetch_user(self, user_id):
        return self.users.get(user_id)

    def get_guild(self, guild_id):
        for guild in self.guilds:
            if guild.id == guild_id:
                return guild
        return None

    def get_channel(self, channel_id):
        for guild in self.guilds:
            channel = guild.get_channel(channel_id)
            if channel:
                return channel
        return None


class MockAuditLogEntry:
    def __init__(self, action, target, user, guild, reason=None):
        self.action = action
        self.target = target
        self.user = user
        self.guild = guild
        self.reason = reason
        self.before = type("obj", (object,), {"roles": []})()
        self.after = type("obj", (object,), {"roles": []})()


class MockReaction:
    def __init__(self, emoji, message=None):
        self.emoji = emoji
        self.message = message
