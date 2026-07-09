"""
availability_service.py - Business logic for lecturer availability management.

This module provides the AvailabilityService class which handles creating,
retrieving, and removing time slots for lecturers. It supports a weekly
template system where lecturers define recurring slots by day-of-week + time,
and concrete slots are auto-generated for the next 14 days when students
browse availability.
"""

from datetime import date, datetime, timedelta

from backend.models import BookingStatus, TimeSlot, WeeklyTemplate, AvailabilityException
from backend.repositories.booking_repo import BookingRepository
from backend.repositories.timeslot_repo import TimeSlotRepository
from backend.repositories.template_repo import TemplateRepository


class AvailabilityService:
    """Manages lecturer time slot availability with weekly template support."""

    def __init__(self, timeslot_repo: TimeSlotRepository, booking_repo: BookingRepository,
                 template_repo: TemplateRepository = None):
        """
        Initializes the AvailabilityService with its required repositories.

        Parameters:
            timeslot_repo: Repository for time slot CRUD operations.
            booking_repo: Repository for checking bookings against time slots.
            template_repo: Repository for weekly templates and exceptions.
        """
        self.timeslot_repo = timeslot_repo
        self.booking_repo = booking_repo
        self.template_repo = template_repo if template_repo else TemplateRepository()

    # ─── Weekly Template Methods ────────────────────────────────────────

    def get_weekly_templates(self, lecturer_id: int) -> list[WeeklyTemplate]:
        """
        Returns all weekly templates for a lecturer.

        Parameters:
            lecturer_id: The lecturer's user ID.

        Returns:
            List of WeeklyTemplate instances ordered by day_of_week, start_time.
        """
        return self.template_repo.get_templates(lecturer_id)

    def add_weekly_template(self, lecturer_id: int, day_of_week: int, start_time: str) -> WeeklyTemplate:
        """
        Adds a recurring weekly template slot for a lecturer.

        Parameters:
            lecturer_id: The lecturer's user ID.
            day_of_week: Day of the week (0=Monday, 4=Friday).
            start_time: Start time in HH:MM format.

        Returns:
            The created WeeklyTemplate instance.
        """
        return self.template_repo.add_template(lecturer_id, day_of_week, start_time)

    def remove_weekly_template(self, template_id: int) -> bool:
        """
        Removes a weekly template slot.

        Parameters:
            template_id: The ID of the template to remove.

        Returns:
            True if removed, False if not found.
        """
        return self.template_repo.remove_template(template_id)

    # ─── Exception Methods ──────────────────────────────────────────────

    def get_exceptions(self, lecturer_id: int) -> list[AvailabilityException]:
        """
        Returns all exceptions for a lecturer.

        Parameters:
            lecturer_id: The lecturer's user ID.

        Returns:
            List of AvailabilityException instances.
        """
        return self.template_repo.get_exceptions(lecturer_id)

    def add_exception(self, lecturer_id: int, exception_date: date, start_time: str) -> AvailabilityException:
        """
        Adds an exception (marks a specific date+time as unavailable).

        Parameters:
            lecturer_id: The lecturer's user ID.
            exception_date: The date to skip.
            start_time: The template slot time to skip in HH:MM format.

        Returns:
            The created AvailabilityException instance.
        """
        return self.template_repo.add_exception(lecturer_id, exception_date, start_time)

    def remove_exception(self, exception_id: int) -> bool:
        """
        Removes an availability exception.

        Parameters:
            exception_id: The ID of the exception to remove.

        Returns:
            True if removed, False if not found.
        """
        return self.template_repo.remove_exception(exception_id)

    # ─── Slot Generation ────────────────────────────────────────────────

    def generate_slots_for_student(self, lecturer_id: int) -> list[TimeSlot]:
        """
        Generates concrete time slots for the next 14 days based on the
        lecturer's weekly template, excluding exceptions and past dates.

        For each day in the next 14 days that matches a template day-of-week:
        1. Check if there's an exception for that date+time
        2. Check if a time_slot already exists in the DB for that lecturer+date+time
        3. If not, create it in the time_slots table
        4. Return all valid slots for the next 14 days

        Parameters:
            lecturer_id: The lecturer's user ID.

        Returns:
            A list of TimeSlot objects for the next 14 days.
        """
        templates = self.template_repo.get_templates(lecturer_id)

        if not templates:
            return []

        today = date.today()
        now = datetime.now()
        generated_slots = []

        for day_offset in range(14):
            target_date = today + timedelta(days=day_offset)
            # target_date.weekday() returns 0=Monday, 6=Sunday
            target_weekday = target_date.weekday()

            # Only consider weekdays (0-4) that match a template
            for template in templates:
                if template.day_of_week != target_weekday:
                    continue

                # Check if this date+time is excepted
                if self.template_repo.is_exception(lecturer_id, target_date, template.start_time):
                    continue

                # Parse the template start time
                hour = int(template.start_time.split(":")[0])
                minute = int(template.start_time.split(":")[1])
                slot_start = datetime(target_date.year, target_date.month, target_date.day, hour, minute)

                # Skip slots that are already in the past
                if slot_start <= now:
                    continue

                # Check if this slot already exists in the database
                existing_slot = self._find_existing_slot(lecturer_id, target_date, template.start_time)

                if existing_slot:
                    generated_slots.append(existing_slot)
                else:
                    # Create the slot in the time_slots table
                    new_slot = self.create_time_slot(
                        lecturer_id=lecturer_id,
                        slot_date=target_date,
                        start_time=slot_start,
                    )
                    generated_slots.append(new_slot)

        return generated_slots

    def _find_existing_slot(self, lecturer_id: int, slot_date: date, start_time_str: str):
        """
        Checks if a time slot already exists for this lecturer+date+time.

        Parameters:
            lecturer_id: The lecturer's user ID.
            slot_date: The date to check.
            start_time_str: The start time in HH:MM format.

        Returns:
            The existing TimeSlot if found, None otherwise.
        """
        existing_slots = self.timeslot_repo.find_by_lecturer(lecturer_id)
        for slot in existing_slots:
            if slot.date == slot_date and slot.start_time.strftime("%H:%M") == start_time_str:
                return slot
        return None

    # ─── Existing Methods (unchanged) ──────────────────────────────────

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
            ValueError: If the computed duration is not exactly 1 hour.
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

        Parameters:
            lecturer_id: The ID of the lecturer whose availability to retrieve.

        Returns:
            A list of TimeSlot instances belonging to the lecturer.
        """
        return self.timeslot_repo.find_by_lecturer(lecturer_id)

    def remove_time_slot(self, time_slot_id: int) -> bool:
        """
        Removes a time slot only if it has no pending or accepted bookings.

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

        Parameters:
            start_time: The start datetime of the slot.
            end_time: The end datetime of the slot.

        Returns:
            True if the duration is exactly 1 hour, False otherwise.
        """
        duration = end_time - start_time
        return duration == timedelta(hours=1)
