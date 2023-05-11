import json
import os
import discord

from exceptions import *
from functools import wraps


def is_owner():
    """
    This is a custom check to see if the user executing the command is an owner of the bot.
    """

    async def predicate(context: commands.Context):
        with open(
            f"{os.path.realpath(os.path.dirname(__file__))}/../config.json"
        ) as file:
            data = json.load(file)
        if context.author.id not in data["owners"]:
            raise UserNotOwner
        return True

    return commands.check(predicate)


def is_quickfire():
    def decorator(func):
        @wraps(func)
        async def wrapper(context, *args, **kwargs):
            tournament_name = args[0]  # assuming tournament_name is the first argument
            if 'quickfire' not in tournament_name:
                embed = discord.Embed(title='Error!',
                                      description=f'This command only works for Quickfire tournaments.',
                                      color=0xe74c3c)
                await context.send(embed=embed)
                return
            return await func(context, *args, **kwargs)
        return wrapper
    return decorator
d