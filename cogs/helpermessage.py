import os
import discord
import toml
from discord.ext import commands
from ..utils.commands import available_subcommands
from ..utils.pagination import paginated_embed_menus, PaginationView
from ..db.models import HelperMessage
from typing import AsyncGenerator, Set, Tuple


class Helpermessage(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.data = toml.load(os.environ["CONFIG_PATH"])
        self.subjects = self.data["subjects"]
        self.description = self.data["helper_description"]
        self.helper_roles = [self.subjects[channel] for channel in self.subjects.keys()]

    @commands.hybrid_group()
    async def helpermessage(self, ctx: commands.Context):
        """
        Commands for handling reminders.
        """
        await available_subcommands(ctx)

    @helpermessage.command()
    async def list(self, ctx: commands.Context):
        """
        List all active helpermessage embeds
        """
        embed_dict = dict(
            title="List of all active helpermessages",
            description="Here is a list of all active helpermessages.",
        )
        channel_ids = await HelperMessage.all().values_list("channel_id", flat=True)
        helpermessage_ids = await HelperMessage.all().values_list("message_id", flat=True)
        names = [f"<#{channel}>" for channel in channel_ids]
        values = [
            f"https://discord.com/channels/{ctx.guild.id}/{channel}/{helpermessage}"
            for channel, helpermessage in zip(channel_ids, helpermessage_ids)
        ]
        embeds = paginated_embed_menus(names, values, embed_dict=embed_dict)
        embed, view = await PaginationView(ctx, embeds).return_paginated_embed_view()
        await ctx.send(embed=embed, view=view)

    async def embed_getter(
        self, edited_roles: Set[discord.Role]
    ) -> AsyncGenerator[Tuple[discord.Message, discord.Role, discord.Embed], None]:
        for role in edited_roles:
            for channel, roles in self.subjects.items():
                if role.id in roles:
                    discord_channel = await self.bot.fetch_channel(int(channel))
                    helpermessage = await discord_channel.fetch_message(
                        HelperMessage.get(channel_id=discord_channel.id)
                    )
                    embed = helpermessage.embeds[0]
                    yield helpermessage, role, embed

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Update helper message based on user helper/dehelper.
        """
        # checking if there has been a change in roles
        if before.roles != after.roles:
            before_roles = set(before.roles)
            after_roles = set(after.roles)
            # checking whether roles were removed or added
            added_roles = after_roles - before_roles
            removed_roles = before_roles - after_roles
            # routine that runs to add the role
            if added_roles:
                async for helpermessage, role, embed in self.embed_getter(added_roles):
                    new_embed = discord.Embed(description=embed.description)
                    for field in embed.fields:
                        if field.name == f"**{role.name}**":
                            new_embed.add_field(
                                name=field.name, value=field.value + f"\n{after.mention}"
                            )
                        else:
                            new_embed.add_field(name=field.name, value=field.value)
                    await helpermessage.edit(embed=new_embed)

            # routine that runs to remove roles
            if removed_roles:
                async for helpermessage, role, embed in self.embed_getter(removed_roles):
                    new_embed = discord.Embed(description=embed.description)
                    for field in embed.fields:
                        if field.name == f"**{role.name}**":
                            members = field.value.split("\n")
                            new_member_list = [
                                member for member in members if member != after.mention
                            ]
                            new_embed.add_field(
                                name=field.name, value="\n".join(new_member_list)
                            )
                        else:
                            new_embed.add_field(name=field.name, value=field.value)
                    await helpermessage.edit(embed=new_embed)

    @helpermessage.command()
    async def create(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        helper_roles: commands.Greedy[discord.Role],
    ):
        """
        Create the helpermessage embed for a specific channel given the channel and helper role
        """
        # Create the embed that will be pinned in the message
        description = (
            self.description["description"] + f"\n\n **Subject helpers for {channel.name}:**"
        )
        helper_embed = discord.Embed(description=description)
        # add the field displaying the helpers
        for role in helper_roles:
            subject_helpers = [
                member.mention for member in ctx.guild.members if role in member.roles
            ]
            helper_embed.add_field(
                name=f"**{role.name}**", value="\n".join(subject_helpers), inline=False
            )
        # send the message
        helpermessage = await channel.send(embed=helper_embed)
        # pin the message
        await helpermessage.pin()
        # save to the database
        values = dict(
            message_id=helpermessage.id,
            channel_id=channel.id,
            role_id=[role.id for role in helper_roles],
        )
        helpermessage = await HelperMessage.create(**values)
        await ctx.send("The helpermessage has been created!")

    @helpermessage.command()
    async def delete(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Delete the helpermessage embed for a specific channel given the channel and helper role
        """
        helpermessage = await HelperMessage.get_or_none(channel_id=channel.id)
        if not helpermessage:
            await ctx.send("The helpermessage does not exist!")
            return
        discord_channel = await self.bot.fetch_channel(helpermessage.channel_id)
        discord_message = await discord_channel.fetch_message(helpermessage.message_id)
        await discord_message.delete()
        await helpermessage.delete()
        await ctx.send(
            f"The helpermessage for the channel <#{discord_channel.id}> has been successfully deleted!"
        )

    @helpermessage.command()
    async def edit(self, ctx: commands.Context, *, content: str):
        """
        Edit the content in the helpermessage
        """
        self.description["description"] = content
        channel_ids = await HelperMessage.all().values_list("channel_id", flat=True)
        for channel_id in channel_ids:
            discord_channel = await self.bot.fetch_channel(channel_id)
            helpermessage = await discord_channel.fetch_message(channel_id=channel_id)
            embed = helpermessage.embeds[0]
            embed.description = (
                content + f"\n\n **Subject helpers for {discord_channel.name}:**"
            )
            await helpermessage.edit(embed=embed)
        await ctx.send("Updated messages successfully")


async def setup(bot: commands.Bot):
    await bot.add_cog(Helpermessage(bot))
