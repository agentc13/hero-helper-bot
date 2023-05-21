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
        # Searches through all pending tournaments and get the current Highlander tournament if there is one.
        tournaments = challonge.tournaments.index(state='pending')
        highlander_tournament = None
        for t in tournaments:
            if 'Highlander'.lower() in t['name'].lower():
                highlander_tournament = t
                break

        if highlander_tournament is None:
            embed = discord.Embed(
                title='Error!',
                description=f'There is no Highlander tournament pending.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
        else:
            participants = challonge.participants.index(highlander_tournament['id'])

            # Check if the participant name already exists
            if any(p['name'].lower() == participant_name.lower() for p in participants):
                embed = discord.Embed(
                    title='Error!',
                    description=f'IGN "{participant_name}" is already signed up.',
                    colour=discord.Colour.dark_red(),
                )
                await context.send(embed=embed)
            else:
                participant = challonge.participants.create(highlander_tournament['id'], participant_name)
                embed = discord.Embed(
                    title="Participant Added",
                    description=f'"{participant["name"]}" has been added to {highlander_tournament["name"]}',
                    colour=discord.Colour.dark_blue(),
                )
                await context.send(embed=embed)
                # Gives user the Quickfire Role
                role = discord.utils.get(context.guild.roles, id=1088139361217945686)
                if role is not None:
                    await context.author.add_roles(role)

    @hl.command(
        name="show_players",
        description="Displays participants in a Highlander tournament.",
    )
    async def show_players(self, context: Context):
        """
        Displays participants in a Highlander tournament.

        :param context: The hybrid command context.
        """
        # Searches through all pending and in progress tournaments and get the current Highlander tournament if there is one.
        pending_tournaments = challonge.tournaments.index(state='pending')
        in_progress_tournaments = challonge.tournaments.index(state='in progress')

        # Combine both lists
        tournaments = pending_tournaments + in_progress_tournaments

        highlander_tournament = None
        for t in tournaments:
            if 'Highlander'.lower() in t['name'].lower():
                highlander_tournament = t
                break

        if highlander_tournament is None:
            embed = discord.Embed(
                title='Error!',
                description=f'There is no pending or in progress Highlander tournament.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
        else:
            participants = challonge.participants.index(highlander_tournament['id'])
            participant_names = [p['name'] for p in participants]
            participant_list = '\n'.join(participant_names)
            embed = discord.Embed(
                title=f'Participants in tournament "{highlander_tournament["name"]}"',
                description=participant_list,
                colour=discord.Colour.dark_magenta(),
            )
            await context.send(embed=embed)

    # Define the show_matches command, which returns a list of matches for a tournament
    @hl.command(
        name="show_matches",
        description="Displays open matches for a Highlander tournament.",
    )
    async def show_matches(self, context: Context):
        """
        Displays open matches for a Highlander tournament.

        :param context: The hybrid command context.
        """
        # Searches through all pending tournaments and get the current Highlander tournament if there is one.
        tournaments = challonge.tournaments.index(state='in progressd')
        highlander_tournament = None
        for t in tournaments:
            if 'Highlander'.lower() in t['name'].lower():
                highlander_tournament = t
                break

        if highlander_tournament is None:
            embed = discord.Embed(
                title='Error!',
                description=f'There is no Highlander tournament in progress.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)

        else:
            matches = challonge.matches.index(highlander_tournament['id'], state='open')
            participants = challonge.participants.index(highlander_tournament['id'])
            participant_ids = {p['id']: p for p in participants}
            bracket = []
            for match in matches:
                if match['player1_id'] is not None and match['player2_id'] is not None:
                    p1_name = participant_ids[match['player1_id']]['name']
                    p2_name = participant_ids[match['player2_id']]['name']
                else:
                    p1_name = "TBD"
                    p2_name = "TBD"
                round_num = match.get('round', 'N/A')
                bracket.append((match['id'], p1_name, p2_name, round_num))
            bracket_str = tabulate(bracket, headers=["Match ID", "Player 1", "Player 2", "Round"])

            embed = discord.Embed(
                title=highlander_tournament["name"],
                description='Tournament Bracket',
                colour=discord.Colour.dark_green(),
            )
            embed.add_field(name='Round', value='\n'.join([str(b[3]) for b in bracket]))
            embed.add_field(name='Player 1', value='\n'.join([b[1] for b in bracket]))
            embed.add_field(name='Player 2', value='\n'.join([b[2] for b in bracket]))

            await context.send(embed=embed)

    @hl.command(
        name="bracket_link",
        description="Displays the bracket link for the specified tournament.",
    )
    async def bracket_link(self, context: Context):
        """
        Displays the bracket link for the specified tournament.

        :param context: The command context.
        """
        # Searches through all in progress tournaments and get the current Highlander tournament if there is one.
        tournaments = challonge.tournaments.index(state='in progress')
        highlander_tournament = None
        for t in tournaments:
            if 'Highlander'.lower() in t['name'].lower():
                highlander_tournament = t
                break

        if highlander_tournament is None:
            embed = discord.Embed(
                title='Error!',
                description=f'There is no Highlander tournament pending.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
        else:
            # Get the tournament URL
            tournament_url = highlander_tournament['full_challonge_url']

            # Create an embed with the tournament bracket URL
            embed = discord.Embed(
                title=f'Tournament Bracket for "{highlander_tournament["name"]}"',
                description=f'[View the bracket here]({tournament_url})',
                colour=discord.Colour.dark_gold(),
            )
            await context.send(embed=embed)

    @hl.command(
        name="bracket",
        description="Displays the bracket link for the specified tournament.",
    )
    async def bracket_link(self, context: Context):
        """
        Displays the bracket link for the specified tournament.

        :param context: The command context.
        """
        # Searches through all pending tournaments and get the current Highlander tournament if there is one.
        tournaments = challonge.tournaments.index(state='in progress')
        highlander_tournament = None
        for t in tournaments:
            if 'Highlander'.lower() in t['name'].lower():
                highlander_tournament = t
                break

        if highlander_tournament is None:
            embed = discord.Embed(
                title='Error!',
                description=f'There is no Highlander tournament pending.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
        else:
            # Get the tournament URL
            tournament_url = highlander_tournament['live_image_url']

            # Set up the headless browser
            options = webdriver.ChromeOptions()
            options.headless = True
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

            try:
                # Navigate to the tournament URL
                driver.get(tournament_url)

                # Set the window size
                driver.set_window_size(1000, 650)

                # Take a screenshot of the bracket
                screenshot = driver.get_screenshot_as_png()
                driver.quit()

                # Post the screenshot as an image
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(screenshot)
                    temp_file.flush()
                    embed = discord.Embed(
                        title=f'Tournament Bracket for "{highlander_tournament["name"]}"',
                        colour=discord.Colour.dark_gold(),
                    )
                    await context.send(
                        embed=embed,
                        file=discord.File(temp_file.name,
                                          filename="bracket.png"))
                    os.unlink(temp_file.name)

            except Exception as e:
                driver.quit()
                embed = discord.Embed(
                    title='Error!',
                    description='Failed to capture the bracket image.',
                    colour=discord.Colour.dark_red(),
                )
                await context.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Highlander(bot))
