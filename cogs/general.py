import platform
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context


class General(commands.Cog, name="General"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="help",
        description="List all commands the bot has loaded."
    )
    async def help(self, context: Context):
        """
        Lists all commands the bot has loaded.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            title="Hero-Helper Bot Help",
            description="**All commands start with /**\n"
                        "Commands in a group will begin with the group prefix, then the specific command.\n\n"
                        "Tutorial videos can be found on [agentc13's YouTube channel](https://www.youtube.com/channel/UCUEuO2cFBlw5kh94ENUR0Ag).",
            colour=discord.Colour.dark_purple(),
        )

        for cog in self.bot.cogs.values():
            data = []

            for command in cog.get_commands():
                if command.hidden:
                    continue

                if isinstance(command, commands.Group):
                    data.append(f"`/{command.name}` - {command.short_doc}")
                    for subcommand in command.commands:
                        if not subcommand.hidden:  # check if the subcommand is hidden
                            data.append(f"`/{command.name} {subcommand.name}` - {subcommand.short_doc}")
                else:
                    data.append(f"`/{command.name}` - {command.short_doc}")

            if data:
                help_text = "\n".join(data)
                embed.add_field(
                    name=cog.qualified_name, value=help_text, inline=False
                )

        await context.send(embed=embed)

    # botinfo command
    @commands.hybrid_command(
        name="botinfo",
        description="Information about the Hero-Helper Discord Bot.",
    )
    async def botinfo(self, context: Context):
        """
        Information about the Hero-Helper Discord Bot.

        :param context: The hybrid command context.
        """
        embed = discord.Embed(
            description="Hero-Helper Discord Bot",
            colour=discord.Colour.dark_purple(),
        )
        embed.set_author(name="Bot Information")
        embed.add_field(name="Owner:", value="agentc13#8194", inline=True)
        embed.add_field(
            name="Python Version:", value=f"{platform.python_version()}", inline=True
        )
        embed.add_field(
            name="Prefix:",
            value=f"/ (Slash Commands) or {self.bot.config['prefix']} for normal commands",
            inline=False,
        )
        embed.set_footer(text=f"Requested by {context.author}")
        await context.send(embed=embed)

    # serverinfo command
    @commands.hybrid_command(
        name="serverinfo",
        description="Information about the discord server.",
    )
    async def serverinfo(self, context: Context):
        """
        Information about the discord server.

        :param context: The hybrid command context.
        """
        roles = [role.name for role in context.guild.roles]
        if len(roles) > 50:
            roles = roles[:50]
            roles.append(f">>>> Displaying[50/{len(roles)}] Roles")
        roles = ", ".join(roles)

        embed = discord.Embed(
            title="**Server Name:**",
            description=f"{context.guild}",
            colour=discord.Colour.dark_purple(),
        )
        if context.guild.icon is not None:
            embed.set_thumbnail(url=context.guild.icon.url)
        embed.add_field(name="Server ID", value=context.guild.id)
        embed.add_field(name="Member Count", value=context.guild.member_count)
        embed.add_field(
            name="Text/Voice Channels", value=f"{len(context.guild.channels)}"
        )
        embed.add_field(name=f"Roles ({len(context.guild.roles)})", value=roles)
        embed.set_footer(text=f"Created at: {context.guild.created_at}")
        await context.send(embed=embed)

    # bot invite command
    # @commands.hybrid_command(
    #     name="invite_link",
    #     description="Get the invite link of the bot to be able to invite it.",
    # )
    # async def invite_link(self, context: Context):
    #     """
    #     Get the invite link of the bot to be able to invite it to a server.
    #
    #     :param context: The hybrid command context.
    #     """
    #     embed = discord.Embed(
    #         description=f"Invite me by clicking [here](https://discordapp.com/oauth2/authorize?&client_id={self.bot.config['application_id']}&scope=bot+applications.commands&permissions={self.bot.config['permissions']}).",
    #         colour = discord.Colour.dark_purple(),
    #     )
    #     try:
    #         await context.author.send(embed=embed)
    #         await context.send("I sent you a private message!")
    #     except discord.Forbidden:
    #         await context.send(embed=embed)

    # purge command - only works if user has permissions to delete posts.
    @commands.hybrid_command(
        name="purge",
        description="Delete a number of messages.",
        hidden=True,
    )
    @commands.has_guild_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The amount of messages that should be deleted.")
    async def purge(self, context: Context, amount: int):
        """
        Delete a number of messages.

        :param context: The hybrid command context.
        :param amount: The number of messages that should be deleted.
        """
        await context.send(
            "Deleting messages..."
        )
        await context.channel.purge(limit=amount + 1)


async def setup(bot):
    await bot.add_cog(General(bot))
