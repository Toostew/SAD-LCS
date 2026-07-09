"""
template_repo.py - Repository for weekly template and exception data access.

This module provides the TemplateRepository class which handles all SQLite
operations for the weekly_templates and availability_exceptions tables.
"""

from datetime import date

from backend.database import get_connection
from backend.models import WeeklyTemplate, AvailabilityException


class TemplateRepository:
    """Repository class for weekly template and availability exception CRUD operations."""

    def add_template(self, lecturer_id: int, day_of_week: int, start_time: str) -> WeeklyTemplate:
        """
        Inserts a new weekly template slot, ignoring duplicates.

        Parameters:
            lecturer_id: The lecturer's user ID.
            day_of_week: Day of the week (0=Monday, 4=Friday).
            start_time: Start time in HH:MM format.

        Returns:
            The created or existing WeeklyTemplate instance.
        """
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO weekly_templates (lecturer_id, day_of_week, start_time)
                VALUES (?, ?, ?)
                """,
                (lecturer_id, day_of_week, start_time),
            )
            # Fetch the row (whether just inserted or already existed)
            cursor = conn.execute(
                """
                SELECT * FROM weekly_templates
                WHERE lecturer_id = ? AND day_of_week = ? AND start_time = ?
                """,
                (lecturer_id, day_of_week, start_time),
            )
            row = cursor.fetchone()

        return self._row_to_template(row)

    def remove_template(self, template_id: int) -> bool:
        """
        Deletes a weekly template by its primary key.

        Parameters:
            template_id: The ID of the template to delete.

        Returns:
            True if deleted, False if not found.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM weekly_templates WHERE id = ?", (template_id,)
            )
            return cursor.rowcount > 0

    def get_templates(self, lecturer_id: int) -> list[WeeklyTemplate]:
        """
        Returns all weekly templates for a lecturer, ordered by day and time.

        Parameters:
            lecturer_id: The lecturer's user ID.

        Returns:
            List of WeeklyTemplate instances.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM weekly_templates
                WHERE lecturer_id = ?
                ORDER BY day_of_week ASC, start_time ASC
                """,
                (lecturer_id,),
            )
            rows = cursor.fetchall()

        return [self._row_to_template(row) for row in rows]

    def add_exception(self, lecturer_id: int, exception_date: date, start_time: str) -> AvailabilityException:
        """
        Inserts a new availability exception, ignoring duplicates.

        Parameters:
            lecturer_id: The lecturer's user ID.
            exception_date: The date to skip.
            start_time: The template slot time to skip in HH:MM format.

        Returns:
            The created or existing AvailabilityException instance.
        """
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO availability_exceptions (lecturer_id, exception_date, start_time)
                VALUES (?, ?, ?)
                """,
                (lecturer_id, exception_date.isoformat(), start_time),
            )
            cursor = conn.execute(
                """
                SELECT * FROM availability_exceptions
                WHERE lecturer_id = ? AND exception_date = ? AND start_time = ?
                """,
                (lecturer_id, exception_date.isoformat(), start_time),
            )
            row = cursor.fetchone()

        return self._row_to_exception(row)

    def remove_exception(self, exception_id: int) -> bool:
        """
        Deletes an availability exception by its primary key.

        Parameters:
            exception_id: The ID of the exception to delete.

        Returns:
            True if deleted, False if not found.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM availability_exceptions WHERE id = ?", (exception_id,)
            )
            return cursor.rowcount > 0

    def get_exceptions(self, lecturer_id: int) -> list[AvailabilityException]:
        """
        Returns all exceptions for a lecturer, ordered by date and time.

        Parameters:
            lecturer_id: The lecturer's user ID.

        Returns:
            List of AvailabilityException instances.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM availability_exceptions
                WHERE lecturer_id = ?
                ORDER BY exception_date ASC, start_time ASC
                """,
                (lecturer_id,),
            )
            rows = cursor.fetchall()

        return [self._row_to_exception(row) for row in rows]

    def is_exception(self, lecturer_id: int, check_date: date, start_time: str) -> bool:
        """
        Checks if a specific date+time is marked as an exception.

        Parameters:
            lecturer_id: The lecturer's user ID.
            check_date: The date to check.
            start_time: The time slot to check in HH:MM format.

        Returns:
            True if an exception exists for this date+time, False otherwise.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) as cnt FROM availability_exceptions
                WHERE lecturer_id = ? AND exception_date = ? AND start_time = ?
                """,
                (lecturer_id, check_date.isoformat(), start_time),
            )
            row = cursor.fetchone()

        return row["cnt"] > 0

    def _row_to_template(self, row) -> WeeklyTemplate:
        """Maps a SQLite Row to a WeeklyTemplate instance."""
        return WeeklyTemplate(
            id=row["id"],
            lecturer_id=row["lecturer_id"],
            day_of_week=row["day_of_week"],
            start_time=row["start_time"],
        )

    def _row_to_exception(self, row) -> AvailabilityException:
        """Maps a SQLite Row to an AvailabilityException instance."""
        return AvailabilityException(
            id=row["id"],
            lecturer_id=row["lecturer_id"],
            exception_date=date.fromisoformat(row["exception_date"]),
            start_time=row["start_time"],
        )
