"""
edit_proposal_service.py - Business logic for booking edit proposals.

This module implements the EditProposalService class which handles the full
lifecycle of edit proposals: creation, acceptance (applying changes to bookings),
declining, and querying pending proposals for a student.
"""

from backend.models import EditProposal, EditProposalStatus
from backend.repositories import edit_proposal_repo
from backend.repositories.booking_repo import BookingRepository


class EditProposalService:
    """
    Manages the lifecycle of lecturer-initiated booking edit proposals.

    A lecturer can propose changes (new time slot, new place, or both) to an
    existing accepted booking. The student then accepts or declines the proposal.
    Acceptance applies the changes to the booking; declining leaves it unchanged.

    Uses constructor injection for its repository dependencies.
    """

    def __init__(self, edit_proposal_repo_module, booking_repo: BookingRepository):
        """
        Initializes the EditProposalService with required repository dependencies.

        Parameters:
            edit_proposal_repo_module: The edit_proposal_repo module providing
                functions: create, find_by_id, update, find_pending_by_student.
            booking_repo: A BookingRepository instance for booking data access.
        """
        self.edit_proposal_repo = edit_proposal_repo_module
        self.booking_repo = booking_repo

    def create_proposal(self, booking_id: int, proposed_time_slot_id=None, proposed_place=None) -> EditProposal:
        """
        Creates an edit proposal without modifying the original booking.

        Stores the proposed changes (new time slot, new place, or both) linked
        to an existing booking. At least one of the proposed changes must be
        provided. The original booking remains unchanged until the student
        accepts the proposal.

        Parameters:
            booking_id: The ID of the booking to propose changes for.
            proposed_time_slot_id: The ID of the new proposed time slot, or None
                                   if the time slot should remain unchanged.
            proposed_place: The new proposed consultation location, or None if
                           the place should remain unchanged.

        Returns:
            The newly created EditProposal instance with status=PENDING.

        Raises:
            ValueError: If neither proposed_time_slot_id nor proposed_place is provided.
        """
        if proposed_time_slot_id is None and proposed_place is None:
            raise ValueError(
                "At least one of proposed_time_slot_id or proposed_place must be provided"
            )

        proposal = EditProposal(
            id=0,  # Will be assigned by the database
            booking_id=booking_id,
            proposed_time_slot_id=proposed_time_slot_id,
            proposed_place=proposed_place,
            status=EditProposalStatus.PENDING,
            created_at=None,  # Will be assigned by the database default
        )

        return self.edit_proposal_repo.create(proposal)

    def accept_proposal(self, proposal_id: int):
        """
        Applies proposed changes to the booking and marks the proposal as accepted.

        Retrieves the proposal, updates the associated booking with whatever
        fields were proposed (time_slot_id, place, or both), then sets the
        proposal status to ACCEPTED.

        Parameters:
            proposal_id: The ID of the edit proposal to accept.

        Returns:
            The updated Booking instance with the proposed changes applied.
        """
        # Retrieve the proposal
        proposal = self.edit_proposal_repo.find_by_id(proposal_id)

        # Retrieve the associated booking
        booking = self.booking_repo.find_by_id(proposal.booking_id)

        # Apply proposed changes to the booking
        if proposal.proposed_time_slot_id is not None:
            booking.time_slot_id = proposal.proposed_time_slot_id

        if proposal.proposed_place is not None:
            booking.place = proposal.proposed_place

        # Save the updated booking
        updated_booking = self.booking_repo.update(booking)

        # Mark the proposal as accepted
        proposal.status = EditProposalStatus.ACCEPTED
        self.edit_proposal_repo.update(proposal)

        return updated_booking

    def decline_proposal(self, proposal_id: int) -> EditProposal:
        """
        Marks the proposal as declined without modifying the original booking.

        The booking retains its original time slot and place. Only the proposal
        status is changed to DECLINED.

        Parameters:
            proposal_id: The ID of the edit proposal to decline.

        Returns:
            The updated EditProposal instance with status=DECLINED.
        """
        proposal = self.edit_proposal_repo.find_by_id(proposal_id)
        proposal.status = EditProposalStatus.DECLINED
        self.edit_proposal_repo.update(proposal)
        return proposal

    def get_pending_proposals_for_student(self, student_id: int) -> list:
        """
        Returns all pending edit proposals for bookings belonging to the student.

        Queries for proposals that have status=PENDING and are linked to bookings
        where the student_id matches the given student. This allows the student
        to see all proposals awaiting their response.

        Parameters:
            student_id: The ID of the student whose pending proposals to retrieve.

        Returns:
            A list of EditProposal instances with status=PENDING for the student's
            bookings, or an empty list if none exist.
        """
        return self.edit_proposal_repo.find_pending_by_student(student_id)
