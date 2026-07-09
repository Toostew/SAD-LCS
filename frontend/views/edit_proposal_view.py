"""
edit_proposal_view.py - Student view for reviewing and responding to edit proposals.

This module provides the edit proposal response view for students. It displays
all pending edit proposals from lecturers, showing the original booking details
alongside the proposed changes in a side-by-side layout. Students can accept
or decline each proposal.
"""

import flet as ft

from frontend.components.notification_bar import show_notification


def edit_proposal_view(page, user, edit_proposal_service, booking_repo, timeslot_repo, booking_service=None, availability_service=None):
    """
    Builds and returns the edit proposal response view for students.

    Fetches all pending edit proposals for the authenticated student and renders
    them as cards showing original booking details vs proposed changes. Each card
    has Accept, Accept & Edit Place, and Decline buttons.

    Parameters:
        page: The Flet Page object for rendering and updating the UI.
        user: The authenticated User object (student) whose proposals to display.
        edit_proposal_service: The EditProposalService instance for accepting/declining proposals.
        booking_repo: The BookingRepository instance for fetching original booking details.
        timeslot_repo: The TimeSlotRepository instance for fetching time slot details.
        booking_service: Optional BookingService instance for editing bookings after acceptance.

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

        def on_counter_propose(e, prop=proposal, bk=booking):
            """
            Opens a dialog for the student to counter-propose changes.

            Allows the student to pick a different time slot from the lecturer's
            available slots and/or modify the place before accepting.

            Parameters:
                e: The Flet click event object.
                prop: The EditProposal instance.
                bk: The original Booking instance.
            """
            # Get available slots for this lecturer
            available_slots = []
            if availability_service:
                all_slots = availability_service.generate_slots_for_student(bk.lecturer_id)
                for s in all_slots:
                    slot_status = booking_service.get_slot_status(s.id) if booking_service else "available"
                    if slot_status != "taken" or s.id == bk.time_slot_id:
                        available_slots.append(s)

            # Build time slot dropdown options
            slot_options = []
            proposed_slot_id = prop.proposed_time_slot_id if prop.proposed_time_slot_id else bk.time_slot_id
            for s in available_slots:
                label = f"{s.date.strftime('%Y-%m-%d')} | {s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
                if s.id == bk.time_slot_id:
                    label += " (original)"
                elif prop.proposed_time_slot_id and s.id == prop.proposed_time_slot_id:
                    label += " (proposed)"
                slot_options.append(ft.dropdown.Option(key=str(s.id), text=label))

            time_slot_dropdown = ft.Dropdown(
                label="Time Slot",
                width=350,
                value=str(proposed_slot_id),
                options=slot_options,
            ) if slot_options else None

            counter_place_field = ft.TextField(
                label="Consultation Place",
                value=prop.proposed_place if prop.proposed_place else bk.place,
                hint_text="e.g. Room 301, Library, Online",
                width=350,
            )

            def on_submit_counter(e):
                new_place = counter_place_field.value.strip() if counter_place_field.value else ""
                if not new_place:
                    show_notification(page, "Place cannot be empty.", type="warning")
                    return

                # Accept the proposal first (applies the lecturer's changes)
                edit_proposal_service.accept_proposal(prop.id)

                # Then override with the student's preferences
                updated_booking = booking_repo.find_by_id(bk.id)
                if time_slot_dropdown and time_slot_dropdown.value:
                    updated_booking.time_slot_id = int(time_slot_dropdown.value)
                updated_booking.place = new_place
                booking_repo.update(updated_booking)

                page.pop_dialog()
                show_notification(page, "Proposal accepted with your changes.", type="success")
                load_proposals()

            def on_cancel_counter(e):
                page.pop_dialog()

            # Build dialog content
            content_controls = [
                ft.Text("Accept the proposal but make your own adjustments:"),
            ]
            if time_slot_dropdown:
                content_controls.append(time_slot_dropdown)
            else:
                content_controls.append(
                    ft.Text("No other time slots available.", italic=True, color=ft.Colors.GREY_600)
                )
            content_controls.append(ft.Divider(height=1))
            content_controls.append(counter_place_field)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Accept & Edit"),
                content=ft.Column(
                    controls=content_controls,
                    tight=True,
                    spacing=10,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=on_cancel_counter),
                    ft.ElevatedButton("Accept with Changes", on_click=on_submit_counter),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.show_dialog(dialog)

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
                ft.TextButton(
                    "Accept & Edit Place",
                    icon=ft.Icons.EDIT,
                    on_click=on_counter_propose,
                ),
                ft.OutlinedButton(
                    "Decline",
                    icon=ft.Icons.CLOSE,
                    on_click=on_decline,
                ),
            ],
            spacing=10,
            wrap=True,
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
