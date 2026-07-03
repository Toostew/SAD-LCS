"""
availability_service.py - Business logic for lecturer availability management.

This module provides the AvailabilityService class which handles creating,
retrieving, and removing time slots for lecturers. It enforces the fixed
1-hour duration constraint and prevents deletion of slots that have active
(pending or accepted) bookings.
"""

from datetime import date, datetime, timedelta

from backend.models import BookingStatus, TimeSlot
from backend.repositories.booking_repo import BookingRepository
from backend.repositories.timeslot_repo import TimeSlotRepository


class AvailabilityService:
    """Manages lecturer time slot availability."""

    def __init__(self, timeslot_repo: TimeSlotRepository, booking_repo: BookingRepository):
        """
        Initializes the AvailabilityService with its required repositories.

        Parameters:
            timeslot_repo: Repository for time slot CRUD operations.
            booking_repo: Repository for checking bookings against time slots.
        """
        self.timeslot_repo = timeslot_repo
        self.booking_repo = booking_repo

    def create_time_slot(self, lecturer_id: int, slot_date: date, start_time: datetime) -> TimeSlot:
        """
        Creates a fixed 1-hour time slot for a lecturer.

        Computes end_time as start_time + 1 hour, validates the duration,
        builds a TimeSlot object, and persists it via the repository.

        Parameters:
            lecturer_id: The ID of the lecturer creating the slot.
            slot_date: The calendar date for the time slot.
            start_time: The start datetime of the consultation slot.

        Returns:
            The persisted TimeSlot instance with a database-generated ID.

        Raises:
            ValueError: If the computed duration is not exactly 1 hour
                        (should not occur in normal usage since end_time is
                        always calculated, but acts as a safety check).
        """
        end_time = start_time + timedelta(hours=1)

        if not self.validate_duration(start_time, end_time):
            raise ValueError("Time slot must be exactly 1 hour")

        time_slot = TimeSlot(
            id=0,
            lecturer_id=lecturer_id,
            date=slot_date,
            start_time=start_time,
            end_time=end_time,
        )

        return self.timeslot_repo.create(time_slot)

    def get_lecturer_availability(self, lecturer_id: int) -> list[TimeSlot]:
        """
        Retrieves all time slots for a given lecturer.

        Delegates to the repository which returns slots ordered by date and
        start time for chronological display.

        Parameters:
            lecturer_id: The ID of the lecturer whose availability to retrieve.

        Returns:
            A list of TimeSlot instances belonging to the lecturer, ordered
            by date and start time. Returns an empty list if none exist.
        """
        return self.timeslot_repo.find_by_lecturer(lecturer_id)

    def remove_time_slot(self, time_slot_id: int) -> bool:
        """
        Removes a time slot only if it has no pending or accepted bookings.

        Checks whether any bookings with status PENDING or ACCEPTED reference
        the given time slot. If active bookings exist, deletion is blocked to
        protect scheduled consultations.

        Parameters:
            time_slot_id: The ID of the time slot to remove.

        Returns:
            True if the time slot was successfully deleted.
            False if deletion was blocked due to active bookings.
        """
        pending_count = self.booking_repo.count_by_slot_and_status(
            time_slot_id, BookingStatus.PENDING
        )
        accepted_count = self.booking_repo.count_by_slot_and_status(
            time_slot_id, BookingStatus.ACCEPTED
        )

        if pending_count > 0 or accepted_count > 0:
            return False

        return self.timeslot_repo.delete(time_slot_id)

    def validate_duration(self, start_time: datetime, end_time: datetime) -> bool:
        """
        Validates that the time slot duration is exactly 1 hour.

        Computes the difference between end_time and start_time and checks
        that it equals exactly 3600 seconds (1 hour).

        Parameters:
            start_time: The start datetime of the slot.
            end_time: The end datetime of the slot.

        Returns:
            True if the duration is exactly 1 hour, False otherwise.
        """
        duration = end_time - start_time
        return duration == timedelta(hours=1)
