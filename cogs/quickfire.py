import challonge
import discord
import time
from discord.ext import commands
from discord.ext.commands import Context
from tabulate import tabulate
import os
import tempfile
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager



# Define the Quickfire class, which is a subclass of commands.Cog
class Quickfire(commands.Cog, name="quickfire"):
    def __init__(self, bot):
        self.bot = bot

        # Set Challonge API credentials
        key = self.bot.config["CHALLONGE_KEY"]
        user = self.bot.config["CHALLONGE_USER"]
        challonge.set_credentials(user, key)

    @commands.hybrid_group(
        name="qf",
        description="Command group for Quickfire tournaments.",
    )
    async def qf(self, context: Context) -> None:
        """
        Command group for Quickfire tournaments.

        :param context: The hybrid command context.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="You need to specify a subcommand.\n\n"
                            "**Subcommands:**\n"
                            "`signup` - Sign up for the currently open Quickfire tournament.\n"
                            "`show_players` - Lists the players signed up for a specific Quickfire tournament.\n"
                            "`show_tournaments` - Lists the Quickfire tournaments that are open or in progress.\n"
                            "`show_matches` - Lists the matches in a specified Quickfire tournament.\n"
                            "`bracket_link` - Posts the link to a Quickfire tournament bracket in Challonge.\n"
                            "`bracket` - Posts screenshot of current Challonge bracket for a specified Quickfire tournament.\n"
                            "`report` - Allows user to report a match result for a specific Quickfire tournament.\n\n"
                            "**Tournament Organizer Only**\n"
                            "`create_tournament` - Creates a Quickfire tournament in Challonge.\n",

                color=0x992d22,
            )
            await context.send(embed=embed)

    # Define the signup command, which allows a user to sign up for a tournament
    @qf.command(
        name="signup",
        description="Allows user to sign up for the current Quickfire tournament",
    )
    async def signup(self, context: Context, tournament_name: str):
        """
        Allows user to sign up for the current Quickfire tournament.

        :param context: The hybrid command context.
        :param tournament_name: Tournament name.
        """
        # check if the tournament_name includes 'quickfire'
        if 'quickfire' not in tournament_name:
            embed = discord.Embed(title='Error!',
                                  description=f'This command only works for Quickfire tournaments.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
            return

        # Get the list of all pending tournaments
        tournaments = challonge.tournaments.index(state='pending')

        # Find the tournament by its name
        tournament = next((t for t in tournaments if t['name'].lower() == tournament_name.lower()), None)
        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Tournament "{tournament_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # If the tournament exists, check the number of participants
            num_participants = len(challonge.participants.index(tournament['id']))
            if num_participants < 16:
                embed = discord.Embed(title="Add Participant",
                                      description=f"Please enter your IGN (In Game Name) to be added to tournament {tournament_name}",
                                      color=0x1f8b4c)
                await context.send(embed=embed)
                participant_name = await self.bot.wait_for('message', check=lambda m: m.author == context.author)
                participant = challonge.participants.create(tournament['id'], participant_name.content)
                num_participants += 1
                if num_participants == 16:
                    # Start the tournament and create a new tournament with the same name
                    challonge.tournaments.start(tournament['id'])
                    new_tournament_name = f'{tournament_name}{len(tournaments) + 1}'
                    unique_url = f"{tournament_name}{int(time.time())}"  # Add this line to create a unique URL
                    new_tournament = challonge.tournaments.create(new_tournament_name,
                                                                  url=unique_url,
                                                                  game_name="Hero Realms Digital")  # Add url=unique_url parameter
                    embed = discord.Embed(title="Tournament Created",
                                          description=f'Tournament "{new_tournament_name}" has started! A new tournament "{new_tournament_name}" has been created.',
                                          color=0xc27c0e)
                    await context.send(embed=embed)

                else:
                    embed = discord.Embed(title="Participant Added",
                                          description=f'Participant "{participant["name"]}" has been added to tournament "{tournament_name}"',
                                          color=0x1f8b4c)
                    await context.send(embed=embed)
                    # Gives user the Quickfire Role
                    role = discord.utils.get(context.guild.roles, id=1104624377313624066)
                    await context.author.add_roles(role)

    # Define the show_participants command, which allows a tournament organizer to view the list of participants in a tournament
    @qf.command(
        name="show_players",
        description="Lists participants in a specific Quickfire tournament.",
    )
    async def show_players(self, context: Context, tournament_name: str):
        """
        Lists participants in a specific Quickfire tournament.

        :param context: The hybrid command context.
        :param tournament_name: Tournament name.
        """
        # check if the tournament_name includes 'quickfire'
        if 'quickfire' not in tournament_name:
            embed = discord.Embed(title='Error!',
                                  description=f'This command only works for Quickfire tournaments.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
            return

        tournaments = challonge.tournaments.index(state='all')
        tournament = next((t for t in tournaments if t['name'].lower() == tournament_name.lower()), None)
        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Tournament "{tournament_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            participants = challonge.participants.index(tournament['id'])
            participant_names = [p['name'] for p in participants]
            participant_list = '\n'.join(participant_names)
            embed = discord.Embed(title=f'Participants in tournament "{tournament_name}"',
                                  description=participant_list,
                                  color=0x992d22)
            await context.send(embed=embed)

    # Define the show_matches command, which returns a list of matches for a tournament
    @qf.command(
        name="show_matches",
        description="Returns a list of matches for a specific Quickfire tournament.",
    )
    async def show_matches(self, context: Context, tournament_name: str):
        """
        Returns a list of open matches for a specific Quickfire tournament.

        :param context: The hybrid command context.
        :param tournament_name: Name of tournament whose matches will be returned.
        """
        # check if the tournament_name includes 'quickfire'
        if 'quickfire' not in tournament_name:
            embed = discord.Embed(title='Error!',
                                  description=f'This command only works for Quickfire tournaments.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
            return

        tournaments = challonge.tournaments.index(state='in progress')
        tournament = next((t for t in tournaments if t['name'].lower() == tournament_name.lower()), None)
        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Tournament "{tournament_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            matches = challonge.matches.index(tournament['id'], state='open')
            participants = challonge.participants.index(tournament['id'])
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
    
            embed = discord.Embed(title=tournament_name, description='Tournament Bracket', color=0x206694)
            embed.add_field(name='Round', value='\n'.join([str(b[3]) for b in bracket]))
            embed.add_field(name='Player 1', value='\n'.join([b[1] for b in bracket]))
            embed.add_field(name='Player 2', value='\n'.join([b[2] for b in bracket]))
    
            await context.send(embed=embed)

    @qf.command(
        name="bracket_link",
        description="Displays the tournament bracket from Challonge.",
    )
    async def bracket_link(self, context: Context, tournament_name: str):
        """
        Returns the Challonge bracket link for the specified tournament (if in progress).

        :param context: The command context.
        :param tournament_name: Tournament name.
        """
        # check if the tournament_name includes 'quickfire'
        if 'quickfire' not in tournament_name:
            embed = discord.Embed(title='Error!',
                                  description=f'This command only works for Quickfire tournaments.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
            return

        tournaments = challonge.tournaments.index(state='in progress')
        tournament = next((t for t in tournaments if t['name'].lower() == tournament_name.lower()), None)

        if tournament is None:
            await context.send(f'Tournament "{tournament_name}" not found')
        else:
            # Get the tournament URL
            tournament_url = tournament['full_challonge_url']

            # Create an embed with the tournament bracket URL
            embed = discord.Embed(
                title=f'Tournament Bracket for "{tournament_name}"',
                description=f'[View the bracket here]({tournament_url})',
                color=0x71368a
            )
            await context.send(embed=embed)

    @qf.command(
        name="bracket",
        description="Screenshots the tournament bracket from Challonge and posts the image.",
    )
    async def bracket(self, context: Context, tournament_name: str):
        """
        Displays the Challonge bracket image for the specified in progress tournament by taking a screenshot.
        This is an experimental feature, and may not always work.

        :param context: The command context.
        :param tournament_name: Tournament name.
        """
        # check if the tournament_name includes 'quickfire'
        if 'quickfire' not in tournament_name:
            embed = discord.Embed(title='Error!',
                                  description=f'This command only works for Quickfire tournaments.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
            return

        tournaments = challonge.tournaments.index(state='in progress')
        tournament = next((t for t in tournaments if t['name'].lower() == tournament_name.lower()), None)

        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Tournament "{tournament_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # Get the tournament URL
            tournament_url = tournament['live_image_url']

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

                # Take a screenshot of the bracket
                screenshot = driver.get_screenshot_as_png()
                driver.quit()

                # Post the screenshot as an image
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(screenshot)
                    temp_file.flush()
                    embed = discord.Embed(
                        title=f'Tournament Bracket for "{tournament_name}"',
                        color=0x71368a
                    )
                    await context.send(embed=embed, file=discord.File(temp_file.name, filename="bracket.png"))
                    os.unlink(temp_file.name)

            except Exception as e:
                driver.quit()
                embed = discord.Embed(title='Error!',
                                      description='Failed to capture the bracket image.',
                                      color=0xe74c3c)
                await context.send(embed=embed)

    # Define the show_tournaments command, which lists all current tournaments and their status
    @qf.command(
        name="show_tournaments",
        description="Returns a list of current Quickfire tournaments and their status.",
    )
    async def show_tournaments(self, context: Context):
        """
        List of current Quickfire tournaments in Challonge and their status.

        :param context: The hybrid command context.
        """
        tournaments = challonge.tournaments.index(state='in_progress,pending')
        embed = discord.Embed(title='Quickfire Tournament List',
                              description='All currently in progress or pending Quickfire tournaments.',
                              color=0xa84300)
        for tournament in tournaments:
            if 'quickfire' in tournament['name'].lower():
                embed.add_field(name=tournament['name'],
                                value=f"Status: {tournament['state']}",
                                inline=False)
        await context.send(embed=embed)

    # Define the report command, which allows users to report the result of a match
    @qf.command(
        name="report",
        description="Allows user to report a Quickfire match result.",
    )
    async def report(self, context: Context, tournament_name: str, round_number: int, winner: str):
        """
        Report the result of a match in the specified Quickfire tournament using the round number.

        :param context: The hybrid command context.
        :param tournament_name: Tournament name.
        :param round_number: Round number of the match.
        :param winner: Name of the winner.
        """
        # check if the tournament_name includes 'quickfire'
        if 'quickfire' not in tournament_name:
            embed = discord.Embed(title='Error!',
                                  description=f'This command only works for Quickfire tournaments.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
            return

        # Fetch all in progress tournaments and find the one with the specified name
        tournaments = challonge.tournaments.index(state='in progress')
        tournament = next((t for t in tournaments if t['name'].lower() == tournament_name.lower()), None)

        # If the tournament is not found, send an error message
        if tournament is None:
            embed = discord.Embed(
                title="Error",
                description=f'Tournament "{tournament_name}" not found',
                color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # Fetch all open matches in the tournament
            matches = challonge.matches.index(tournament['id'], state='open')

            # Get participants of the tournament
            participants = challonge.participants.index(tournament['id'])

            # Find the winner in the list of participants
            winner_participant = next((p for p in participants if p["name"] == winner), None)

            # Determine the winner's ID
            winner_id = winner_participant['id']

            # Find the match which is the correct round and includes the winner id
            match = next((m for m in matches if m['round'] == round_number and (
                        m['player1_id'] == winner_id or m['player2_id'] == winner_id)), None)

            # If the match is not found or already completed, send an error message
            if match is None:
                embed = discord.Embed(
                    title="Error",
                    description=f'Match in round {round_number} not found or already completed in tournament "{tournament_name}"',
                    color=0xe74c3c)
                await context.send(embed=embed)
            else:
                # If the winner is not found in the list of participants, send an error message
                if winner_participant is None:
                    embed = discord.Embed(
                        title="Error",
                        description=f'Winner "{winner}" not found in the list of participants',
                        color=0xe74c3c)
                    await context.send(embed=embed)
                    return

                # Check if the winner is either player 1 or player 2 of the match
                if winner_id not in [match['player1_id'], match['player2_id']]:
                    embed = discord.Embed(
                        title='Error',
                        description=f'Winner "{winner}" is not a player in the match of round {round_number}',
                        color=0xe74c3c)
                    await context.send(embed=embed)
                else:
                    # Determine the score (1-0) for the winner
                    scores_csv = "1-0" if winner_id == match['player1_id'] else "0-1"

                    # Update the match and mark it as complete
                    challonge.matches.update(
                        tournament['id'],
                        match['id'],
                        scores_csv=scores_csv,
                        winner_id=winner_id
                    )
                    embed = discord.Embed(
                        title='Match Reported',
                        description=f'Match result reported for match in round {round_number} in tournament "{tournament_name} {winner} won 1-0',
                        color=0x71368a
                    )
                    await context.send(embed=embed)

                    # Check if all matches are completed
                    matches = challonge.matches.index(tournament['id'], state='all')
                    if all(m['state'] == 'complete' for m in matches):
                        # Finalize the tournament
                        challonge.tournaments.finalize(tournament['id'])

                        # Check if the tournament is complete
                        tournament = challonge.tournaments.show(tournament['id'])
                        if tournament['state'] == 'complete':
                            # Find the winner in the list of participants
                            final_winner = next((p for p in participants if p["id"] == winner_id), None)
                            role = discord.utils.get(context.guild.roles, id=1104624377313624066)
                            # Create an embed with the winner's information
                            embed = discord.Embed(
                                title=f'Tournament "{tournament_name}" is complete!',
                                description=f'Congratulations to the winner: {final_winner["name"]}',
                                color=0x1f8b4c
                            )
                            await context.send(embed=embed)

    # Define the add_player command which allows a Tournament Organizer to add a player to Quickfire tournaments manually.
    @qf.command(
        name="add_player",
        description="Allows TO to manually add a player to a Quickfire tournament",
    )
    @commands.has_role("Tournament Organizer")
    async def add_player(self, context: Context, tournament_name: str, player_name: str):
        """
        Add player to tournament.

        :param context: The hybrid command context.
        :param tournament_name: Name of the tournament.
        :param player_name: Name of player to add.
        """
        # check if the tournament_name includes 'quickfire'
        if 'quickfire' not in tournament_name:
            embed = discord.Embed(title='Error!',
                                  description=f'This command only works for Quickfire tournaments.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
            return

        # Get the list of all pending tournaments
        tournaments = challonge.tournaments.index(state='pending')

        # Find the tournament by its name
        tournament = next((t for t in tournaments if t['name'].lower() == tournament_name.lower()), None)

        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Tournament "{tournament_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # If the tournament exists, check the number of participants
            participant = challonge.participants.create(tournament['id'], player_name)
            embed = discord.Embed(title="Participant Added",
                                  description=f'Participant {participant["name"]} added to tournament {tournament["name"]}',
                                  color=0x1f8b4c)
            await context.send(embed=embed)

            # Check the number of participants
            num_participants = len(challonge.participants.index(tournament['id']))
            if num_participants >= 16:
                embed = discord.Embed(title="Tournament Full",
                                      description=f'The tournament "{tournament_name}" is full with {num_participants} participants',
                                      color=0xa84300)
                await context.send(embed=embed)
            if num_participants == 16:
                # Start the tournament and create a new tournament with the same name
                challonge.participants.randomize(tournament['id'])
                challonge.tournaments.start(tournament['id'])
                new_tournament_name = f'{tournament_name}{len(tournaments) + 1}'
                unique_url = f"{tournament_name}{int(time.time())}"  # Add this line to create a unique URL
                new_tournament = challonge.tournaments.create(new_tournament_name,
                                                              url=unique_url,
                                                              game_name="Hero Realms Digital")  # Add url=unique_url parameter
                embed = discord.Embed(title='Full Tournament',
                                      description=f'Tournament "{tournament_name}" has started! A new tournament "{new_tournament_name}" has been created.',
                                      color=0xe67e22)
                await context.send(embed=embed)


# Define the setup function, which adds the Quickfire cog to the Hero-Helper Bot
async def setup(bot):
    await bot.add_cog(Quickfire(bot))
