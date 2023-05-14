from discord.ext import commands
from discord.ext.commands import Context
import random
import discord


from helpers import checks

# Dictionary for gambit roll effects
roll_effect = [
    '1: "No Heroes"',
    '2: "Double Health"',
    '3: "Each Player May Ban 1 Class"',
    '4: "No Clerics"',
    '5: "No Fighters"',
    '6: "No Rangers"',
    '7: "No Thieves"',
    '8: "No Wizards"',
    '9: "Cleric Mirror"',
    '10: "Fighter Mirror"',
    '11: "Ranger Mirror"',
    '12: "Thief Mirror"',
    '13: "Wizard Mirror"',
    '14: "Level 3 Match"',
    '15: "Level 7 Match"',
    '16: "Level 9 Match"',
    '17: "Blind Challenge"',
    '18: "Level 5 Match"',
    '19: "Level 11 Match"',
    '20: "No Gambit"',
]

# List of gambits
gambits = '1: No Heroes\n2: Double Health\n3: Each Player May Ban 1 Class\n4: No Clerics\n' \
              '5: No Fighters\n6: No Rangers\n7: No Thieves\n8: No Wizards\n9: Cleric Mirror\n' \
              '10: Fighter Mirror\n11: Ranger Mirror\n12: Thief Mirror\n13: Wizard Mirror\n' \
              '14: Level 3 Match\n15: Level 7 Match\n16: Level 9 Match\n17: Blind Challenge\n' \
              '18: Level 5 Match\n19: Level 11 Match\n20: No Gambit'


class Gambits(commands.Cog, name="Gambits"):
    def __init__(self, bot):
        self.bot = bot

    # gambit command
    @commands.hybrid_command(
        name="gambit",
        description="Selects a random gambit from the gambit list.",
    )
    async def gambit(self, context: Context):
        """Selects a random gambit from the gambit list."""
        result = random.choice(roll_effect)
        embed = discord.Embed(
            description=f"{result}",
            color=0x1f8b4c,
        )
        embed.set_author(name="Gambit Effect")
        await context.send(embed=embed)

    # gambit list command
    @commands.hybrid_command(
        name="gambitlist",
        description="Prints the gambit list.",
    )
    async def gambitlist(self, context: Context):
        """Displays the entire Gambit Effect List."""
        embed = discord.Embed(
            description=f"{gambits}",
            color=0x1f8b4c,
        )
        embed.set_author(name="Gambit Effect List")
        await context.send(embed=embed)


# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot):
    await bot.add_cog(Gambits(bot))
