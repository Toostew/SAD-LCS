"""
timeslot_repo.py - Repository for TimeSlot data access.

This module provides the TimeSlotRepository class which handles all SQLite
operations for the time_slots table, including creating, finding, and deleting
time slot records. It maps database rows to TimeSlot dataclass instances.
"""

from datetime import date, datetime
from typing import Optional

from backend.database import get_connection
from backend.models import TimeSlot


class TimeSlotRepository:
    """Repository class for TimeSlot CRUD operations against the SQLite database."""

    def create(self, time_slot: TimeSlot) -> TimeSlot:
        """
        Inserts a new time slot record into the database.

        Stores the date as an ISO format string (YYYY-MM-DD) and start_time/end_time
        as HH:MM format strings. Returns a new TimeSlot instance with the
        auto-generated database id.

        Parameters:
            time_slot: A TimeSlot instance to persist. The id field is ignored
                       since the database assigns it via AUTOINCREMENT.

        Returns:
            A new TimeSlot instance with the id set to the generated primary key.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO time_slots (lecturer_id, slot_date, start_time, end_time)
                VALUES (?, ?, ?, ?)
                """,
                (
                    time_slot.lecturer_id,
                    time_slot.date.isoformat(),
                    time_slot.start_time.strftime("%H:%M"),
                    time_slot.end_time.strftime("%H:%M"),
                ),
            )
            new_id = cursor.lastrowid

        return TimeSlot(
            id=new_id,
            lecturer_id=time_slot.lecturer_id,
            date=time_slot.date,
            start_time=time_slot.start_time,
            end_time=time_slot.end_time,
        )

    def find_by_id(self, id: int) -> Optional[TimeSlot]:
        """
        Retrieves a single time slot by its primary key.

        Parses the stored date string back into a date object and the stored
        time strings back into datetime objects (using the slot's date for
        the datetime component).

        Parameters:
            id: The integer primary key of the time slot to find.

        Returns:
            A TimeSlot instance if found, or None if no record matches the id.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM time_slots WHERE id = ?", (id,)
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_timeslot(row)

    def find_by_lecturer(self, lecturer_id: int) -> list[TimeSlot]:
        """
        Retrieves all time slots belonging to a specific lecturer, ordered by
        date and start time for chronological display.

        Parameters:
            lecturer_id: The integer id of the lecturer whose slots to retrieve.

        Returns:
            A list of TimeSlot instances ordered by slot_date ASC, start_time ASC.
            Returns an empty list if no slots exist for the lecturer.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM time_slots
                WHERE lecturer_id = ?
                ORDER BY slot_date ASC, start_time ASC
                """,
                (lecturer_id,),
            )
            rows = cursor.fetchall()

        return [self._row_to_timeslot(row) for row in rows]

    def delete(self, id: int) -> bool:
        """
        Deletes a time slot record by its primary key.

        Parameters:
            id: The integer primary key of the time slot to delete.

        Returns:
            True if a record was deleted (rowcount == 1), False if no record
            was found with the given id.
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM time_slots WHERE id = ?", (id,)
            )
            return cursor.rowcount > 0

    def _row_to_timeslot(self, row) -> TimeSlot:
        """
        Maps a SQLite Row object to a TimeSlot dataclass instance.

        Parses the stored ISO date string into a date object and the stored
        HH:MM time strings into datetime objects combined with the slot's date.

        Parameters:
            row: A sqlite3.Row object from a query on the time_slots table.

        Returns:
            A fully populated TimeSlot instance.
        """
        slot_date = date.fromisoformat(row["slot_date"])
        start_time = datetime.combine(
            slot_date, datetime.strptime(row["start_time"], "%H:%M").time()
        )
        end_time = datetime.combine(
            slot_date, datetime.strptime(row["end_time"], "%H:%M").time()
        )

        return TimeSlot(
            id=row["id"],
            lecturer_id=row["lecturer_id"],
            date=slot_date,
            start_time=start_time,
            end_time=end_time,
        )
