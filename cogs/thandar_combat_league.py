import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from helpers import checks, db_manager


class Tcl(commands.Cog, name="tcl"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(
        name="tcl",
        description="Command group for Thandar Combat League.",
    )
    @checks.is_owner()
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
                            "`standings` - Posts the current division standings.\n\n"
                            "**Tournament Organizer Only**\n"
                            "`create_division` - Creates a new Thandar Combat League division.\n"
                            "`add` - Add a user to a Thandar Combat League division.\n"
                            "`remove` - Remove a user from Thandar Combat League division.\n"
                            "`show` - Lists players in a Thandar Combat League division.\n"
                            "`matches` - Posts matches for the week, and lists unreported matches from previous weeks.\n"
                            "`start` - Starts a Thandar Combat League division for the season.\n"
                            "`finalize` - Finalizes a Thandar Combat League division for the season.",
                color=0x992d22,
            )
            await context.send(embed=embed)

    @tcl.command(
        name="signup",
        description="Sign up for Thandar Combat League.",
    )
    async def signup(self, context: Context, hr_ign: str):
        """
        Sign up for Thandar Combat League. You will receive a DM with the rules
        link and be added to the list of players for the next season.

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
    async def report(self, context: Context):
        """
        Allows user to report a Thandar Combat League match result.

        :param context: The hybrid command context.
        """
        pass

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
        pass

    @tcl.command(
        base="tcl",
        name="add",
        description="Sign up for Thandar Combat League.",
    )
    @commands.has_role("Tournament Organizer")
    async def add(self, context: Context, user: discord.User, hr_ign: str):
        """
        Sign up for Thandar Combat League.

        :param context: The hybrid command context.
        :param user: The user that should be added to Thandar Combat League.
        :param hr_ign: The Hero Realms In Game Name for the user to be added to Thandar Combat League.
        """
        user_id = user.id
        if await db_manager.is_signed_up(user_id):
            embed = discord.Embed(
                description=f"**{user.name}** is already on the waitlist.",
                color=0x992d22,
            )
            await context.send(embed=embed)
            return
        total = await db_manager.add_user_to_waitlist(user_id, hr_ign)
        embed = discord.Embed(
            description=f"**{user.name}** has been successfully added to the waitlist",
            color=0x992d22,
        )
        embed.set_footer(
            text=f"There {'is' if total == 1 else 'are'} now {total} {'user' if total == 1 else 'users'} on the waitlist."
        )
        await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="remove",
        description="Lets you remove a user from the waitlist.",
    )
    @commands.has_role("Tournament Organizer")
    async def remove(self, context: Context, user: discord.User):
        """
        Lets you remove a user from the waitlist.

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
        name="show",
        description="Lists the players in a Thandar Combat League division.",
    )
    @commands.has_role("Tournament Organizer")
    async def show(self, context: Context):
        """
        Allows user to report a Thandar Combat League match result.

        :param context: The hybrid command context.
        """
        waitlist = await db_manager.get_waitlist()
        if len(waitlist) == 0:
            embed = discord.Embed(
                description="There are currently no Thandar Combat League users.", color=0x992d22
            )
            await context.send(embed=embed)
            return

        embed = discord.Embed(title="Thandar Combat League Users", color=0x992d22)
        users = []
        for participant in waitlist:
            user = self.bot.get_user(int(participant[0])) or await self.bot.fetch_user(
                int(participant[0])
            )
            users.append(f"• {user.mention}  IGN: {participant[1]} - Signed Up <t:{participant[2]}>")
        embed.description = "\n".join(users)
        await context.send(embed=embed)

    @tcl.command(
        base="tcl",
        name="matches",
        description="Display the weeks' matches for a Thandar Combat League division.",
    )
    @commands.has_role("Tournament Organizer")
    async def matches(self, context: Context):
        """
        Display the weeks' matches for a Thandar Combat League division.

        :param context: The hybrid command context.
        """
        pass

    @tcl.command(
        base="tcl",
        name="start",
        description="Starts the season for a Thandar Combat League division.",
    )
    @commands.has_role("Tournament Organizer")
    async def start(self, context: Context):
        """
        Starts the season for a Thandar Combat League division.

        :param context: The hybrid command context.
        """
        pass

    @tcl.command(
        base="tcl",
        name="end",
        description="Finalizes the season for a Thandar Combat League division.",
    )
    @commands.has_role("Tournament Organizer")
    async def end(self, context: Context):
        """
        Finalizes the season for a Thandar Combat League division.

        :param context: The hybrid command context.
        """
        pass


async def setup(bot):
    await bot.add_cog(Tcl(bot))
