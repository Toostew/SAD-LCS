"""
database.py - SQLite connection management and schema initialization for the
Lecturer Consultation Service.

This module provides:
- init_db(): Creates all required tables and indexes if they do not exist.
- get_connection(): A context manager that yields a safe SQLite connection
  with foreign key enforcement enabled.

The database file (consultation_service.db) is created at runtime in the
project root directory.
"""

import sqlite3
import os
from contextlib import contextmanager


# Path to the SQLite database file, located in the project root.
DATABASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "consultation_service.db"
)


@contextmanager
def get_connection():
    """
    Context manager that provides a safe SQLite database connection.

    Opens a connection to the SQLite database, enables foreign key enforcement,
    and ensures the connection is properly closed when the context exits.
    Commits the transaction on successful exit; rolls back on exception.

    Parameters:
        None

    Yields:
        sqlite3.Connection: An active SQLite connection with foreign keys enabled
                            and row_factory set to sqlite3.Row for dict-like access.

    Usage:
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM users")
            rows = cursor.fetchall()
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """
    Initializes the database schema by creating all required tables and indexes.

    Creates the following tables if they do not already exist:
    - users: Stores student and lecturer accounts with role enforcement.
    - time_slots: Stores lecturer availability as fixed 1-hour periods.
    - bookings: Stores consultation booking requests with status tracking.
    - edit_proposals: Stores lecturer-proposed changes to bookings.

    Also creates performance indexes on the bookings table for common queries.

    Parameters:
        None

    Returns:
        None
    """
    with get_connection() as conn:
        # Create users table for authentication and role management
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('student', 'lecturer'))
            )
        """)

        # Create time_slots table for lecturer availability
        conn.execute("""
            CREATE TABLE IF NOT EXISTS time_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lecturer_id INTEGER NOT NULL,
                slot_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                FOREIGN KEY (lecturer_id) REFERENCES users(id)
            )
        """)

        # Create bookings table for consultation requests
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_slot_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                lecturer_id INTEGER NOT NULL,
                place TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK(status IN ('pending', 'accepted', 'declined', 'invalidated')),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (time_slot_id) REFERENCES time_slots(id),
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (lecturer_id) REFERENCES users(id)
            )
        """)

        # Create edit_proposals table for lecturer-proposed booking modifications
        conn.execute("""
            CREATE TABLE IF NOT EXISTS edit_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                proposed_time_slot_id INTEGER,
                proposed_place TEXT,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK(status IN ('pending', 'accepted', 'declined')),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (booking_id) REFERENCES bookings(id),
                FOREIGN KEY (proposed_time_slot_id) REFERENCES time_slots(id)
            )
        """)

        # Create weekly_templates table for recurring availability
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weekly_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lecturer_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 4),
                start_time TEXT NOT NULL,
                FOREIGN KEY (lecturer_id) REFERENCES users(id),
                UNIQUE(lecturer_id, day_of_week, start_time)
            )
        """)

        # Create availability_exceptions table for skipping specific dates
        conn.execute("""
            CREATE TABLE IF NOT EXISTS availability_exceptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lecturer_id INTEGER NOT NULL,
                exception_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                FOREIGN KEY (lecturer_id) REFERENCES users(id),
                UNIQUE(lecturer_id, exception_date, start_time)
            )
        """)

        # Create indexes for common booking queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_bookings_slot_status
                ON bookings(time_slot_id, status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_bookings_lecturer_date_status
                ON bookings(lecturer_id, status)
        """)
