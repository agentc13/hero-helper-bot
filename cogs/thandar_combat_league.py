import discord
import challonge
import time
import operator
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
                colour=discord.Colour.dark_orange(),
            )
            await context.send(embed=embed)

    # This code defines a command named "signup" in a discord bot for signing up for the Thandar Combat League.
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
        # Get the user ID of the author who triggered the command.
        user_id = context.author.id

        # Check if the user is already signed up.
        if await db_manager.is_signed_up(user_id):
            # If the user is already signed up, create an embed message indicating that.
            embed = discord.Embed(
                title="Error!",
                description=f"**{context.author.mention}** is already on waitlist.",
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
            return

        # Create an embed message with information about being added to the waitlist.
        embed = discord.Embed(
            description=f"You have been added to the Thandar Combat League waitlist. You can find the rules document "
                        f"[here](https://agentc13.com/tcl-rules.html)",
            colour=discord.Colour.dark_gold(),
        )

        try:
            # Send the embed message to the user who triggered the command.
            await context.author.send(embed=embed)

            # Add the user to the waitlist and get the total number of users on the waitlist.
            total = await db_manager.add_user_to_waitlist(user_id, hr_ign)

            # Create an embed message indicating that the user has been successfully added to the waitlist.
            embed = discord.Embed(
                title="Success!",
                description=f"**{context.author.mention}** has been successfully added to the waitlist.",
                colour=discord.Colour.dark_blue(),
            )
            embed.set_footer(
                text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} in "
                     f"Thandar Combat League"
            )

            # Send the embed message indicating successful signup to the channel where the command was triggered.
            await context.send(embed=embed)
        except discord.Forbidden:
            # If sending a direct message to the user is forbidden, send the embed message to the channel instead.
            await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="report",
        description="Allows user to report a Thandar Combat League match result.",
    )
    async def report(self, context: Context, round_number: int, winner_name: str, games_won_by_winner: int):
        """
        Allows user to report a Thandar Combat League match result.

        :param context: The hybrid command context.
        :param round_number: The round number in which the match took place.
        :param winner_name: The name of the winner of the match.
        :param games_won_by_winner: The number of games won by the winner of the match.
        """
        division_name = context.channel.name  # Get division_name from channel name

        # Challonge community (subdomain) hosting the tournament
        community_name = "b5d0ca83e61253ea7f84a60c"

        # Calculate loser's score by subtracting winner's score from total score (3)
        games_won_by_loser = 3 - games_won_by_winner

        # Check if the winner's score is valid (between 0 and 3)
        if games_won_by_loser < 0 or games_won_by_winner not in [2, 3]:
            embed = discord.Embed(
                title='Error!',
                description='Winner score is incorrect. It must be 2 or 3.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
            return

        # Get all tournaments from the Challonge API
        tournaments = challonge.tournaments.index(state='all', subdomain=community_name)

        # Find the tournament with the specified division name
        tournament = next((t for t in tournaments if t['name'].lower() == division_name.lower()), None)

        # Check if the tournament was found
        if tournament is None:
            embed = discord.Embed(
                title='Error!',
                description=f'Division "{division_name}" not found.',
                colour=discord.Colour.dark_red(),
                )
            await context.send(embed=embed)
            return

        # Get all participants of the found tournament
        participants = challonge.participants.index(tournament['id'])

        # Find the participant with the specified winner's name
        winner = next((p for p in participants if p['name'].lower() == winner_name.lower()), None)

        # Check if the winner was found
        if winner is None:
            embed = discord.Embed(
                title='Error!',
                description=f'Participant "{winner_name}" not found.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
            return

        # Get all open matches of the tournament
        matches = challonge.matches.index(tournament['id'], state='open', subdomain=community_name)

        # Find the match with the specified round number and the winner as one of the players
        match = next((m for m in matches if m['round'] == round_number and (
                    m['player1_id'] == winner['id'] or m['player2_id'] == winner['id'])), None)

        # Check if the match was found
        if match is None:
            embed = discord.Embed(
                title='Error!',
                description=f'Match for round "{round_number}" not found or match already closed.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
            return

        # Update the match with the winner's and loser's scores and set the winner
        if match['player1_id'] == winner['id']:
            challonge.matches.update(tournament['id'], match['id'],
                                     scores_csv=f"{games_won_by_winner}-{games_won_by_loser}", winner_id=winner['id'],
                                     subdomain=community_name)
        else:
            challonge.matches.update(tournament['id'], match['id'],
                                     scores_csv=f"{games_won_by_loser}-{games_won_by_winner}", winner_id=winner['id'],
                                     subdomain=community_name)

        # Send a success message to the user
        embed = discord.Embed(
            title="Match Reported",
            description=f'Match result has been reported. Winner: {winner_name}, Score: {games_won_by_winner}-{games_won_by_loser}',
            colour=discord.Colour.dark_blue(),
            )
        await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="standings",
        description="Display the standings for a Thandar Combat League division.",
    )
    async def standings(self, context: Context):
        """
        Display the standings for a Thandar Combat League division.

        :param context: The hybrid command context.
        """
        division_name = context.channel.name.replace("-",
                                                     " ")  # Get division_name from channel name and replace "-" with " "

        # Challonge community (subdomain) hosting the tournament
        community_name = "b5d0ca83e61253ea7f84a60c"

        # Retrieve the list of tournaments from Challonge
        tournaments = challonge.tournaments.index(subdomain=community_name)
        tournament = None
        # Search for a tournament that matches the provided division name
        for t in tournaments:
            if t['name'].lower() == division_name.lower():
                tournament = t
                break

        if tournament is None:
            # If no matching tournament is found, send an error message
            embed = discord.Embed(
                title='Error!',
                description=f'Division "{division_name}" not found.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
            return

        # Retrieve the matches for the selected tournament
        matches = challonge.matches.index(tournament["id"], subdomain=community_name)

        # Dictionary to store player statistics
        players = {}
        for match in matches:
            player1_id = match['player1_id']
            player2_id = match['player2_id']

            # Initialize player statistics if they don't exist in the dictionary
            if player1_id not in players:
                players[player1_id] = {"wins": 0, "losses": 0, "match_wins": 0, "match_losses": 0}
            if player2_id not in players:
                players[player2_id] = {"wins": 0, "losses": 0, "match_wins": 0, "match_losses": 0}

            if match['scores_csv']:
                scores = match['scores_csv'].split('-')
                player1_score = int(scores[0])
                player2_score = int(scores[1])

                # Update player statistics based on match results
                players[player1_id]['wins'] += player1_score
                players[player1_id]['losses'] += player2_score
                players[player2_id]['wins'] += player2_score
                players[player2_id]['losses'] += player1_score

                # Increment match wins and losses
                if player1_score > player2_score:
                    players[player1_id]['match_wins'] += 1
                    players[player2_id]['match_losses'] += 1
                else:
                    players[player1_id]['match_losses'] += 1
                    players[player2_id]['match_wins'] += 1

        standings = []
        for player_id, stats in players.items():
            # Calculate win percentage for each player
            win_percentage = round(stats['wins'] / (stats['wins'] + stats['losses']) * 100, 2)
            # Retrieve player information from Challonge
            player = challonge.participants.show(tournament["id"], player_id, subdomain=community_name)
            # Append player statistics to the standings list
            standings.append({
                "name": player['name'],
                "wins": stats['wins'],
                "losses": stats['losses'],
                "win_percentage": win_percentage,
                "match_wins": stats['match_wins']
            })

        # Sort the standings list based on win percentage and match wins in descending order
        standings.sort(key=operator.itemgetter('win_percentage', 'match_wins'), reverse=True)

        # Create the embed to be sent
        embed = discord.Embed(
            title=f"{tournament['name'].title()}",
            description="Player Statistics",
            colour=discord.Colour.dark_green(),
        )
        for player in standings:
            # Add a field to the embed for each player, displaying their statistics
            embed.add_field(
                name=player['name'],
                value=f"Wins: {player['wins']}\nLosses: {player['losses']}\nWin%: {player['win_percentage']}\nMatch Wins: {player['match_wins']}",
                inline=False
            )

        # Send the embed as a message in the Discord channel
        await context.send(embed=embed)

    # Start Tournament Organizer specific commands.
    @tcl.command(
        base="tcl",
        name="remove_waitlist",
        description="Removes a player from the Thandar Combat League waitlist.",
        hidden=True,
    )
    @commands.has_role("TCL Organizer")
    async def remove_waitlist(self, context: Context, user: discord.User):
        """
        Removes a player from the Thandar Combat League waitlist.

        :param context: The hybrid command context.
        :param user: The user that should be removed from the waitlist.
        """
        # Retrieve the ID of the user to be removed from the waitlist
        user_id = user.id

        # Check if the user is already signed up on the waitlist
        if not await db_manager.is_signed_up(user_id):
            # User is not on the waitlist, send an error message
            embed = discord.Embed(
                description=f"**{user.name}** is not on the waitlist.",
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
            return

        # Remove the user from the waitlist and get the updated total count
        total = await db_manager.remove_user_from_waitlist(user_id)

        # Create an embedded message indicating successful removal
        embed = discord.Embed(
            description=f"**{user.name}** has been successfully removed from the waitlist.",
            colour=discord.Colour.dark_blue(),
        )

        # Set the footer text based on the number of users remaining on the waitlist
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} on the waitlist."
        )

        # Send the embedded message as a response in the Discord channel
        await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="create_division",
        description="Creates a new Thandar Combat League division.",
        hidden=True,
    )
    @commands.has_role("TCL Organizer")
    async def create_division(self, context: Context, name: str):
        """
        Creates a new Thandar Combat League division.

        :param context: The hybrid command context.
        :param name: Name of division.
        """
        new_tournament_name = f'{name}'
        # Creates a unique url based on the tournament name and time
        unique_url = f"{name}{int(time.time())}".replace(" ", "")
        # Adds the tournament into Challonge.
        new_tournament = challonge.tournaments.create(new_tournament_name,
                                                      url=unique_url,
                                                      tournament_type="round robin",
                                                      game_name="Hero Realms Digital",
                                                      ranked_by="points scored",
                                                      subdomain="b5d0ca83e61253ea7f84a60c",
                                                      tie_breaks=["match wins", "game win percentage", "points scored"]
                                                      )

        # Gets division role id for permissions
        division_role = discord.utils.get(context.guild.roles, name=f"{name}")

        # Get the Hero-Helper role
        hero_helper_role = discord.utils.get(context.guild.roles, name="Hero-Helper")

        # If no role with that name exists, create a new one
        if division_role is None:
            division_role = await context.guild.create_role(name=f"{name}")

        # Get the category under which to create the channel
        category = discord.utils.get(context.guild.categories, name="Thandar Combat League")

        # Permissions overwrites
        overwrites = {
            context.guild.default_role: discord.PermissionOverwrite(read_messages=False),  # Default
            division_role: discord.PermissionOverwrite(read_messages=True),  # Division
            hero_helper_role: discord.PermissionOverwrite(read_messages=True),  # Hero-Helper
            context.guild.get_member(237772104416755712): discord.PermissionOverwrite(read_messages=True),  # Tim
            context.guild.get_member(617875604527775767): discord.PermissionOverwrite(read_messages=True),  # Sam
            context.guild.get_member(189143550091460608): discord.PermissionOverwrite(read_messages=True),  # Chris
        }

        # Create a new discord channel with the division name
        await context.guild.create_text_channel(name, overwrites=overwrites, category=category)

        # Creates and sends an embed with the tournament info.
        embed = discord.Embed(
            title="Division Created",
            description=f"Name: {new_tournament_name}\nGame: Hero Realms Digital",
            colour=discord.Colour.dark_gold(),
        )
        await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="add_players",
        description="Adds players to Thandar Combat League division.",
        hidden=True,
    )
    @commands.has_role("TCL Organizer")
    async def add_players(self, context: Context, division_name: str, hr_igns: str):
        """
        Adds players to Thandar Combat League division.

        :param context: The hybrid command context.
        :param division_name: The Thandar Combat League division that the users should be added to.
        :param hr_igns: A string of comma-separated usernames for the users to be added to Thandar Combat League.
        """
        # Challonge community (subdomain) hosting the tournament
        community_name = "b5d0ca83e61253ea7f84a60c"

        # Get the list of all tournaments
        tournaments = challonge.tournaments.index(state='pending', subdomain=community_name)

        # Find the tournament by its name
        tournament = next((t for t in tournaments if t['name'].lower() == division_name.lower()), None)

        if tournament is None:
            embed = discord.Embed(
                title='Error!',
                description=f'Tournament "{division_name}" not found.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
        else:
            # If the tournament exists, add the participants.
            hr_igns_list = [ign.strip() for ign in hr_igns.split(',')]  # Split the input string into a list

            for hr_ign in hr_igns_list:
                participant = challonge.participants.create(tournament['id'], hr_ign, subdomain=community_name)

                # Get the Discord user ID from the database based on HR IGN
                user_id = await db_manager.get_user_id_from_db(hr_ign)

                if user_id:
                    guild = context.guild
                    member = guild.get_member(user_id)  # Try fetching the member

                    if member is None:
                        # Member not found, fetch the member using Discord's API
                        try:
                            member = await guild.fetch_member(user_id)
                        except discord.NotFound:
                            member = None

                    if member:
                        # Assign the role with the same name as the division to the player
                        role_name = division_name.title()
                        role = discord.utils.get(guild.roles, name=role_name)
                        if role:
                            await member.add_roles(role)

                embed = discord.Embed(
                    title="Participant Added",
                    description=f'Participant {participant["name"]} added to tournament {tournament["name"]}',
                    colour=discord.Colour.dark_blue(),
                )
                await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="show_division",
        description="Lists the players in a Thandar Combat League division.",
        hidden=True,
    )
    @commands.has_role("TCL Organizer")
    async def show_division(self, context: Context, division_name: str):
        """
        Lists the players in a Thandar Combat League division.

        :param context: The hybrid command context.
        :param division_name: Name of the Thandar Combat League Division.
        """

        # Challonge community (subdomain) hosting the tournament
        community_name = "b5d0ca83e61253ea7f84a60c"

        # Get a list of all tournaments in the Challonge community
        tournaments = challonge.tournaments.index(state='all', subdomain=community_name)

        # Find the tournament that matches the provided division name
        tournament = next((t for t in tournaments if t['name'].lower() == division_name.lower()), None)

        if tournament is None:
            # If the tournament is not found, display an error message
            embed = discord.Embed(
                title='Error!',
                description=f'Division "{division_name}" not found.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
        else:
            # If the tournament is found, retrieve the list of participants
            participants = challonge.participants.index(tournament['id'])
            participant_names = [p['name'] for p in participants]
            participant_list = '\n'.join(participant_names)

            # Create an embed message with the list of participants and send it
            embed = discord.Embed(
                title=f'Participants in division "{division_name}"',
                description=participant_list,
                colour=discord.Colour.dark_magenta(),
            )
            await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="show_waitlist",
        description="Lists the players in the Thandar Combat League waitlist.",
        hidden=True,
    )
    @commands.has_role("TCL Organizer")
    async def show_waitlist(self, context: Context):
        """
        Lists the players in the Thandar Combat League waitlist.

        :param context: The hybrid command context.
        """
        # Get waitlist from db.
        participants = await db_manager.get_waitlist()
        participant_names = [p[1] for p in participants]
        participant_list = '\n'.join(participant_names)
        # Creates and sends an embed showing the participants on the waitlist.
        embed = discord.Embed(
            title=f'Players signed up for Thandar Combat League',
            description=participant_list,
            colour=discord.Colour.dark_magenta(),
        )
        await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="show_matches",
        description="Display the weeks' matches for a Thandar Combat League division up to a specified round.",
        hidden=True,
    )
    @commands.has_role("TCL Organizer")
    async def show_matches(self, context: Context, division_name: str, max_round: int):
        """
        Display the weeks' matches for a Thandar Combat League division up to a specified round.

        :param context: The hybrid command context.
        :param division_name: Name of the tournament whose matches will be returned.
        :param max_round: The maximum round to display matches for.
        """

        # Challonge community (subdomain) hosting the tournament
        community_name = "b5d0ca83e61253ea7f84a60c"

        # Get all tournaments from Challonge with the specified subdomain
        tournaments = challonge.tournaments.index(state='all', subdomain=community_name)

        # Find the tournament with the specified division name
        tournament = next((t for t in tournaments if t['name'].lower() == division_name.lower()), None)

        if tournament is None:
            # If the tournament is not found, display an error message
            embed = discord.Embed(
                title='Error!',
                description=f'Division "{division_name}" not found.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
        else:
            # Get the matches for the tournament
            matches = challonge.matches.index(tournament['id'], state='open', subdomain=community_name)

            # Get the participants for the tournament
            participants = challonge.participants.index(tournament['id'])
            participant_ids = {p['id']: p for p in participants}

            bracket = []
            for match in matches:
                if match['round'] > max_round:
                    continue

                # Get the names of the players for each match
                if match['player1_id'] is not None and match['player2_id'] is not None:
                    p1_name = participant_ids[match['player1_id']]['name']
                    p2_name = participant_ids[match['player2_id']]['name']
                else:
                    p1_name = "TBD"
                    p2_name = "TBD"

                round_num = match.get('round', 'N/A')
                bracket.append((match['id'], p1_name, p2_name, round_num))

            # Create an embed to display the matches
            embed = discord.Embed(
                title=division_name.title(),
                description='Division Matches',
                colour=discord.Colour.dark_gold(),
            )

            # Sort the matches based on round number
            bracket.sort(key=lambda x: x[3])

            # Group the matches by round number
            grouped_matches = []
            current_round = None
            for match in bracket:
                if match[3] != current_round:
                    current_round = match[3]
                    grouped_matches.append((current_round, []))

                player1 = match[1]
                player2 = match[2]
                grouped_matches[-1][1].append(f'{player1} vs. {player2}\n')

            # Add the matches to the embed as fields
            for round_num, matches in grouped_matches:
                embed.add_field(name=f'Round {round_num}', value=''.join(matches), inline=False)

            # Send the embed as a message
            await context.send(embed=embed)

    # Define the start_division command, which allows a tournament organizer to start a round robin tournament for a division.
    @tcl.command(
        base="tcl",
        name="start_division",
        description="Allows a Tournament Organizer to start a TCL division in Challonge.",
        hidden=True,
    )
    @commands.has_role("TCL Organizer")
    async def start_division(self, context: Context, division_name: str):
        """
        Allows a Tournament Organizer to start a TCL division in challonge.

        :param context: The hybrid command context.
        :param division_name: Name of the division.
        """
        # Challonge community (subdomain) hosting the tournament
        community_name = "b5d0ca83e61253ea7f84a60c"

        # Get the list of all tournaments
        tournaments = challonge.tournaments.index(state='all', subdomain=community_name)

        # Find the tournament by its name
        tournament = next((t for t in tournaments if t['name'].lower() == division_name.lower()), None)

        if tournament is None:
            embed = discord.Embed(
                title='Error!',
                description=f'Division "{division_name}" not found.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
        else:
            # Randomize seeds before starting the tournament
            challonge.participants.randomize(tournament['id'])

            challonge.tournaments.start(tournament['id'], subdomain=community_name)
            embed = discord.Embed(
                title="Division Started",
                description=f'Thandar Combat League {tournament["name"]} has started!',
                colour=discord.Colour.dark_blue(),
            )
            await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="end_division",
        description="Finalizes the season for a Thandar Combat League division.",
        hidden=True,
    )
    @commands.has_role("TCL Organizer")
    async def end_division(self, context: Context, division_name: str):
        """
        Finalizes the season for a Thandar Combat League division.

        :param context: The hybrid command context.
        :param division_name: The name of the division.
        """
        # Challonge community (subdomain) hosting the tournament
        community_name = "b5d0ca83e61253ea7f84a60c"

        tournaments = challonge.tournaments.index(state='all', subdomain=community_name)
        tournament = next((t for t in tournaments if t['name'].lower() == division_name.lower()), None)

        if tournament is None:
            embed = discord.Embed(
                title='Error!',
                description=f'Division "{division_name}" not found.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
        else:
            # Finalize the tournament
            challonge.tournaments.finalize(tournament['id'], subdomain=community_name)

    @tcl.command(
        name="create_season",
        description="Creates a new season of Thandar Combat League.",
    )
    @commands.has_role("TCL Organizer")
    async def create_season(self, context: Context, season_number: int):
        """
        Creates a new season for Thandar Combat League.
        :param context: The command context.
        :param season_number: The season number.
        """
        try:
            # Get all users from the waitlist.
            waitlist = await db_manager.get_waitlist()

            # For each user in the waitlist, add them to the tcl_participants table.
            for user in waitlist:
                await db_manager.add_user_to_participants(user[0], user[1])

            # Clear the waitlist for the next season.
            await db_manager.clear_waitlist()

            # Provided division names
            division_names = ["Fire Bomb", "Domination", "Rampage", "Life Drain", "Deception", "Command", "Elven Curse", "Death Touch"]

            # Calculate the number of divisions to be created
            num_divisions = len(waitlist) // 8
            if len(waitlist) % 8 != 0:
                num_divisions += 1  # Add one more division if there are leftover participants

            # Ensure there are enough division names for the divisions to be created
            if num_divisions > len(division_names):
                raise ValueError("Not enough division names provided for the number of divisions to be created")

            # Create each division using the provided names
            for i in range(num_divisions):
                # Prefix each division name with "S# "
                division_name = f"S{season_number} {division_names[i]}"
                await self.create_division(context, division_name)

            # Create an embed message indicating the start of the new season.
            embed = discord.Embed(
                title="Season Created!",
                description=f"Season {season_number} of Thandar Combat League has been created with {num_divisions} division(s)!",
                colour=discord.Colour.dark_blue(),
            )
            embed.set_footer(
                text=f"There are now {len(waitlist)} participants in this season of Thandar Combat League."
            )

            # Send the embed message indicating successful season start to the channel where the command was triggered.
            await context.send(embed=embed)
        except Exception as e:
            # If there was an error starting the season, send a message indicating the error.
            embed = discord.Embed(
                title="Error!",
                description=f"An error occurred while trying to create the season: {str(e)}",
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)

    @tcl.command(
        name="start_season",
        description="Starts a new season of Thandar Combat League.",
    )
    @commands.has_role("TCL Organizer")
    async def start_season(self, context: Context, season: int):
        """
        Start a new season for Thandar Combat League.
        :param context: The command context.
        :param season: The season number.
        """
        # Get all users from the waitlist.
        waitlist = await db_manager.get_waitlist()

        # For each user in the waitlist, add them to the tcl_participants table.
        for user in waitlist:
            await db_manager.add_user_to_participants(user[0], user[1])

        # Clear the waitlist for the next season.
        await db_manager.clear_waitlist()

        # Challonge community (subdomain) hosting the tournament
        community_name = "b5d0ca83e61253ea7f84a60c"

        # Get the list of all tournaments
        tournaments = challonge.tournaments.index(state='all', subdomain=community_name)

        # Find all tournaments that start with 'S{season}'
        season_tournaments = [t for t in tournaments if t['name'].lower().startswith(f's{season}')]

        # Start each season tournament
        for tournament in season_tournaments:
            # Randomize seeds before starting the tournament
            challonge.participants.randomize(tournament['id'])

            challonge.tournaments.start(tournament['id'], subdomain=community_name)

        # Mention the "Thandar Combat League" role
        role = discord.utils.get(context.guild.roles, id=1088139361217945688)
        # Get the channel ID of the specific channel you want to send the message to
        channel_id = 1088139363294130200

        # Obtain the channel object using the channel ID
        channel = context.guild.get_channel(channel_id)

        if channel:
            # Send the message to the specific channel
            await channel.send(
                f"{role.mention}\n"
                f"**Season {season} of Thandar Combat League has started!**\n\n"
                f"Thank you all so much for participating! I have done a major overhaul on the backend/organizational side of things in order to use the Hero-Helper Bot to track and record everything.  The match reporting/tracking process will now happen in discord using bot commands. *These commands will only work in your specific division channels!*\n\n"
                f"`/tcl report` -This command will report an open match result. You will need to enter the round number, winner's name, and the number of games that were won by the winner of the match. Either player can report results and once reported duplicate reports will not mess things up.\n\n"
                f"`/tcl standings` - This command will post the current division standings, listing players from first to last using win percentage as the primary metric. Match wins are the first tiebreaker.  I have not coded in the final head-to-head tie-breaker yet so the command will not take that into account and will randomly list players who are tied.\n\n"
                f"If you are not familiar with discord bot commands, I made some tutorial videos for the Hero-Helper Bot that you can check out:\n"
                f"Introduction to Hero-Helper Bot: [link here]\n"
                f"Thandar Combat League with Hero-Helper Bot: [link here]\n\n"
                f"Be sure to keep an eye on this channel for league-wide announcements, and your division channel for the division specific stuff. Feel free to let me know if there are any questions.\n\n"
                f"Good luck and let the battles begin!"
            )
            await context.send("Season announcement sent!")
        else:
            # Channel not found, send an error message
            await context.send("The specified channel was not found.")

    @tcl.command(
        base="tcl",
        name="end_season",
        description="Finalizes all divisions for a Thandar Combat League season.",
        hidden=True,
    )
    @commands.has_role("TCL Organizer")
    async def end_season(self, context: Context, season: int):
        """
        Finalizes all divisions for a Thandar Combat League season.

        :param context: The hybrid command context.
        :param season: The season number.
        """
        # Challonge community (subdomain) hosting the tournament
        community_name = "b5d0ca83e61253ea7f84a60c"

        # Get the list of all tournaments
        tournaments = challonge.tournaments.index(state='all', subdomain=community_name)

        # Find all tournaments that belong to the specified season
        season_tournaments = [t for t in tournaments if t['name'].lower().startswith(f's{season}')]

        if not season_tournaments:
            embed = discord.Embed(
                title='Error!',
                description=f'No divisions found for season {season}.',
                colour=discord.Colour.dark_red(),
            )
            await context.send(embed=embed)
            return

        for tournament in season_tournaments:
            # Finalize each tournament
            challonge.tournaments.finalize(tournament['id'], subdomain=community_name)

        embed = discord.Embed(
            title='Success!',
            description=f'All divisions for season {season} have been finalized.',
            colour=discord.Colour.green(),
        )
        await context.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Tcl(bot))
