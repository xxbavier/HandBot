"""Discord client lifecycle and application command error handling."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from database import Database
from settings import Settings

logger = logging.getLogger(__name__)


class HandBotTree(app_commands.CommandTree):
    async def on_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        # Internal exceptions go to logs rather than exposing infrastructure details.
        if isinstance(error, (app_commands.CheckFailure, app_commands.TransformerError)):
            description = str(error)
        else:
            original = getattr(error, "original", error)
            logger.error(
                "Application command failed: %s",
                getattr(interaction.command, "qualified_name", "unknown"),
                exc_info=(type(original), original, original.__traceback__),
            )
            description = "Please try again later."

        embed = discord.Embed(
            title="Error",
            description="There was an error processing the command.",
            color=discord.Color.red(),
        )
        embed.add_field(
            name="``Error Description``", value=description[:1024] or "Unknown error"
        )
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException:
            logger.warning("Could not deliver command error response.", exc_info=True)


class HandBot(commands.Bot):
    def __init__(self, settings: Settings):
        # Keep member events, role checks, and the existing prefix/help command.
        # Presence and voice events are not used by the current features.
        intents = discord.Intents.none()
        intents.guilds = True
        intents.members = True
        intents.messages = True
        intents.message_content = True
        super().__init__(
            command_prefix="?",
            intents=intents,
            application_id=settings.application_id,
            tree_cls=HandBotTree,
            status=discord.Status.online,
            activity=discord.Game("Handball"),
        )
        self.settings = settings
        self.database = Database(settings.mongo_uri)

    async def setup_hook(self) -> None:
        for extension in self.settings.extensions:
            # Stop on a broken extension before syncing an incomplete tree.
            await self.load_extension(extension)
            logger.info("Loaded extension %s", extension)
        synced = await self.tree.sync()
        logger.info(
            "Synced %d global commands: %s",
            len(synced), ", ".join(cmd.name for cmd in synced),
        )

    async def on_ready(self) -> None:
        logger.info(
            "Logged in as %s (%s)", self.user,
            self.user.id if self.user else "unknown",
        )

    async def close(self) -> None:
        try:
            await super().close()
        finally:
            await self.database.close()
