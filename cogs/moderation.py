"""
Hero-Helper discord bot
Description:
A python based discord bot for the Hero Realms community.

Created by agentc13.
Version: 1.0
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks, db_manager


class Moderation(commands.Cog, name="moderation"):
    def __init__(self, bot):
        self.bot = bot

    # warning command
    @commands.hybrid_group(
        name="warning",
        description="Manage warnings of a user on a server.",
    )
    @commands.has_permissions(manage_messages=True)
    @checks.not_blacklisted()
    async def warning(self, context: Context) -> None:
        """
        Manage warnings of a user on a server.

        :param context: The hybrid command context.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="Please specify a subcommand.\n\n"
                            "**Subcommands:**\n"
                            "`add` - Add a warning to a user.\n"
                            "`remove` - Remove a warning from a user.\n"
                            "`list` - List all warnings of a user.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)

    # add warning
    @warning.command(
        name="add",
        description="Adds a warning to a user in the server.",
    )
    @checks.not_blacklisted()
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="The user that should be warned.",
        reason="The reason why the user should be warned.",
    )
    async def warning_add(
        self, context: Context, user: discord.User, *, reason: str = "Not specified"
    ) -> None:
        """
        Warns a user in his private messages.

        :param context: The hybrid command context.
        :param user: The user that should be warned.
        :param reason: The reason for the warn. Default is "Not specified".
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        total = await db_manager.add_warn(
            user.id, context.guild.id, context.author.id, reason
        )
        embed = discord.Embed(
            description=f"**{member}** was warned by **{context.author}**!\nTotal warns for this user: {total}",
            color=0x9C84EF,
        )
        embed.add_field(name="Reason:", value=reason)
        await context.send(embed=embed)
        try:
            await member.send(
                f"You were warned by **{context.author}** in **{context.guild.name}**!\nReason: {reason}"
            )
        except:
            # Couldn't send a message in the private messages of the user
            await context.send(
                f"{member.mention}, you were warned by **{context.author}**!\nReason: {reason}"
            )

    # remove warning
    @warning.command(
        name="remove",
        description="Removes a warning from a user in the server.",
    )
    @checks.not_blacklisted()
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(
        user="The user that should get their warning removed.",
        warn_id="The ID of the warning that should be removed.",
    )
    async def warning_remove(
        self, context: Context, user: discord.User, warn_id: int
    ) -> None:
        """
        Warns a user in his private messages.

        :param context: The hybrid command context.
        :param user: The user that should get their warning removed.
        :param warn_id: The ID of the warning that should be removed.
        """
        member = context.guild.get_member(user.id) or await context.guild.fetch_member(
            user.id
        )
        total = await db_manager.remove_warn(warn_id, user.id, context.guild.id)
        embed = discord.Embed(
            description=f"I've removed the warning **#{warn_id}** from **{member}**!\nTotal warns for this user: {total}",
            color=0x9C84EF,
        )
        await context.send(embed=embed)

    # list warnings
    @warning.command(
        name="list",
        description="Shows the warnings of a user in the server.",
    )
    @commands.has_guild_permissions(manage_messages=True)
    @checks.not_blacklisted()
    @app_commands.describe(user="The user you want to get the warnings of.")
    async def warning_list(self, context: Context, user: discord.User):
        """
        Shows the warnings of a user in the server.

        :param context: The hybrid command context.
        :param user: The user you want to get the warnings of.
        """
        warnings_list = await db_manager.get_warnings(user.id, context.guild.id)
        embed = discord.Embed(title=f"Warnings of {user}", color=0x9C84EF)
        description = ""
        if len(warnings_list) == 0:
            description = "This user has no warnings."
        else:
            for warning in warnings_list:
                description += f"• Warned by <@{warning[2]}>: **{warning[3]}** (<t:{warning[4]}>) - Warn ID #{warning[5]}\n"
        embed.description = description
        await context.send(embed=embed)

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
