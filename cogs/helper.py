import discord
from discord.ext import commands
from utils.config import subjects 


class Helper(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot        
        self.subjects_list = [pair.split(",") for pair in subjects.split(";")]
        self.subject_channels_list = [int(pair[0]) for pair in self.subjects_list]
        
        @bot.tree.context_menu(name="Toggle Pin")
        async def pin_message(interaction: discord.Interaction, message: discord.Message):
            # checks if the command is being issued in a subject channel
            if interaction.channel.id not in self.subject_channels_list:
                return await interaction.response.send_message('You may only pin messages in subject channels')
            # checks if the person issuing the action is a helper
            subject_helper_role  = [int(list[1]) for list in self.subjects_list if str(interaction.channel.id) in list][0]
            if subject_helper_role not in [role.id for role in interaction.user.roles]:
                return await interaction.response.send_message('Only subject helpers can pin/unpin messages')
            # unpins the message if pinned already
            if message.pinned:
                await message.unpin()
                return await interaction.response.send_message('The message was successfully unpinned')
            # pins the message if not the case
            else:
                await message.pin()
                await interaction.response.send_message('The message was successfully pinned')        
                
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Update helper message based on user helper/dehelper.
        """
        ...
        
            
    @commands.hybrid_command()
    async def helpermessage(self, ctx: commands.Context):
        """
        Send an updating list of helpers for a subject.
        """ 
        raise NotImplementedError('Command requires implementation and permission set-up.')
     
    @commands.hybrid_command()
    async def pin(self, ctx: commands.Context, message):
        """
        Pin a message to a channel.
        """
        if ctx.channel.id not in self.subject_channels_list:
            return await ctx.send('You may only pin messages in subject channels')
        subject_helper_role  = [int(list[1]) for list in self.subjects_list if str(ctx.channel.id) in list][0]
        if subject_helper_role not in [role.id for role in ctx.author.roles]:
            return await ctx.send('Only subject helpers can pin messages')
        # ensure that a valid message is referenced
        try:
            message = await ctx.channel.fetch_message(message)
        # checks if the message is already pinned
            if message.pinned:
                return await ctx.send('The message is already pinned.')
        # pins the message
            await message.pin()
            return await ctx.send('The message was successfully pinned')
        except discord.NotFound:
            return await ctx.send('Invalid message ID provided. You must be in the same channel as the message.')
            
    @commands.hybrid_command()
    async def unpin(self, ctx: commands.Context, message):
        """
        Unpin a message from a channel.
        """
        if ctx.channel.id not in self.subject_channels_list:
            return await ctx.send('You may only unpin messages in subject channels')
        subject_helper_role  = [int(list[1]) for list in self.subjects_list if str(ctx.channel.id) in list][0]
        if subject_helper_role not in [role.id for role in ctx.author.roles]:
            return await ctx.send('Only subject helpers can pin messages')
        try:
            message = await ctx.channel.fetch_message(message)
        # checks if the message is already unpinned
            if not message.pinned:
                return await ctx.send('The message is already unpinned')
        # unpins the message
            await message.unpin()
            return await ctx.send('The message was successfully unpinned')
        except discord.NotFound:
            return await ctx.send('Invalid message ID provided. You must be in the same channel as the message')
 
async def setup(bot: commands.Bot):
    await bot.add_cog(Helper(bot))