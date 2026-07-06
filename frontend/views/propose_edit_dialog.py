"""
propose_edit_dialog.py - Dialog for lecturers to propose edits to pending bookings.

This module provides a dialog function that allows lecturers to propose a new
time slot and/or place for a pending booking. It connects to the
EditProposalService to create the proposal and notifies the user of success
or validation errors.
"""

import flet as ft

from frontend.components.notification_bar import show_notification


def show_propose_edit_dialog(page, booking, edit_proposal_service, availability_service, lecturer_id, on_done):
    """
    Opens a dialog for the lecturer to propose a new time slot and/or place for a booking.

    Displays the current booking details (time slot, place) and provides:
    - A Dropdown to optionally select a different time slot from the lecturer's availability
    - A TextField to optionally enter a new place
    At least one field must be changed for submission to succeed.

    On submit, calls edit_proposal_service.create_proposal() and shows a success
    notification. On validation error (neither field filled), shows an error notification.

    Parameters:
        page: The Flet Page object for rendering the dialog and notifications.
        booking: The Booking instance being edited (must have id, place, time_slot_id).
        edit_proposal_service: The EditProposalService instance with create_proposal().
        availability_service: The AvailabilityService instance for fetching lecturer time slots.
        lecturer_id: The ID of the lecturer proposing the edit.
        on_done: Callback function invoked after a successful proposal to refresh the parent view.

    Returns:
        None. The dialog is displayed as a side effect on the page.
    """
    # Fetch all available time slots for this lecturer
    available_slots = availability_service.get_lecturer_availability(lecturer_id)

    # Build dropdown options from lecturer's time slots, excluding the current one
    slot_options = []
    for slot in available_slots:
        if slot.id == booking.time_slot_id:
            continue  # Skip the slot already assigned to this booking
        label = f"{slot.date.strftime('%Y-%m-%d')} | {slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
        slot_options.append(ft.dropdown.Option(key=str(slot.id), text=label))

    # Dropdown for selecting a new time slot (optional)
    time_slot_dropdown = ft.Dropdown(
        label="Proposed Time Slot (optional)",
        hint_text="Select a different time slot",
        options=slot_options,
        width=350,
    )

    # TextField for entering a new place (optional)
    place_field = ft.TextField(
        label="Proposed Place (optional)",
        hint_text="Enter a new consultation location",
        width=350,
    )

    # Display current booking details for reference
    current_info = ft.Column(
        controls=[
            ft.Text("Current Booking Details:", weight=ft.FontWeight.BOLD, size=14),
            ft.Text(f"Place: {booking.place}", size=13),
        ],
        spacing=6,
    )

    def handle_submit(e):
        """
        Handles the submit button click to create the edit proposal.

        Reads the dropdown and text field values, calls create_proposal on the
        service, and either shows a success notification or an error if neither
        field is filled.

        Parameters:
            e: The Flet click event object.

        Returns:
            None
        """
        # Extract selected time slot ID (or None if not selected)
        proposed_time_slot_id = int(time_slot_dropdown.value) if time_slot_dropdown.value else None

        # Extract proposed place (or None if empty)
        proposed_place = place_field.value.strip() if place_field.value and place_field.value.strip() else None

        try:
            edit_proposal_service.create_proposal(
                booking_id=booking.id,
                proposed_time_slot_id=proposed_time_slot_id,
                proposed_place=proposed_place,
            )
            # Close the dialog and notify success
            page.pop_dialog()
            show_notification(page, "Edit proposal submitted successfully.", "success")
            on_done()
        except ValueError:
            # Neither field was filled — show error notification
            show_notification(page, "Please propose at least a new time slot or place.", "error")

    def handle_cancel(e):
        """
        Handles the cancel button click to close the dialog without changes.

        Parameters:
            e: The Flet click event object.

        Returns:
            None
        """
        page.pop_dialog()

    # Build the dialog
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Propose Edit to Booking"),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    current_info,
                    ft.Divider(height=1),
                    ft.Text("Propose Changes:", weight=ft.FontWeight.BOLD, size=14),
                    time_slot_dropdown,
                    place_field,
                    ft.Text(
                        "At least one field must be filled.",
                        size=12,
                        italic=True,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                spacing=12,
                tight=True,
            ),
            width=400,
            padding=ft.Padding.only(top=10),
        ),
        actions=[
            ft.TextButton("Cancel", on_click=handle_cancel),
            ft.ElevatedButton("Submit Proposal", on_click=handle_submit),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # Show the dialog on the page
    page.show_dialog(dialog)
