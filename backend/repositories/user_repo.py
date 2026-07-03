"""
user_repo.py - Repository for user data access.

This module provides the UserRepository class which abstracts all SQLite
queries related to the users table and maps database rows to User dataclass
instances.
"""

from typing import Optional

from backend.database import get_connection
from backend.models import User, Role


def _row_to_user(row) -> User:
    """
    Converts a sqlite3.Row object into a User dataclass instance.

    Maps the 'role' text column to the corresponding Role enum value.

    Parameters:
        row: A sqlite3.Row object from a query on the users table.

    Returns:
        User: A fully populated User dataclass instance.
    """
    return User(
        id=row["id"],
        username=row["username"],
        password=row["password"],
        full_name=row["full_name"],
        role=Role(row["role"]),
    )


def find_by_username(username: str) -> Optional[User]:
    """
    Finds a user by their username.

    Queries the users table for an exact username match and returns the
    corresponding User object, or None if no match is found.

    Parameters:
        username: The login username to search for.

    Returns:
        User if a matching record exists, None otherwise.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_user(row)


def find_by_id(user_id: int) -> Optional[User]:
    """
    Finds a user by their unique ID.

    Queries the users table for a matching primary key and returns the
    corresponding User object, or None if no match is found.

    Parameters:
        user_id: The integer primary key of the user to find.

    Returns:
        User if a matching record exists, None otherwise.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_user(row)


def find_all_lecturers() -> list[User]:
    """
    Retrieves all users with the 'lecturer' role.

    Returns a list of User objects representing every lecturer in the system.
    Returns an empty list if no lecturers exist.

    Parameters:
        None

    Returns:
        list[User]: All lecturer users, or an empty list if none exist.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM users WHERE role = ?", (Role.LECTURER.value,)
        )
        rows = cursor.fetchall()
        return [_row_to_user(row) for row in rows]


def find_all_students() -> list[User]:
    """
    Retrieves all users with the 'student' role.

    Returns a list of User objects representing every student in the system.
    Returns an empty list if no students exist.

    Parameters:
        None

    Returns:
        list[User]: All student users, or an empty list if none exist.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM users WHERE role = ?", (Role.STUDENT.value,)
        )
        rows = cursor.fetchall()
        return [_row_to_user(row) for row in rows]
