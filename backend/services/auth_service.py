"""
auth_service.py - Authentication service for the Lecturer Consultation Service.

This module provides the AuthService class which handles user authentication
against a hardcoded credential store and role-based feature resolution. It also
provides a seed_users() function that inserts the hardcoded credentials into the
database on first initialization.
"""

from typing import Optional

from backend.database import get_connection
from backend.repositories import user_repo
from backend.models import User, Role


# Hardcoded credential store used for authentication and database seeding.
CREDENTIALS = [
    {"username": "lecturer1", "password": "pass123", "full_name": "Dr. Ahmad", "role": "lecturer"},
    {"username": "lecturer2", "password": "pass123", "full_name": "Dr. Siti", "role": "lecturer"},
    {"username": "student1", "password": "pass123", "full_name": "Ali bin Abu", "role": "student"},
    {"username": "student2", "password": "pass123", "full_name": "Nurul Ain", "role": "student"},
    {"username": "student3", "password": "pass123", "full_name": "Raj Kumar", "role": "student"},
]

# Feature lists mapped to each role, defining what actions are accessible.
ROLE_FEATURES = {
    Role.STUDENT: [
        "browse_lecturers",
        "view_availability",
        "book_consultation",
        "respond_edit_proposals",
    ],
    Role.LECTURER: [
        "set_availability",
        "view_bookings",
        "manage_bookings",
        "propose_edits",
    ],
}


class AuthService:
    """
    Handles user authentication against hardcoded credentials and provides
    role-based feature resolution.

    The service validates login attempts by looking up the username in the
    database (seeded from the hardcoded store) and comparing the password.
    It also exposes which features are available for each role.
    """

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Validates user credentials against the database.

        Looks up the user by username using the user repository. If a matching
        user is found and the password matches, returns the User object.
        Otherwise returns None to indicate authentication failure.

        Parameters:
            username: The login username provided by the user.
            password: The password provided by the user.

        Returns:
            User object if credentials are valid, None if authentication fails.
        """
        user = user_repo.find_by_username(username)
        if user is None:
            return None
        if user.password == password:
            return user
        return None

    def get_role_features(self, role: Role) -> list[str]:
        """
        Returns the list of accessible features for a given role.

        Each role has a predefined set of features that determines what
        actions and views are available to the user in the UI.

        Student features: browse_lecturers, view_availability,
                          book_consultation, respond_edit_proposals
        Lecturer features: set_availability, view_bookings,
                           manage_bookings, propose_edits

        Parameters:
            role: The Role enum value (Role.STUDENT or Role.LECTURER).

        Returns:
            A list of feature name strings accessible to the given role.
        """
        return ROLE_FEATURES.get(role, [])


def seed_users():
    """
    Seeds the hardcoded users into the database if they do not already exist.

    Iterates through the CREDENTIALS list and inserts each user into the
    users table only if no user with that username is already present.
    This ensures the database is populated on first initialization without
    creating duplicates on subsequent runs.

    Parameters:
        None

    Returns:
        None
    """
    with get_connection() as conn:
        for cred in CREDENTIALS:
            # Check if user already exists to avoid duplicate insertion
            cursor = conn.execute(
                "SELECT id FROM users WHERE username = ?", (cred["username"],)
            )
            if cursor.fetchone() is None:
                conn.execute(
                    "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                    (cred["username"], cred["password"], cred["full_name"], cred["role"]),
                )
