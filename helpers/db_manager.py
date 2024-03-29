import os
import aiosqlite

DATABASE_PATH = f"{os.path.realpath(os.path.dirname(__file__))}/../database/database.db"


async def get_waitlist():
    """
    This function will return the list of all users on waitlist.

    :return: True if the user is on waitlist, False if not.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT user_id, hr_ign, strftime('%s', created_at) FROM waitlist"
        ) as cursor:
            result = await cursor.fetchall()
            return result


async def is_signed_up(user_id: int):
    """
    This function will check if a user is signed up.

    :param user_id: The ID of the user that should be checked.
    :return: True if the user is signed up, False if not.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM waitlist WHERE user_id=?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None


async def add_user_to_waitlist(user_id: int, hr_ign: str):
    """
    This function will add a user based on its ID in the waitlist.

    :param user_id: The ID of the user that should be added into the waitlist.
    :param hr_ign: The Hero Realms In Game Name of the user to be added into the waitlist.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO waitlist(user_id, hr_ign) VALUES (?, ?)", (user_id, hr_ign))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM waitlist")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0


async def remove_user_from_waitlist(user_id: int):
    """
    This function will remove a user based on its ID from the waitlist.

    :param user_id: The ID of the user that should be removed from the waitlist.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM waitlist WHERE user_id=?", (user_id,))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM waitlist")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0


async def add_user_to_participants(user_id: int, hr_ign: str):
    """
    This function will add a user based on its ID to the participants list.

    :param user_id: The ID of the user that should be added into the participants list.
    :param hr_ign: The Hero Realms In Game Name of the user to be added into the participants list.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT * FROM tcl_participants WHERE user_id = ?", (user_id,))
        data = await cursor.fetchone()
        if data is None:
            await db.execute("INSERT INTO tcl_participants(user_id, hr_ign) VALUES (?, ?)", (user_id, hr_ign))
            await db.commit()


async def clear_waitlist():
    """
    This function will remove all users from the waitlist.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM waitlist")
        await db.commit()


async def get_user_id_from_db(hr_ign):
    """
    Retrieve the user ID from the SQLite database based on the HR IGN.

    :param hr_ign: The HR IGN for which to retrieve the user ID.
    :return: The user ID if found, None otherwise.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT user_id FROM tcl_participants WHERE hr_ign=?", (hr_ign,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else None
