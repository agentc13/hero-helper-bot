"""
Hero-Helper discord bot
Description:
A python based discord bot for the Hero Realms community.

Created by agentc13.
Version: 1.0
"""


from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks


class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot):
        self.bot = bot

    # purge command
    @commands.hybrid_command(
        name="purge",
        description="Delete a number of messages.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @checks.not_blacklisted()
    @app_commands.describe(amount="The amount of messages that should be deleted.")
    async def purge(self, context: Context, amount: int) -> None:
        """
        Delete a number of messages.

        :param context: The hybrid command context.
        :param amount: The number of messages that should be deleted.
        """
        await context.send(
            "Deleting messages..."
        )
        await context.channel.purge(limit=amount + 1)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
