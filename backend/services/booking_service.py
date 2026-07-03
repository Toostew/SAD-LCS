"""
booking_service.py - Core booking business logic.

This module implements the BookingService class which handles all booking
operations including creation, queue management, accept/decline workflows,
conflict detection, daily limit enforcement, and slot status derivation.
"""

from datetime import date

from backend.models import Booking, BookingStatus, SlotUnavailableError, TimeSlot
from backend.repositories.booking_repo import BookingRepository
from backend.repositories.timeslot_repo import TimeSlotRepository


class BookingService:
    """
    Core booking logic: creation, queue management, accept/decline, slot status.

    Uses constructor injection for its repository dependencies. Enforces
    business rules such as slot conflict prevention, daily booking limits,
    and queue invalidation upon acceptance.
    """

    DAILY_BOOKING_LIMIT = 5

    def __init__(self, booking_repo: BookingRepository, timeslot_repo: TimeSlotRepository):
        """
        Initializes the BookingService with required repository dependencies.

        Parameters:
            booking_repo: Repository for booking data access operations.
            timeslot_repo: Repository for time slot data access operations.
        """
        self.booking_repo = booking_repo
        self.timeslot_repo = timeslot_repo

    # ──────────────────────────────────────────────
    # Task 6.1: Core logic
    # ──────────────────────────────────────────────

    def create_booking(self, student_id: int, time_slot_id: int, lecturer_id: int, place: str) -> Booking:
        """
        Creates a new booking with status=pending.

        Before creation, checks whether the slot already has an accepted booking.
        If the slot is "taken", raises SlotUnavailableError to prevent new bookings.
        Otherwise, creates a pending booking which joins the queue for that slot.

        Parameters:
            student_id: The ID of the student making the booking request.
            time_slot_id: The ID of the time slot being booked.
            lecturer_id: The ID of the lecturer for the consultation.
            place: The proposed consultation location/room.

        Returns:
            The newly created Booking instance with status=PENDING.

        Raises:
            SlotUnavailableError: If the time slot already has an accepted booking.
        """
        if self.get_slot_status(time_slot_id) == "taken":
            raise SlotUnavailableError("This time slot already has an accepted booking")

        new_booking = Booking(
            id=0,  # Will be assigned by the database
            time_slot_id=time_slot_id,
            student_id=student_id,
            lecturer_id=lecturer_id,
            place=place,
            status=BookingStatus.PENDING,
            created_at=None,  # Will be assigned by the database default
        )

        return self.booking_repo.create(new_booking)

    def get_booking_queue(self, lecturer_id: int, time_slot_id: int) -> list:
        """
        Returns all pending bookings for a given lecturer and time slot,
        ordered by submission time (FIFO).

        This is used by the lecturer's queue management view to display
        pending requests in the order they were received.

        Parameters:
            lecturer_id: The ID of the lecturer whose queue to retrieve.
            time_slot_id: The ID of the time slot to get the queue for.

        Returns:
            A list of Booking instances with status=PENDING, ordered by
            created_at ascending (oldest first).
        """
        return self.booking_repo.find_by_slot_and_status(
            time_slot_id=time_slot_id,
            lecturer_id=lecturer_id,
            status=BookingStatus.PENDING,
        )

    def decline_booking(self, booking_id: int) -> Booking:
        """
        Sets a booking's status to declined.

        This is a simple status transition — the booking is marked as declined
        by the lecturer without affecting other bookings in the queue.

        Parameters:
            booking_id: The ID of the booking to decline.

        Returns:
            The updated Booking instance with status=DECLINED.
        """
        booking = self.booking_repo.find_by_id(booking_id)
        booking.status = BookingStatus.DECLINED
        return self.booking_repo.update(booking)

    # ──────────────────────────────────────────────
    # Task 6.2: Slot status derivation
    # ──────────────────────────────────────────────

    def get_slot_status(self, time_slot_id: int) -> str:
        """
        Derives the display status for a time slot based on its bookings.

        The status is computed by checking the booking records:
          - If any booking for this slot has status=ACCEPTED → "taken"
          - Else if any booking has status=PENDING → "queued"
          - Otherwise → "available"

        Parameters:
            time_slot_id: The ID of the time slot to check.

        Returns:
            A string: "available", "queued", or "taken".
        """
        accepted_count = self.booking_repo.count_by_slot_and_status(
            time_slot_id, BookingStatus.ACCEPTED
        )
        if accepted_count > 0:
            return "taken"

        pending_count = self.booking_repo.count_by_slot_and_status(
            time_slot_id, BookingStatus.PENDING
        )
        if pending_count > 0:
            return "queued"

        return "available"

    def get_pending_count(self, time_slot_id: int) -> int:
        """
        Returns the number of pending bookings for a time slot.

        This count is displayed to students as the queue size indicator,
        showing how many other students are waiting for the same slot.

        Parameters:
            time_slot_id: The ID of the time slot to count pending bookings for.

        Returns:
            An integer count of bookings with status=PENDING for this slot.
        """
        return self.booking_repo.count_by_slot_and_status(
            time_slot_id, BookingStatus.PENDING
        )

    # ──────────────────────────────────────────────
    # Task 6.3: Accept logic
    # ──────────────────────────────────────────────

    def accept_booking(self, booking_id: int) -> tuple:
        """
        Attempts to accept a booking with conflict detection and daily limit enforcement.

        Algorithm:
            1. Retrieve the booking and its associated time slot.
            2. Check if another booking is already accepted for the same time slot
               → If yes: return (False, "conflict: ...").
            3. Check if the lecturer has reached the daily limit (5) for the slot's date
               → If yes: return (False, "daily_limit_reached: ...").
            4. Set this booking's status to ACCEPTED.
            5. Invalidate all other PENDING bookings in the same queue.
            6. Return (True, "accepted").

        Parameters:
            booking_id: The ID of the booking to accept.

        Returns:
            A tuple (success: bool, message: str) indicating the outcome.
        """
        booking = self.booking_repo.find_by_id(booking_id)
        time_slot = self.timeslot_repo.find_by_id(booking.time_slot_id)

        # Step 2: Conflict check — is another booking already accepted for this slot?
        if self.has_conflict(booking.lecturer_id, booking.time_slot_id):
            return (False, "conflict: another booking already accepted for this time slot")

        # Step 3: Daily limit check — has the lecturer reached 5 accepted for this date?
        if not self.can_accept_on_date(booking.lecturer_id, time_slot.date):
            return (False, "daily_limit_reached: maximum 5 accepted bookings per day")

        # Step 4: Accept the booking
        booking.status = BookingStatus.ACCEPTED
        self.booking_repo.update(booking)

        # Step 5: Invalidate all other pending bookings in the same queue
        queue = self.booking_repo.find_by_slot_and_status(
            time_slot_id=booking.time_slot_id,
            lecturer_id=booking.lecturer_id,
            status=BookingStatus.PENDING,
        )
        for queued_booking in queue:
            queued_booking.status = BookingStatus.INVALIDATED
            self.booking_repo.update(queued_booking)

        return (True, "accepted")

    def has_conflict(self, lecturer_id: int, time_slot_id: int) -> bool:
        """
        Checks whether the lecturer already has an accepted booking for the given time slot.

        This prevents accepting multiple bookings for the same slot, ensuring
        a one-to-one relationship between a time slot and its accepted booking.

        Parameters:
            lecturer_id: The ID of the lecturer to check.
            time_slot_id: The ID of the time slot to check for conflicts.

        Returns:
            True if an accepted booking already exists for this slot, False otherwise.
        """
        accepted_count = self.booking_repo.count_by_slot_and_status(
            time_slot_id, BookingStatus.ACCEPTED
        )
        return accepted_count > 0

    def can_accept_on_date(self, lecturer_id: int, target_date: date) -> bool:
        """
        Checks whether the lecturer can accept another booking on the given date.

        Enforces the daily booking limit by comparing the current count of
        accepted bookings for the date against DAILY_BOOKING_LIMIT (5).

        Parameters:
            lecturer_id: The ID of the lecturer to check.
            target_date: The calendar date to check the limit for.

        Returns:
            True if the lecturer has fewer than 5 accepted bookings on that date,
            False if at or above the limit.
        """
        count = self.get_daily_accepted_count(lecturer_id, target_date)
        return count < self.DAILY_BOOKING_LIMIT

    def get_daily_accepted_count(self, lecturer_id: int, target_date: date) -> int:
        """
        Returns the number of accepted bookings for a lecturer on a specific date.

        Delegates to the booking repository which joins with the time_slots table
        to match bookings by the slot's calendar date.

        Parameters:
            lecturer_id: The ID of the lecturer to count for.
            target_date: The calendar date to count accepted bookings on.

        Returns:
            An integer count of accepted bookings for the lecturer on that date.
        """
        return self.booking_repo.count_accepted_on_date(lecturer_id, target_date)
