import discord
import challonge
import time
from tabulate import tabulate
from discord.ext import commands
from discord.ext.commands import Context

from helpers import db_manager


class Tcl(commands.Cog, name="Thandar Combat League"):
    def __init__(self, bot):
        self.bot = bot

        # Set Challonge API credentials
        key = self.bot.config["CHALLONGE_KEY"]
        user = self.bot.config["CHALLONGE_USER"]
        challonge.set_credentials(user, key)

    @commands.hybrid_group(
        name="tcl",
        description="Command group for Thandar Combat League.",
    )
    async def tcl(self, context: Context):
        """
        Command group for Thandar Combat League.

        :param context: The hybrid command context.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="You need to specify a subcommand.\n\n"
                            "**Subcommands:**\n"
                            "`signup` - Sign up for Thandar Combat League.\n"
                            "`report` - Report match results.\n"
                            "`standings` - Posts the current division standings.\n",
                color=0x992d22,
            )
            await context.send(embed=embed)

    @tcl.command(
        name="signup",
        description="Sign up for Thandar Combat League.",
    )
    async def signup(self, context: Context, hr_ign: str):
        """
        Sign up for Thandar Combat League.

        :param context: The hybrid command context.
        :param hr_ign: Your Hero Realms In Game Name.
        """
        embed = discord.Embed(
            description=f"You have been added to the Thandar Combat League waitlist. You can find the rules document "
                        f"[here](https://agentc13.com/tcl-rules.html)",
            color=0x992d22,
        )
        try:
            await context.author.send(embed=embed)
            user_id = context.author.id
            if await db_manager.is_signed_up(user_id):
                embed = discord.Embed(
                    description=f"**{context.author}** is already on waitlist.",
                    color=0x992d22,
                )
                await context.send(embed=embed)
                return
            total = await db_manager.add_user_to_waitlist(user_id, hr_ign)
            embed = discord.Embed(
                description=f"**{context.author}** has been successfully added to the waitlist.",
                color=0x992d22,
            )
            embed.set_footer(
                text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} in "
                     f"Thandar Combat League"
            )
            await context.send(embed=embed)
        except discord.Forbidden:
            await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="report",
        description="Allows user to report a Thandar Combat League match result.",
    )
    async def report(self, context: Context, division_name: str, round_number: int, winner_name: str, games_won_by_winner: int):
        """
        Allows user to report a Thandar Combat League match result.

        :param context: The hybrid command context.
        :param division_name: The name of the division.
        :param round_number: The round number in which the match took place.
        :param winner_name: The name of the winner of the match.
        :param games_won_by_winner: The number of games won by the winner of the match.
        """
        # Calculate loser's score by subtracting winner's score from total score (3)
        games_won_by_loser = 3 - games_won_by_winner

        # Check if the winner's score is valid (between 0 and 3)
        if games_won_by_loser < 0 or games_won_by_winner not in [2, 3]:
            embed = discord.Embed(title='Error!',
                                  description='Winner score is incorrect. It must be 2 or 3.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
            return

        # Get all tournaments from the Challonge API
        tournaments = challonge.tournaments.index(state='all')

        # Find the tournament with the specified division name
        tournament = next((t for t in tournaments if t['name'].lower() == division_name.lower()), None)

        # Check if the tournament was found
        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'TDivision "{division_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
            return

        # Get all participants of the found tournament
        participants = challonge.participants.index(tournament['id'])

        # Find the participant with the specified winner's name
        winner = next((p for p in participants if p['name'].lower() == winner_name.lower()), None)

        # Check if the winner was found
        if winner is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Participant "{winner_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
            return

        # Get all open matches of the tournament
        matches = challonge.matches.index(tournament['id'], state='open')

        # Find the match with the specified round number and the winner as one of the players
        match = next((m for m in matches if m['round'] == round_number and (m['player1_id'] == winner['id'] or m['player2_id'] == winner['id'])), None)

        # Check if the match was found
        if match is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Match for round "{round_number}" not found or match already closed.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
            return

        # Update the match with the winner's and loser's scores and set the winner
        if match['player1_id'] == winner['id']:
            challonge.matches.update(tournament['id'], match['id'], scores_csv=f"{games_won_by_winner}-{games_won_by_loser}", winner_id=winner['id'])
        else:
            challonge.matches.update(tournament['id'], match['id'], scores_csv=f"{games_won_by_loser}-{games_won_by_winner}", winner_id=winner['id'])

        # Send a success message to the user
        embed = discord.Embed(title="Match Reported",
                              description=f'Match result has been reported. Winner: {winner_name}, Score: {games_won_by_winner}-{games_won_by_loser}',
                              color=0x206694)
        await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="standings",
        description="Display the standings for a Thandar Combat League division.",
    )
    async def standings(self, context: Context, division_name: str):
        """
        Display the standings for a Thandar Combat League division.

        :param context: The hybrid command context.
        :param division_name: The name of the Thandar Combat League division.
        """
        pass

    # Start Tournament Organizer specific commands.
    @tcl.command(
        base="tcl",
        name="remove_waitlist",
        description="Removes a player from the Thandar Combat League waitlist.",
        hidden=True,
    )
    @commands.has_role("Tournament Organizer")
    async def remove_waitlist(self, context: Context, user: discord.User):
        """
        Removes a player from the Thandar Combat League waitlist.

        :param context: The hybrid command context.
        :param user: The user that should be removed from the waitlist.
        """
        user_id = user.id
        if not await db_manager.is_signed_up(user_id):
            embed = discord.Embed(
                description=f"**{user.name}** is not on the waitlist.", color=0x992d22
            )
            await context.send(embed=embed)
            return
        total = await db_manager.remove_user_from_waitlist(user_id)
        embed = discord.Embed(
            description=f"**{user.name}** has been successfully removed from the waitlist.",
            color=0x992d22,
        )
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} on the waitlist."
        )
        await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="create_division",
        description="Creates a new Thandar Combat League division.",
        hidden=True,
    )
    @commands.has_role("Tournament Organizer")
    async def create_division(self, context: Context, name: str):
        """
        Creates a new Thandar Combat League division.

        :param context: The hybrid command context.
        :param name: Name of division.
        """
        new_tournament_name = f'{name}'
        unique_url = f"{name}{int(time.time())}".replace(" ", "")  # Create a unique URL
        new_tournament = challonge.tournaments.create(new_tournament_name,
                                                      url=unique_url,
                                                      tournament_type="round robin",
                                                      game_name="Hero Realms Digital",
                                                      ranked_by="points scored",
                                                      tie_breaks=["match wins", "game win percentage", "points scored"]
                                                      )
        embed = discord.Embed(title="Tournament Created",
                              description=f"Name: {new_tournament_name}\nURL: {unique_url}\nGame: Hero Realms Digital",
                              color=0xc27c0e)
        await context.send(embed=embed)

    # Tournament Organizer command to add players into a specified division.
    @tcl.command(
        base="tcl",
        name="add_player",
        description="Adds player to Thandar Combat League division.",
        hidden=True,
    )
    @commands.has_role("Tournament Organizer")
    async def add_player(self, context: Context, division_name: str, hr_ign: str):
        """
        Adds player to Thandar Combat League division.

        :param context: The hybrid command context.
        :param division_name: The Thandar Combat League division that the user should be added to.
        :param hr_ign: The Hero Realms In Game Name for the user to be added to Thandar Combat League.
        """
        # Get the list of all tournaments
        tournaments = challonge.tournaments.index(state='all')

        # Find the tournament by its name
        tournament = next((t for t in tournaments if t['name'] == division_name), None)

        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Tournament "{division_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # If the tournament exists, add the participant.
            participant = challonge.participants.create(tournament['id'], hr_ign)
            embed = discord.Embed(title="Participant Added",
                                  description=f'Participant {participant["name"]} added to tournament {tournament["name"]}',
                                  color=0x1f8b4c)
            await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="remove_player",
        description="Removes a player from a Thandar Combat League waitlist.",
        hidden=True,
    )
    @commands.has_role("Tournament Organizer")
    async def remove_player(self, context: Context, user: discord.User):
        """
        Removes a player from the Thandar Combat League waitlist.

        :param context: The hybrid command context.
        :param user: The user that should be removed from the waitlist.
        """
        user_id = user.id
        if not await db_manager.is_signed_up(user_id):
            embed = discord.Embed(
                description=f"**{user.name}** is not on the waitlist.", color=0x992d22
            )
            await context.send(embed=embed)
            return
        total = await db_manager.remove_user_from_waitlist(user_id)
        embed = discord.Embed(
            description=f"**{user.name}** has been successfully removed from the waitlist.",
            color=0x992d22,
        )
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} on the waitlist."
        )
        await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="show_division",
        description="Lists the players in a Thandar Combat League division.",
        hidden=True,
    )
    @commands.has_role("Tournament Organizer")
    async def show_division(self, context: Context, division_name: str):
        """
        Lists the players in a Thandar Combat League division.

        :param context: The hybrid command context.
        :param division_name: Name of the Thandar Combat League Division.
        """
        tournaments = challonge.tournaments.index(state='all')
        tournament = next((t for t in tournaments if t['name'] == division_name), None)
        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Division "{division_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            participants = challonge.participants.index(tournament['id'])
            participant_names = [p['name'] for p in participants]
            participant_list = '\n'.join(participant_names)
            embed = discord.Embed(title=f'Participants in division "{division_name}"',
                                  description=participant_list,
                                  color=0x992d22)
            await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="show_waitlist",
        description="Lists the players in the Thandar Combat League waitlist.",
        hidden=True,
    )
    @commands.has_role("Tournament Organizer")
    async def show_waitlist(self, context: Context):
        """
        Lists the players in the Thandar Combat League waitlist.

        :param context: The hybrid command context.
        """
        # Get waitlist from db.
        participants = await db_manager.get_waitlist()
        participant_names = [p[1] for p in participants]
        participant_list = '\n'.join(participant_names)
        embed = discord.Embed(title=f'Players signed up for Thandar Combat League',
                              description=participant_list,
                              color=0x992d22)
        await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="show_matches",
        description="Display the weeks' matches for a Thandar Combat League division up to a specified round.",
        hidden=True,
    )
    @commands.has_role("Tournament Organizer")
    async def show_matches(self, context: Context, division_name: str, max_round: int):
        """
        Display the weeks' matches for a Thandar Combat League division up to a specified round.

        :param context: The hybrid command context.
        :param division_name: Name of the tournament whose matches will be returned.
        :param max_round: The maximum round to display matches for.
        """
        tournaments = challonge.tournaments.index(state='all')
        tournament = next((t for t in tournaments if t['name'].lower() == division_name.lower()), None)
        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Division "{division_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            matches = challonge.matches.index(tournament['id'], state='open')
            participants = challonge.participants.index(tournament['id'])
            participant_ids = {p['id']: p for p in participants}
            bracket = []
            for match in matches:
                if match['round'] > max_round:
                    continue
                if match['player1_id'] is not None and match['player2_id'] is not None:
                    p1_name = participant_ids[match['player1_id']]['name']
                    p2_name = participant_ids[match['player2_id']]['name']
                else:
                    p1_name = "TBD"
                    p2_name = "TBD"
                round_num = match.get('round', 'N/A')
                bracket.append((match['id'], p1_name, p2_name, round_num))
            bracket_str = tabulate(bracket, headers=["Match ID", "Player 1", "Player 2", "Round"])

            embed = discord.Embed(title=division_name, description='Division Matches', color=0x206694)
            embed.add_field(name='Week', value='\n'.join([str(b[3]) for b in bracket]))
            embed.add_field(name='Player 1', value='\n'.join([b[1] for b in bracket]))
            embed.add_field(name='Player 2', value='\n'.join([b[2] for b in bracket]))

            await context.send(embed=embed)

            # Define the start_division command, which allows a tournament organizer to start a round robin tournament for a division.
    @tcl.command(
        base="tcl",
        name="start_division",
        description="Allows a Tournament Organizer to start a TCL division in Challonge.",
        hidden=True,
    )
    @commands.has_role("Tournament Organizer")
    async def start_division(self, context: Context, division_name: str):
        """
        Allows a Tournament Organizer to start a TCL division in challonge.

        :param context: The hybrid command context.
        :param division_name: Name of the division.
        """
        # Get the list of all tournaments
        tournaments = challonge.tournaments.index(state='all')

        # Find the tournament by its name
        tournament = next((t for t in tournaments if t['name'].lower() == division_name.lower()), None)

        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Division "{division_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # Randomize seeds before starting the tournament
            challonge.participants.randomize(tournament['id'])

            challonge.tournaments.start(tournament['id'])
            embed = discord.Embed(title="Division Started",
                                  description=f'Thandar Combat League {tournament["name"]} has started!',
                                  color=0x206694)
            await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="end_division",
        description="Finalizes the season for a Thandar Combat League division.",
        hidden=True,
    )
    @commands.has_role("Tournament Organizer")
    async def end_division(self, context: Context, division_name: str):
        """
        Finalizes the season for a Thandar Combat League division.

        :param context: The hybrid command context.
        :param division_name: The name of the division.
        """
        tournaments = challonge.tournaments.index(state='all')
        tournament = next((t for t in tournaments if t['name'].lower() == division_name.lower()), None)

        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'TDivision "{division_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # Finalize the tournament
            challonge.tournaments.finalize(tournament['id'])


async def setup(bot):
    await bot.add_cog(Tcl(bot))
