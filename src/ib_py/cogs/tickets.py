import discord
from discord.ext import commands

from ..config import IBPyConfig

config = IBPyConfig()
BUGREPORT_CHANNEL_ID = 1537983881544728737


class BugReportModal(discord.ui.Modal, title="Bug Report"):
    summary = discord.ui.TextInput(
        label="Summary",
        placeholder="Briefly describe the bug.",
        max_length=100,
    )
    details = discord.ui.TextInput(
        label="What happend? Steps to Reproduce",
        style=discord.TextStyle.paragraph,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        cog: "Tickets" = interaction.client.get_cog("Tickets")
        await cog.publish_tickets(
            interaction=interaction,
            kind="Bug Report",
            color=discord.Color.red(),
            fields={"Summary": self.summary.value, "Details": self.details.value},
        )


class FeatureRequestModal(discord.ui.Modal, title="Feature Request"):
    summary = discord.ui.TextInput(
        label="Summary",
        placeholder="Briefly describe the feature request.",
        max_length=100,
    )
    details = discord.ui.TextInput(
        label="Why would this be useful?",
        style=discord.TextStyle.paragraph,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        cog: "Tickets" = interaction.client.get_cog("Tickets")
        await cog.publish_tickets(
            interaction=interaction,
            kind="Feature Request",
            color=discord.Color.green(),
            fields={"Summary": self.summary.value, "Details": self.details.value},
        )


class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Bug Report",
        style=discord.ButtonStyle.danger,
        emoji="\U0001f41e",
        custom_id="ticket_panel:bug_report",
    )
    async def bug_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BugReportModal())

    @discord.ui.button(
        label="Feature Request",
        style=discord.ButtonStyle.primary,
        emoji="\u2728",
        custom_id="ticket_panel:feature_request",
    )
    async def feature_request(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(FeatureRequestModal())


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(TicketPanel())

    async def publish_tickets(
        self,
        *,
        interaction: discord.Interaction,
        kind: str,
        color: discord.Color,
        fields: dict[str, str],
    ):
        channel = self.bot.get_channel(BUGREPORT_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message(
                "The bug report channel is not set up correctly. Please contact the bot owner.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(title=kind, color=color, timestamp=discord.utils.utcnow())
        embed.set_author(
            name=f"{interaction.user} ({interaction.user.id})",
            icon_url=interaction.user.display_avatar.url,
        )
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=False)

        await channel.send(embed=embed)
        await interaction.response.send_message(
            f"Your {kind.lower()} has been submitted successfully. Thank you for your feedback!",
            ephemeral=True,
        )

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def ticketpanel(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Bug Reports & Feature Requests",
            description=(
                "Found a bug or have an idea for a new feature?\n"
                "Click a button below to let us know!"
            ),
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed, view=TicketPanel())


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
