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


class Tcl(commands.Cog, name="tcl"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="waitlist",
        description="Sign up for Thandar Combat League.",
    )
    # This will only allow non-blacklisted members to execute the command
    @checks.not_blacklisted()
    async def waitlist(self, context: Context) -> None:
        """
        Sign up for Thandar Combat League. You will receive a DM with the rules
        link and be added to the list of players for the next season.

        :param context: The hybrid command context.
        """
        # embed text for PM. Will be sent in channel if PM forbidden.
        # TO DO: add code to actually sign up player and add to DB.
        embed = discord.Embed(
            description=f"You have been added to the Thandar Combat League waitlist. You can find the rules document "
                        f"[here](https://agentc13.com/tcl-rules.html)",
            color=0x992d22,
        )
        try:
            await context.author.send(embed=embed)
            await context.send(f"{context.author.mention} has signed up for Thandar Combat League!")
        except discord.Forbidden:
            await context.send(embed=embed)

# Testing for DB stuff
    @commands.hybrid_group(
        name="tcl",
        description="Lets you add or remove a user to the Thandar Combat League.",
    )
    @checks.is_owner()
    async def tcl(self, context: Context) -> None:
        """
        Lets you add or remove a user to the Thandar Combat League.

        :param context: The hybrid command context.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="You need to specify a subcommand.\n\n**Subcommands:**\n`add` - Add a user to TCL."
                            "\n`remove` - Remove a user from TCL.",
                color=0x992d22,
            )
            await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="show",
        description="Shows the list of all Thandar Combat League Users.",
    )
    @checks.is_owner()
    async def tcl_show(self, context: Context) -> None:
        """
        Shows the list of all Thandar Combat League users.

        :param context: The hybrid command context.
        """
        tcl_users = await db_manager.get_tcl_users()
        if len(tcl_users) == 0:
            embed = discord.Embed(
                description="There are currently no Thandar Combat League users.", color=0x992d22
            )
            await context.send(embed=embed)
            return

        embed = discord.Embed(title="Thandar Combat League Users", color=0x992d22)
        users = []
        for tcluser in tcl_users:
            user = self.bot.get_user(int(tcluser[0])) or await self.bot.fetch_user(
                int(tcluser[0])
            )
            users.append(f"• {user.mention} ({user}) - Signed Up <t:{tcluser[1]}>")
        embed.description = "\n".join(users)
        await context.send(embed=embed)

    @tcl.command(
        base="tcl_list",
        name="add",
        description="Lets you add a user to Thandar Combat League.",
    )
    @app_commands.describe(user="The user that should be added to Thandar Combat League")
    @checks.is_owner()
    async def tcl_add(self, context: Context, user: discord.User) -> None:
        """
        Lets you add a user to Thandar Combat League.

        :param context: The hybrid command context.
        :param user: The user that should be added to the Thandar Combat League.
        """
        user_id = user.id
        if await db_manager.is_signed_up(user_id):
            embed = discord.Embed(
                description=f"**{user.name}** is already in Thandar Combat League.",
                color=0x992d22,
            )
            await context.send(embed=embed)
            return
        total = await db_manager.add_user_to_tcl(user_id)
        embed = discord.Embed(
            description=f"**{user.name}** has been successfully added to Thandar Combat League",
            color=0x992d22,
        )
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} in "
                 f"Thandar Combat League"
        )
        await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="remove",
        description="Lets you remove a user from Thandar Combat League.",
    )
    @app_commands.describe(user="The user that should be removed from Thandar Combat League.")
    @checks.is_owner()
    async def tcl_remove(self, context: Context, user: discord.User) -> None:
        """
        Lets you remove a user from Thandar Combat League.

        :param context: The hybrid command context.
        :param user: The user that should be removed from Thandar Combat League.
        """
        user_id = user.id
        if not await db_manager.is_signed_up(user_id):
            embed = discord.Embed(
                description=f"**{user.name}** is not in Thandar Combat League.", color=0x992d22
            )
            await context.send(embed=embed)
            return
        total = await db_manager.remove_user_from_tcl(user_id)
        embed = discord.Embed(
            description=f"**{user.name}** has been successfully removed from Thandar Combat League.",
            color=0x992d22,
        )
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} in "
                 f"Thandar Combat League."
        )
        await context.send(embed=embed)


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(Tcl(bot))
