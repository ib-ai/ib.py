import discord
from discord.ext import commands
from utils.config import subjects 


class Helper(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot        
        self.pairs = subjects.split(';')
        self.subjects = {int(pair.split(',')[0]):int(pair.split(',')[1]) for pair in self.pairs}
        
        @bot.tree.context_menu(name="Toggle Pin")
        async def pin_message(interaction: discord.Interaction, message: discord.Message):
            # checks if the person issuing the action is a helper
            helper_role_id = self.subjects[interaction.channel.id]
            if not any(helper_role_id == role.id for role in interaction.user.roles):
                return await interaction.response.send_message('Only subject helpers can pin/unpin messages.', ephemeral=True)
            # checks if the command is being issued in a subject channel
            if interaction.channel.id not in self.subjects.keys():
                return await interaction.response.send_message('You may only pin messages in subject channels.', ephemeral=True)
            try:
                if message.pinned:
                    await message.unpin()
                    return await interaction.response.send_message('The message was successfully unpinned')
                else:
                    await message.pin()
                    return await interaction.response.send_message('The message was successfully pinned')
            except discord.Forbidden:
                return await interaction.response.send_message('The bot does not have permission to pin/unpin messages.', ephemeral=True)
            except discord.NotFound:
                return await interaction.response.send_message('Invalid message ID provided.', ephemeral=True)
            except discord.HTTPException:
                if not message.pinned:
                    return await interaction.response.send_message('You have reached the maximum number of pins for this channel.', ephemeral=True)
                else:
                    return await interaction.response.send_message('The message could not be unpinned', ephemeral=True)
                
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
    async def pin(self, ctx: commands.Context, message: discord.Message = None):
        """
        Pin a message to a channel.
        """
        if message is None:
            return await ctx.send("Please provide a message to pin.")
        helper_role_id = self.subjects[ctx.channel.id]
        if not any(helper_role_id == role.id for role in ctx.author.roles):
            return await ctx.send('Only subject helpers can pin messages')
        if ctx.channel.id not in self.subjects.keys():
            return await ctx.send('You may only pin messages in subject channels.')
        # checks if the message is already pinned
        if message.pinned:
            return await ctx.send('The message is already pinned.')
        # pins the message
        try:
            await message.pin()
            await ctx.send('The message was successfully pinned.')
        except discord.Forbidden:
            return await ctx.send('The bot does not have the permission to unpin messages.')
        except discord.NotFound:
             return await ctx.send('Invalid message ID provided.')
        except discord.HTTPException:
             return await ctx.send('You have reached the maximum number of pins for this channel.')
            
    @commands.hybrid_command()
    async def unpin(self, ctx: commands.Context, message: discord.Message = None):
        """
        Unpin a message from a channel.
        """
        if message is None:
            return await ctx.send("Please provide a message to unpin.")
        helper_role_id = self.subjects[ctx.channel.id]
        if helper_role_id not in [role.id for role in ctx.author.roles]:
            return await ctx.send('Only subject helpers can unpin messages.')
        if ctx.channel.id not in self.subjects.keys():
            return await ctx.send('You may only unpin messages in subject channels.')
        # checks if the message is already unpinned
        if not message.pinned:
            return await ctx.send('The message is already unpinned.')
        # unpins the message
        try:
            await message.unpin()
            return await ctx.send('The message was successfully unpinned.')
        except discord.Forbidden:
            return await ctx.send('The bot does not have the permission to unpin messages.')
        except discord.NotFound:
             return await ctx.send('Invalid message ID provided.')
        except discord.HTTPException:
             return await ctx.send('The message could not be unpinned.')
 
async def setup(bot: commands.Bot):
    await bot.add_cog(Helper(bot))
