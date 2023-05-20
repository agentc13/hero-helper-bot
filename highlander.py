import challonge
import discord
import time
import re
from discord.ext import commands
from discord.ext.commands import Context
from tabulate import tabulate
import os
import tempfile
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


class Highlander(commands.Cog, name="Highlander"):
    def __init__(self, bot):
        self.bot = bot

        # Set Challonge API credentials
        key = self.bot.config["CHALLONGE_KEY"]
        user = self.bot.config["CHALLONGE_USER"]
        challonge.set_credentials(user, key)

    @commands.hybrid_group(
        name="hl",
        description="Command group for Highlander tournaments.",
    )
    async def hl(self, context: Context) -> None:
        """
        Command group for Highlander tournaments.

        :param context: The hybrid command context.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="You need to specify a subcommand.\n\n"
                            "**Subcommands:**\n"
                            "`signup` - Sign up for the current Highlander tournament.\n"
                            "`show_players` - Lists the players in the current Highlander tournament.\n"
                            "`show_matches` - Lists the matches in the current Highlander tournament.\n"
                            "`bracket_link` - Posts the link to the current Highlander tournament bracket.\n"
                            "`bracket` - Posts the an image of the bracket for the current Highlander tournament.\n"
                            "`report` - Allows user to report a match result for the current Highlander tournament.\n"
                            "`rankings` - Posts the current rankings for the Highlander season.\n",

                colour=discord.Colour.dark_orange(),
            )
            await context.send(embed=embed)

    # Define the signup command, which allows a user to sign up for a tournament
    @hl.command(
        name="signup",
        description="Allows user to sign up for the current Highlander tournament",
    )
    async def signup(self, context: Context, participant_name: str):
        """
        Allows user to sign up for the current Highlander tournament.

        :param context: The hybrid command context.
        :param participant_name: Hero Realms IGN.
        """
        # Searches through all pending tournaments and
        tournaments = challonge.tournaments.index(state='pending')
        tournament = [t for t in tournaments if 'Highlander'.lower() in t['name'].lower()]

        if tournament is None:
            embed = discord.Embed(
                title='Error!',
                description=f'There is no Highlander tournament pending.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
        else:
            # If the tournament exists, check the number of participants
            participants = challonge.participants.index(tournament['id'])

            # Check if the participant name already exists
            if any(p['name'].lower() == participant_name.lower() for p in participants):
                embed = discord.Embed(
                    title='Error!',
                    description=f'IGN "{participant_name}" is already signed up.',
                    colour=discord.Colour.dark_red(),
                )
                await context.send(embed=embed)
            else:
                participant = challonge.participants.create(tournament['id'], participant_name)
                embed = discord.Embed(
                    title="Participant Added",
                    description=f'Participant "{participant["name"]}" has been added to tournament["name"]',
                    colour=discord.Colour.dark_blue(),
                )
                await context.send(embed=embed)
                # Gives user the Quickfire Role
                role = discord.utils.get(context.guild.roles, id=1088139361217945686)
                if role is not None:
                    await context.author.add_roles(role)


async def setup(bot):
    await bot.add_cog(Highlander(bot))
