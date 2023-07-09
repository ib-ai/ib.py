import discord
from discord.ext import commands
import toml


class Helper(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot        
        self.subjects = toml.load('config.toml')['subjects']
        self.helper_ids = self.subjects.keys()
        self.subject_channels = [self.subjects[role] for role in self.helper_ids]
        self.ctx_menu = discord.app_commands.ContextMenu(
			name='Toggle Pin',
			callback=self.toggle_pin,
		)
        self.bot.tree.add_command(self.ctx_menu)
        
    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)
        
    async def send_error(self, obj, message):
        if isinstance(obj, commands.Context):
            return await obj.send(message)
        else:
            return await obj.response.send_message(message, ephemeral=True)
    
    async def check_permissions(self, obj):
        user = obj.author if isinstance(obj, commands.Context) else obj.user
        channel = obj.channel.id
        user_role_ids = [str(role.id) for role in user.roles]
        if not any(role in self.helper_ids for role in user_role_ids):
            message = 'Only subject helpers can pin messages.' 
            await self.send_error(obj, message)
            return False
        if channel not in self.subject_channels:
            message = 'You may only pin messages in subject channels.'
            await self.send_error(obj, message)
            return False
        valid_channels = [self.subjects[role] for role in user_role_ids if role in self.helper_ids]
        if channel not in valid_channels:
            message = 'You may only pin messages in your respective subject channel.'
            await self.send_error(obj, message)
            return False
        return True

    async def toggle_pin(self, interaction: discord.Interaction, message: discord.Message):
        if await self.check_permissions(interaction):
            try:
                if message.pinned:
                    await message.unpin()
                    return await interaction.response.send_message('The message was successfully unpinned.')
                else:
                    await message.pin()
                    return await interaction.response.send_message('The message was successfully pinned.')
            except discord.Forbidden:
                return await interaction.response.send_message('The bot does not have permission to pin/unpin messages.', ephemeral=True)
            except discord.NotFound:
                return await interaction.response.send_message('Invalid message ID provided.', ephemeral=True)
            except discord.HTTPException:
                if not message.pinned:
                    return await interaction.response.send_message('You have reached the maximum number of pins for this channel.', ephemeral=True)
                else:
                    return await interaction.response.send_message('The message could not be unpinned.', ephemeral=True)

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
        if await self.check_permissions(ctx):
            if message.pinned:
                return await ctx.send('The message is already pinned.')
            try:
                await message.pin()
                return await ctx.send('The message was successfully pinned.')
            except discord.Forbidden:
                return await ctx.send('The bot does not have the permission to pin/unpin messages.')
            except discord.NotFound:
                return await ctx.send('Invalid message ID provided.')
            except discord.HTTPException:
                return await ctx.send('You have reached the maximum number of pins for this channel.')
            
    @commands.hybrid_command()
    async def unpin(self, ctx: commands.Context, message: discord.Message = None):
        """
        Unpin a message from a channel.
        """
        if await self.check_permissions(ctx): 
            if not message.pinned:
                return await ctx.send('The message is already unpinned.')
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
