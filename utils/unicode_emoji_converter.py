import emojis
from discord.ext import commands

class UnicodeEmojiNotFound(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__(f'Unicode emoji "{argument}" not found.')

class UnicodeEmojiConverter(commands.Converter):
    async def convert(self, ctx, argument):
        emoji = emojis.db.get_emoji_by_code(argument)
        if not emoji:
            raise UnicodeEmojiNotFound(argument)
        return emoji.emoji # The codepoint