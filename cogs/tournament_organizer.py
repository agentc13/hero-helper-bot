import challonge
import discord
import time
from discord.ext import commands
from discord.ext.commands import Context


# Define the Quickfire class, which is a subclass of commands.Cog
class TournamentOrganizer(commands.Cog, name="tournament organizer"):
    def __init__(self, bot):
        self.bot = bot

        # Set Challonge API credentials
        key = self.bot.config["CHALLONGE_KEY"]
        user = self.bot.config["CHALLONGE_USER"]
        challonge.set_credentials(user, key)

    @commands.hybrid_group(
        name="to",
        description="Command group for Tournament Organizers.",
    )
    async def to(self, context: Context) -> None:
        """
        Command group for Tournament Organizers.

        :param context: The hybrid command context.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                description="You need to specify a subcommand.\n\n"
                            "**Subcommands:**\n"
                            "`create_tournament` - Creates a tournament in Challonge.\n"
                            "`remove_tournament` - Deletes a tournament from Challonge.\n"
                            "`start_tournament` - Starts a specific tournament in Challonge.\n"
                            "`add_player` - Allows a Tournament Organizer to manually add a player to a tournament.\n",
                color=0x992d22,
            )
            await context.send(embed=embed)

    # Define the create_tournament command, which allows a user to create a new tournament
    @to.command(
        name="create_tournament",
        description="Allows a Tournament Organizer to create a new tournament in Challonge.",
    )
    @commands.has_role("Tournament Organizer")
    async def create_tournament(self, context: Context, name: str, group: str, tournament_type: str):
        """
        Allows a Tournament Organizer to create a new tournament in Challonge.

        :param context: The hybrid command context.
        :param name: Name of tournament.
        :param group: The command group for the type of tournament being created.
        :param tournament_type: Type of tournament being created (single elimination, round robin, swiss, double elimination).
        """
        new_tournament_name = f'{name}'
        unique_url = f"{name}{int(time.time())}".replace(" ", "")  # Create a unique URL
        new_tournament = challonge.tournaments.create(new_tournament_name,
                                                      url=unique_url,
                                                      tournament_type=tournament_type,
                                                      game_name="Hero Realms Digital")
        embed = discord.Embed(title="Tournament Created",
                              description=f"Name: {new_tournament_name}\nURL: {unique_url}\nGame: Hero Realms Digital",
                              color=0xc27c0e)
        await context.send(embed=embed)
        await context.send(
            f'Sign ups for  "{new_tournament_name}" are open! Use the "/{group} signup {new_tournament_name}" command to join!')

    # Define the remove_tournament command, which allows a tournament organizer to delete a tournament
    @to.command(
        name="remove_tournament",
        description="Allows TO to delete a tournament from Challonge.",
    )
    @commands.has_role("Tournament Organizer")
    async def remove_tournament(self, context: Context, tournament_name: str):
        """
        Allows TO to delete a tournament from Challonge.

        :param context: The hybrid command context.
        :param tournament_name: Tournament name.
        """
        tournaments = challonge.tournaments.index(state='all')
        tournament = next((t for t in tournaments if t['name'] == tournament_name), None)
        if tournament is None:
            embed = discord.Embed(title='Error',
                                  description=f'Tournament "{tournament_name}" not found',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            challonge.tournaments.destroy(tournament['id'])
            embed = discord.Embed(title='Tournament Removed',
                                  description=f'{tournament_name} has been removed from active tournaments.',
                                  color=0xc27c0e)
            await context.send(embed=embed)

    # Define the start_tournament command, which allows a tournament organizer to start a tournament
    @to.command(
        name="start_tournament",
        description="Allows TO to start tournament",
    )
    @commands.has_role("Tournament Organizer")
    async def start_tournament(self, context: Context, tournament_name: str):
        """
        Allows a Tournament Organizer to start a tournament in Challonge.

        :param context: The hybrid command context.
        :param tournament_name: Name of the tournament.
        """
        # Get the list of all tournaments
        tournaments = challonge.tournaments.index(state='all')

        # Find the tournament by its name
        tournament = next((t for t in tournaments if t['name'] == tournament_name), None)

        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Tournament "{tournament_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # Randomize seeds before starting the tournament
            challonge.participants.randomize(tournament['id'])

            challonge.tournaments.start(tournament['id'])
            embed = discord.Embed(title="Tournament Started",
                                  description=f'Tournament {tournament["name"]} has been started',
                                  color=0x206694)
            await context.send(embed=embed)

    @to.command(
        name="reset_tournament",
        description="Allows TO to reset a tournament.",
    )
    @commands.has_role("Tournament Organizer")
    async def reset_tournament(self, context: Context, tournament_name: str):
        """
        Resets a Challonge tournament by its name.

        :param context: The hybrid command context.
        :param tournament_name: Tournament name.
        """
        tournaments = challonge.tournaments.index(state='all')
        tournament = next((t for t in tournaments if t['name'] == tournament_name), None)

        if tournament is None:
            embed = discord.Embed(title='Error',
                                  description=f'Tournament "{tournament_name}" not found',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # Reset the tournament
            challonge.tournaments.reset(tournament['id'])
            embed = discord.Embed(title='Tournament Reset',
                                  description=f'{tournament_name} has been reset.',
                                  color=0xc27c0e)
            await context.send(embed=embed)

    @to.command(
        name="add_player",
        description="Allows a Tournament Organizer to manually add a player to a tournament.",
    )
    @commands.has_role("Tournament Organizer")
    async def add_player(self, context: Context, tournament_name: str, player_name: str):
        """
        Allows a Tournament Organizer to manually add a player to a tournament.

        :param context: The hybrid command context.
        :param tournament_name: Name of the tournament.
        :param player_name: Discord name of player to add.
        """
        # Get the list of all tournaments
        tournaments = challonge.tournaments.index(state='all')

        # Find the tournament by its name
        tournament = next((t for t in tournaments if t['name'] == tournament_name), None)

        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Tournament "{tournament_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # If the tournament exists, add the participant.
            participant = challonge.participants.create(tournament['id'], player_name)
            embed = discord.Embed(title="Participant Added",
                                  description=f'Participant {participant["name"]} added to tournament {tournament["name"]}',
                                  color=0x1f8b4c)
            await context.send(embed=embed)

    @to.command(
        name="remove_player",
        description="Allows a Tournament Organizer to manually remove a player from a tournament.",
    )
    @commands.has_role("Tournament Organizer")
    async def remove_player(self, context: Context, tournament_name: str, name: str):
        """
        Allows a Tournament Organizer to manually remove a player from a tournament.

        :param context: The command context.
        :param tournament_name: Tournament player_name.
        :param name: Name of the player to remove.
        """
        tournaments = challonge.tournaments.index(state='all')
        tournament = next((t for t in tournaments if t['name'] == tournament_name), None)

        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Tournament "{tournament_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # Get participants
            participants = challonge.participants.index(tournament['id'])

            # Find the player in the list of participants
            player_participant = next((p for p in participants if p["name"] == name), None)

            if player_participant is None:
                embed = discord.Embed(title='Error!',
                                      description=f'Player "{name}" not found in the list of participants.',
                                      color=0xe74c3c)
                await context.send(embed=embed)
            else:
                # Remove the player from the tournament
                challonge.participants.destroy(tournament['id'], player_participant['id'])
                await context.send(f'Player "{name}" has been removed from tournament "{tournament_name}"')
                embed = discord.Embed(title='Removed.',
                                      description=f'Player "{name}" has been removed from {tournament_name}.',
                                      color=0x71368a)
                await context.send(embed=embed)

    @to.command(
        name="finalize",
        description="Manually finalizes a Challonge tournament.",
    )
    @commands.has_role("Tournament Organizer")
    async def finalize(self, context: Context, tournament_name: str):
        """
        Manually finalizes a Challonge tournament.

        :param context: The command context.
        :param tournament_name: Tournament name.
        """
        tournaments = challonge.tournaments.index(state='all')
        tournament = next((t for t in tournaments if t['name'] == tournament_name), None)

        if tournament is None:
            embed = discord.Embed(title='Error!',
                                  description=f'Tournament "{tournament_name}" not found.',
                                  color=0xe74c3c)
            await context.send(embed=embed)
        else:
            # Finalize the tournament
            challonge.tournaments.finalize(tournament['id'])

            # Refresh tournament data
            tournament = challonge.tournaments.show(tournament['id'])

            if tournament['state'] == 'complete':
                # Get participants
                participants = challonge.participants.index(tournament['id'])

                # Find the winner in the list of participants
                winner_id = tournament['winner_id']
                winner_participant = next((p for p in participants if p["id"] == winner_id), None)

                # Create an embed with the winner's information
                embed = discord.Embed(
                    title=f'Tournament "{tournament_name}" is complete!',
                    description=f'Congratulations to the winner: {winner_participant["name"]}',
                    color=0x71368a
                )
                await context.send(embed=embed)
            else:
                embed = discord.Embed(title='Error!',
                                      description=f'Tournament "{tournament_name}" cannot be finalized.',
                                      color=0xe74c3c)
                await context.send(embed=embed)


# Define the setup function, which adds the Quickfire cog to the Hero-Helper Bot
async def setup(bot):
    await bot.add_cog(TournamentOrganizer(bot))
