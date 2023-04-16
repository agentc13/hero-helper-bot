"""
Hero-Helper discord bot
Description:
A python based discord bot for the Hero Realms community.

Created by agentc13.
Version: 1.0
"""

import discord
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks


# Here we name the cog and create a new class for the cog.
class Tcl(commands.Cog, name="tcl"):
    def __init__(self, bot):
        self.bot = bot

    # Here you can just add your own commands, you'll always need to provide "self" as first parameter.
    @commands.hybrid_command(
        name="signup",
        description="Sign up for Thandar Combat League.",
    )
    # This will only allow non-blacklisted members to execute the command
    @checks.not_blacklisted()
    async def signup(self, context: Context) -> None:
        """
        Sign up for Thandar Combat League. You will receive a DM with the rules
        link and be added to the list of players for the next season.

        :param context: The hybrid command context.
        """
        # embed text for PM. Will be send in channel if PM forbidden.
        # TO DO: add code to actually sign up player and add to DB.
        embed = discord.Embed(
            description=f"You have signed up for Thandar Combat League. You can find the rules document [here](https://agentc13.com/tcl-rules.html)",
            color=0x9C84EF,
        )
        try:
            await context.author.send(embed=embed)
            await context.send(f"{context.author.mention} has signed up for Thandar Combat League!")
        except discord.Forbidden:
            await context.send(embed=embed)


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(Tcl(bot))
