"""
Data models for the Lecturer Consultation Service.

This module defines all core data structures used throughout the application,
including user roles, booking statuses, and the main entities: User, TimeSlot,
Booking, and EditProposal.
"""

from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
from typing import Optional


class Role(Enum):
    """Represents the two user roles in the system."""

    STUDENT = "student"
    LECTURER = "lecturer"


class BookingStatus(Enum):
    """
    Represents the lifecycle states of a booking.

    - PENDING: Initial state when a student submits a booking request.
    - ACCEPTED: The lecturer has accepted this booking.
    - DECLINED: The lecturer has explicitly declined this booking.
    - INVALIDATED: Automatically set when another booking for the same
      time slot is accepted, invalidating all other pending bookings.
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    INVALIDATED = "invalidated"


class EditProposalStatus(Enum):
    """
    Represents the lifecycle states of an edit proposal.

    - PENDING: The proposal has been submitted and awaits the student's response.
    - ACCEPTED: The student accepted the proposed changes.
    - DECLINED: The student declined the proposed changes.
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


@dataclass
class User:
    """
    Represents a system user (either a student or a lecturer).

    Attributes:
        id: Unique identifier for the user.
        username: Login username for authentication.
        password: User's password (stored as plain text for this prototype).
        full_name: Display name of the user.
        role: The user's role, either STUDENT or LECTURER.
    """

    id: int
    username: str
    password: str
    full_name: str
    role: Role


@dataclass
class TimeSlot:
    """
    Represents a fixed 1-hour consultation availability period set by a lecturer.

    Each time slot is exactly 1 hour long (end_time = start_time + 1 hour).

    Attributes:
        id: Unique identifier for the time slot.
        lecturer_id: ID of the lecturer who owns this availability slot.
        date: The calendar date of the time slot.
        start_time: The start datetime of the consultation slot.
        end_time: The end datetime of the consultation slot (always start_time + 1 hour).
    """

    id: int
    lecturer_id: int
    date: date
    start_time: datetime
    end_time: datetime  # Always start_time + 1 hour


@dataclass
class Booking:
    """
    Represents a student's consultation booking request.

    Multiple students can submit bookings for the same time slot, forming
    a booking queue. The lecturer then accepts one and the rest are invalidated.

    Attributes:
        id: Unique identifier for the booking.
        time_slot_id: ID of the time slot being booked.
        student_id: ID of the student making the booking request.
        lecturer_id: ID of the lecturer being consulted.
        place: The proposed consultation location/room.
        status: Current booking status (pending, accepted, declined, invalidated).
        created_at: Timestamp of when the booking was submitted (used for queue ordering).
    """

    id: int
    time_slot_id: int
    student_id: int
    lecturer_id: int
    place: str
    status: BookingStatus
    created_at: datetime  # Submission order for queue


@dataclass
class EditProposal:
    """
    Represents a lecturer's proposed modification to an existing booking.

    A lecturer can propose a new time slot, a new place, or both. The student
    must accept or decline the proposal before changes take effect.

    Attributes:
        id: Unique identifier for the edit proposal.
        booking_id: ID of the booking being modified.
        proposed_time_slot_id: ID of the new proposed time slot (None if unchanged).
        proposed_place: The new proposed consultation location (None if unchanged).
        status: Current proposal status (pending, accepted, declined).
        created_at: Timestamp of when the proposal was created.
    """

    id: int
    booking_id: int
    proposed_time_slot_id: Optional[int]
    proposed_place: Optional[str]
    status: EditProposalStatus
    created_at: datetime


@dataclass
class WeeklyTemplate:
    """
    Represents a recurring weekly availability slot for a lecturer.

    Attributes:
        id: Unique identifier for the template entry.
        lecturer_id: ID of the lecturer who owns this template.
        day_of_week: Day of the week (0=Monday, 4=Friday).
        start_time: The start time in HH:MM format.
    """

    id: int
    lecturer_id: int
    day_of_week: int  # 0=Monday, 4=Friday
    start_time: str   # HH:MM format


@dataclass
class AvailabilityException:
    """
    Represents a specific date+time that a lecturer marks as unavailable,
    overriding their weekly template for that occurrence.

    Attributes:
        id: Unique identifier for the exception entry.
        lecturer_id: ID of the lecturer who owns this exception.
        exception_date: The specific date to skip (YYYY-MM-DD as a date object).
        start_time: The template slot time to skip in HH:MM format.
    """

    id: int
    lecturer_id: int
    exception_date: date
    start_time: str  # HH:MM format


class SlotUnavailableError(Exception):
    """Raised when a student attempts to book a time slot that already has an accepted booking."""

    pass
