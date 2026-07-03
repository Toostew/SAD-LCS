"""
edit_proposal_repo.py - Repository for edit proposal data access.

This module provides functions that abstract all SQLite queries related to
the edit_proposals table and maps database rows to EditProposal dataclass
instances.
"""

from datetime import datetime
from typing import Optional

from backend.database import get_connection
from backend.models import EditProposal, EditProposalStatus


def _row_to_edit_proposal(row) -> EditProposal:
    """
    Converts a sqlite3.Row object into an EditProposal dataclass instance.

    Maps the 'status' text column to the corresponding EditProposalStatus enum
    value and parses the 'created_at' text column into a datetime object.

    Parameters:
        row: A sqlite3.Row object from a query on the edit_proposals table.

    Returns:
        EditProposal: A fully populated EditProposal dataclass instance.
    """
    return EditProposal(
        id=row["id"],
        booking_id=row["booking_id"],
        proposed_time_slot_id=row["proposed_time_slot_id"],
        proposed_place=row["proposed_place"],
        status=EditProposalStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def create(proposal: EditProposal) -> EditProposal:
    """
    Inserts a new edit proposal into the database.

    Stores the proposed changes (new time slot, new place, or both) for an
    existing booking. The database assigns the id and created_at timestamp.

    Parameters:
        proposal: An EditProposal instance with booking_id, proposed_time_slot_id,
                  proposed_place, and status populated. The id and created_at
                  fields are ignored and assigned by the database.

    Returns:
        EditProposal: The created EditProposal with the database-assigned id
                      and created_at timestamp.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO edit_proposals (booking_id, proposed_time_slot_id, proposed_place, status)
            VALUES (?, ?, ?, ?)
            """,
            (
                proposal.booking_id,
                proposal.proposed_time_slot_id,
                proposal.proposed_place,
                proposal.status.value,
            ),
        )
        proposal_id = cursor.lastrowid

        # Retrieve the full row to get the database-assigned created_at
        result = conn.execute(
            "SELECT * FROM edit_proposals WHERE id = ?", (proposal_id,)
        )
        row = result.fetchone()
        return _row_to_edit_proposal(row)


def find_by_id(proposal_id: int) -> Optional[EditProposal]:
    """
    Finds an edit proposal by its unique ID.

    Queries the edit_proposals table for a matching primary key and returns
    the corresponding EditProposal object, or None if no match is found.

    Parameters:
        proposal_id: The integer primary key of the edit proposal to find.

    Returns:
        EditProposal if a matching record exists, None otherwise.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM edit_proposals WHERE id = ?", (proposal_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_edit_proposal(row)


def update(proposal: EditProposal) -> None:
    """
    Updates an existing edit proposal's status and proposed changes.

    Uses the proposal's id to locate the record and updates the status,
    proposed_time_slot_id, and proposed_place fields.

    Parameters:
        proposal: An EditProposal instance with the id of the record to update
                  and the new values for status, proposed_time_slot_id, and
                  proposed_place.

    Returns:
        None
    """
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE edit_proposals
            SET status = ?, proposed_time_slot_id = ?, proposed_place = ?
            WHERE id = ?
            """,
            (
                proposal.status.value,
                proposal.proposed_time_slot_id,
                proposal.proposed_place,
                proposal.id,
            ),
        )


def find_pending_by_student(student_id: int) -> list[EditProposal]:
    """
    Retrieves all pending edit proposals for bookings belonging to a student.

    Joins the edit_proposals table with the bookings table to find proposals
    where the booking's student_id matches the given student and the proposal
    status is 'pending'. This allows the student to see all proposals awaiting
    their response.

    Parameters:
        student_id: The ID of the student whose pending proposals to retrieve.

    Returns:
        list[EditProposal]: All pending edit proposals for the student's bookings,
                            or an empty list if none exist.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT ep.*
            FROM edit_proposals ep
            JOIN bookings b ON ep.booking_id = b.id
            WHERE b.student_id = ? AND ep.status = ?
            """,
            (student_id, EditProposalStatus.PENDING.value),
        )
        rows = cursor.fetchall()
        return [_row_to_edit_proposal(row) for row in rows]
