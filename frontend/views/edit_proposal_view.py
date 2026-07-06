"""
edit_proposal_view.py - Student view for reviewing and responding to edit proposals.

This module provides the edit proposal response view for students. It displays
all pending edit proposals from lecturers, showing the original booking details
alongside the proposed changes in a side-by-side layout. Students can accept
or decline each proposal.
"""

import flet as ft

from frontend.components.notification_bar import show_notification


def edit_proposal_view(page, user, edit_proposal_service, booking_repo, timeslot_repo):
    """
    Builds and returns the edit proposal response view for students.

    Fetches all pending edit proposals for the authenticated student and renders
    them as cards showing original booking details vs proposed changes. Each card
    has Accept and Decline buttons that invoke the EditProposalService accordingly.

    Parameters:
        page: The Flet Page object for rendering and updating the UI.
        user: The authenticated User object (student) whose proposals to display.
        edit_proposal_service: The EditProposalService instance for accepting/declining proposals.
        booking_repo: The BookingRepository instance for fetching original booking details.
        timeslot_repo: The TimeSlotRepository instance for fetching time slot details.

    Returns:
        ft.Column: A Flet Column control containing the full edit proposal view.
    """
    # Container that holds the list of proposal cards, refreshed on actions
    proposals_container = ft.Column(spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

    def load_proposals():
        """
        Fetches pending proposals for the student and rebuilds the proposals list.

        Clears the current proposals container and re-populates it with cards
        for each pending proposal showing original vs proposed details. Displays
        a 'no pending proposals' message if the list is empty.

        Returns:
            None
        """
        proposals_container.controls.clear()

        pending_proposals = edit_proposal_service.get_pending_proposals_for_student(user.id)

        if not pending_proposals:
            proposals_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No pending edit proposals.",
                        size=16,
                        color=ft.Colors.GREY_600,
                        italic=True,
                    ),
                    padding=30,
                    alignment=ft.Alignment.CENTER,
                )
            )
            page.update()
            return

        for proposal in pending_proposals:
            card = _build_proposal_card(proposal)
            proposals_container.controls.append(card)

        page.update()

    def _build_proposal_card(proposal):
        """
        Builds a visual card for a single edit proposal showing original and proposed details.

        Retrieves the original booking and time slot, as well as the proposed time slot
        (if changed), and renders them side by side with Accept and Decline buttons.

        Parameters:
            proposal: An EditProposal instance to render.

        Returns:
            ft.Card: A Flet Card control displaying the proposal comparison and action buttons.
        """
        # Fetch the original booking details
        booking = booking_repo.find_by_id(proposal.booking_id)

        # Fetch the original time slot
        original_slot = timeslot_repo.find_by_id(booking.time_slot_id)

        # Format original details
        original_date = original_slot.date.strftime("%Y-%m-%d") if original_slot else "Unknown"
        original_time = (
            f"{original_slot.start_time.strftime('%H:%M')} - {original_slot.end_time.strftime('%H:%M')}"
            if original_slot
            else "Unknown"
        )
        original_place = booking.place

        # Determine proposed details
        if proposal.proposed_time_slot_id is not None:
            proposed_slot = timeslot_repo.find_by_id(proposal.proposed_time_slot_id)
            proposed_date = proposed_slot.date.strftime("%Y-%m-%d") if proposed_slot else "Unknown"
            proposed_time = (
                f"{proposed_slot.start_time.strftime('%H:%M')} - {proposed_slot.end_time.strftime('%H:%M')}"
                if proposed_slot
                else "Unknown"
            )
        else:
            proposed_date = original_date
            proposed_time = original_time

        proposed_place = proposal.proposed_place if proposal.proposed_place else original_place

        # Build the original details column
        original_column = ft.Column(
            controls=[
                ft.Text("Original Booking", weight=ft.FontWeight.BOLD, size=14),
                ft.Text(f"Date: {original_date}", size=13),
                ft.Text(f"Time: {original_time}", size=13),
                ft.Text(f"Place: {original_place}", size=13),
            ],
            spacing=5,
            expand=True,
        )

        # Build the proposed changes column
        proposed_column = ft.Column(
            controls=[
                ft.Text("Proposed Changes", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.BLUE),
                ft.Text(
                    f"Date: {proposed_date}",
                    size=13,
                    color=ft.Colors.BLUE if proposal.proposed_time_slot_id else None,
                ),
                ft.Text(
                    f"Time: {proposed_time}",
                    size=13,
                    color=ft.Colors.BLUE if proposal.proposed_time_slot_id else None,
                ),
                ft.Text(
                    f"Place: {proposed_place}",
                    size=13,
                    color=ft.Colors.BLUE if proposal.proposed_place else None,
                ),
            ],
            spacing=5,
            expand=True,
        )

        def on_accept(e, proposal_id=proposal.id):
            """
            Handles the Accept button click for a proposal.

            Calls the edit proposal service to accept the proposal, shows a
            success notification, and refreshes the proposals list.

            Parameters:
                e: The Flet click event object.
                proposal_id: The ID of the proposal being accepted.

            Returns:
                None
            """
            edit_proposal_service.accept_proposal(proposal_id)
            show_notification(page, "Proposal accepted. Booking updated.", type="success")
            load_proposals()

        def on_decline(e, proposal_id=proposal.id):
            """
            Handles the Decline button click for a proposal.

            Calls the edit proposal service to decline the proposal, shows an
            info notification, and refreshes the proposals list.

            Parameters:
                e: The Flet click event object.
                proposal_id: The ID of the proposal being declined.

            Returns:
                None
            """
            edit_proposal_service.decline_proposal(proposal_id)
            show_notification(page, "Proposal declined. Booking unchanged.", type="info")
            load_proposals()

        # Action buttons row
        action_buttons = ft.Row(
            controls=[
                ft.ElevatedButton(
                    "Accept",
                    icon=ft.Icons.CHECK,
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.GREEN,
                    on_click=on_accept,
                ),
                ft.OutlinedButton(
                    "Decline",
                    icon=ft.Icons.CLOSE,
                    on_click=on_decline,
                ),
            ],
            spacing=10,
        )

        # Assemble the card
        card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[original_column, proposed_column],
                            spacing=20,
                        ),
                        ft.Divider(height=1),
                        action_buttons,
                    ],
                    spacing=10,
                ),
                padding=15,
            ),
        )

        return card

    # Build the view header
    header = ft.Text(
        "Edit Proposals",
        size=22,
        weight=ft.FontWeight.BOLD,
    )

    # Assemble the full view layout
    view = ft.Column(
        controls=[
            header,
            ft.Divider(height=1),
            proposals_container,
        ],
        spacing=15,
        expand=True,
    )

    # Initial load of proposals
    load_proposals()

    return view
