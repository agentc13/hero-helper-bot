# Say Command
@commands.hybrid_command(
    name="say",
    description="The bot will say anything you want.",
)
@app_commands.describe(message="The message that should be repeated by the bot")
@checks.is_owner()
async def say(self, context: Context, *, message: str) -> None:
    """
    The bot will say anything you want.

    :param context: The hybrid command context.
    :param message: The message that should be repeated by the bot.
    """
    await context.send(message)


# Embed Command
@commands.hybrid_command(
    name="embed",
    description="The bot will say anything you want, but within embeds.",
)
@app_commands.describe(message="The message that should be repeated by the bot")
@checks.is_owner()
async def embed(self, context: Context, *, message: str) -> None:
    """
    The bot will say anything you want, but using embeds.

    :param context: The hybrid command context.
    :param message: The message that should be repeated by the bot.
    """
    embed = discord.Embed(description=message, color=0x9C84EF)
    await context.send(embed=embed)


# Warning Command Group
@commands.hybrid_group(
    name="warning",
    description="Manage warnings of a user on a server.",
)
@commands.has_permissions(manage_messages=True)
async def warning(self, context: Context) -> None:
    """
    Manage warnings of a user on a server.

    :param context: The hybrid command context.
    """
    if context.invoked_subcommand is None:
        embed = discord.Embed(
            description="Please specify a subcommand.\n\n"
                        "**Subcommands:**\n"
                        "`add` - Add a warning to a user.\n"
                        "`remove` - Remove a warning from a user.\n"
                        "`list` - List all warnings of a user.",
            color=0xE02B2B,
        )
        await context.send(embed=embed)

# Warning Add
@warning.command(
    name="add",
    description="Adds a warning to a user in the server.",
)
@commands.has_permissions(manage_messages=True)
@app_commands.describe(
    user="The user that should be warned.",
    reason="The reason why the user should be warned.",
)
async def warning_add(
    self, context: Context, user: discord.User, *, reason: str = "Not specified"
) -> None:
    """
    Warns a user in his private messages.

    :param context: The hybrid command context.
    :param user: The user that should be warned.
    :param reason: The reason for the warn. Default is "Not specified".
    """
    member = context.guild.get_member(user.id) or await context.guild.fetch_member(
        user.id
    )
    total = await db_manager.add_warn(
        user.id, context.guild.id, context.author.id, reason
    )
    embed = discord.Embed(
        description=f"**{member}** was warned by **{context.author}**!\nTotal warns for this user: {total}",
        color=0x9C84EF,
    )
    embed.add_field(name="Reason:", value=reason)
    await context.send(embed=embed)
    try:
        await member.send(
            f"You were warned by **{context.author}** in **{context.guild.name}**!\nReason: {reason}"
        )
    except:
        # Couldn't send a message in the private messages of the user
        await context.send(
            f"{member.mention}, you were warned by **{context.author}**!\nReason: {reason}"
        )

# Warning Remove
@warning.command(
    name="remove",
    description="Removes a warning from a user in the server.",
)
@commands.has_permissions(manage_messages=True)
@app_commands.describe(
    user="The user that should get their warning removed.",
    warn_id="The ID of the warning that should be removed.",
)
async def warning_remove(
    self, context: Context, user: discord.User, warn_id: int
) -> None:
    """
    Warns a user in his private messages.

    :param context: The hybrid command context.
    :param user: The user that should get their warning removed.
    :param warn_id: The ID of the warning that should be removed.
    """
    member = context.guild.get_member(user.id) or await context.guild.fetch_member(
        user.id
    )
    total = await db_manager.remove_warn(warn_id, user.id, context.guild.id)
    embed = discord.Embed(
        description=f"I've removed the warning **#{warn_id}** from **{member}**!\nTotal warns for this user: {total}",
        color=0x9C84EF,
    )
    await context.send(embed=embed)

# Warning List
@warning.command(
    name="list",
    description="Shows the warnings of a user in the server.",
)
@commands.has_guild_permissions(manage_messages=True)
@app_commands.describe(user="The user you want to get the warnings of.")
async def warning_list(self, context: Context, user: discord.User):
    """
    Shows the warnings of a user in the server.

    :param context: The hybrid command context.
    :param user: The user you want to get the warnings of.
    """
    warnings_list = await db_manager.get_warnings(user.id, context.guild.id)
    embed = discord.Embed(title=f"Warnings of {user}", color=0x9C84EF)
    description = ""
    if len(warnings_list) == 0:
        description = "This user has no warnings."
    else:
        for warning in warnings_list:
            description += f"• Warned by <@{warning[2]}>: **{warning[3]}** (<t:{warning[4]}>) - Warn ID #{warning[5]}\n"
    embed.description = description
    await context.send(embed=embed)



async def add_warn(user_id: int, server_id: int, moderator_id: int, reason: str) -> int:
    """
    This function will add a warn to the database.

    :param user_id: The ID of the user that should be warned.
    :param reason: The reason why the user should be warned.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        rows = await db.execute(
            "SELECT id FROM warns WHERE user_id=? AND server_id=? ORDER BY id DESC LIMIT 1",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            warn_id = result[0] + 1 if result is not None else 1
            await db.execute(
                "INSERT INTO warns(id, user_id, server_id, moderator_id, reason) VALUES (?, ?, ?, ?, ?)",
                (
                    warn_id,
                    user_id,
                    server_id,
                    moderator_id,
                    reason,
                ),
            )
            await db.commit()
            return warn_id


async def remove_warn(warn_id: int, user_id: int, server_id: int) -> int:
    """
    This function will remove a warn from the database.

    :param warn_id: The ID of the warn.
    :param user_id: The ID of the user that was warned.
    :param server_id: The ID of the server where the user has been warned
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM warns WHERE id=? AND user_id=? AND server_id=?",
            (
                warn_id,
                user_id,
                server_id,
            ),
        )
        await db.commit()
        rows = await db.execute(
            "SELECT COUNT(*) FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0


async def get_warnings(user_id: int, server_id: int) -> list:
    """
    This function will get all the warnings of a user.

    :param user_id: The ID of the user that should be checked.
    :param server_id: The ID of the server that should be checked.
    :return: A list of all the warnings of the user.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        rows = await db.execute(
            "SELECT user_id, server_id, moderator_id, reason, strftime('%s', created_at), id FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                result_list.append(row)
            return result_list
'''
From schema.sql
CREATE TABLE IF NOT EXISTS `warns` (
  `id` int(11) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `server_id` varchar(20) NOT NULL,
  `moderator_id` varchar(20) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''