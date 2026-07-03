"""
booking_view.py - Student booking interface for the Lecturer Consultation Service.

This module provides the booking view where students can browse lecturers,
view their available time slots with color-coded status indicators
(green=available, amber=queued, red=taken), and submit booking requests
with a specified consultation place.
"""

import flet as ft

from frontend.components.time_slot_card import time_slot_card
from frontend.components.notification_bar import show_notification
from backend.models import SlotUnavailableError


def booking_view(page, user, booking_service, availability_service, user_repo_module):
    """
    Builds and returns the booking view content for students.

    Displays a dropdown of all lecturers. When a lecturer is selected,
    loads their time slots with status indicators (green=available,
    amber=queued, red=taken). Students can click "Book" on an available
    or queued slot to open a dialog asking for a consultation place.
    On submit, creates a booking and shows success or error notification.

    Parameters:
        page: The Flet Page object for UI updates and dialog display.
        user: The authenticated student User object (used as the booking requester).
        booking_service: BookingService instance for creating bookings and querying slot status.
        availability_service: AvailabilityService instance for retrieving lecturer time slots.
        user_repo_module: The user_repo module providing find_all_lecturers().

    Returns:
        A ft.Column control containing the full booking interface.
    """
    # Container that holds the time slot cards for the selected lecturer
    slots_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

    # Currently selected lecturer (stored as a dict with id and name)
    selected_lecturer = {"id": None, "name": None}

    def load_slots():
        """
        Loads and displays time slots for the currently selected lecturer.

        Clears the slots container and re-populates it with time_slot_card
        components. Each card shows the slot's status (available/queued/taken)
        and a Book button for available or queued slots.
        """
        slots_container.controls.clear()

        if selected_lecturer["id"] is None:
            slots_container.controls.append(
                ft.Text("Select a lecturer to view their available time slots.", italic=True)
            )
            page.update()
            return

        # Retrieve all time slots for the selected lecturer
        time_slots = availability_service.get_lecturer_availability(selected_lecturer["id"])

        if not time_slots:
            slots_container.controls.append(
                ft.Text("No time slots available for this lecturer.", italic=True)
            )
            page.update()
            return

        # Build a card for each time slot with its current status
        for slot in time_slots:
            status = booking_service.get_slot_status(slot.id)
            pending_count = booking_service.get_pending_count(slot.id)

            card = time_slot_card(
                time_slot=slot,
                status=status,
                pending_count=pending_count,
                on_book=lambda s, slot_ref=slot: open_booking_dialog(slot_ref),
            )
            slots_container.controls.append(card)

        page.update()

    def open_booking_dialog(slot):
        """
        Opens a dialog asking the student to enter a consultation place.

        Displays a modal dialog with a text field for the place input and
        submit/cancel buttons. On submit, calls create_booking and handles
        success or SlotUnavailableError.

        Parameters:
            slot: The TimeSlot object the student wants to book.
        """
        place_field = ft.TextField(
            label="Consultation Place",
            hint_text="e.g. Room 301, Library, Online",
            autofocus=True,
        )

        error_text = ft.Text("", color=ft.Colors.RED, visible=False)

        def on_submit(e):
            """
            Handles booking submission when the user clicks Submit.

            Validates that the place field is not empty, then calls
            booking_service.create_booking(). On success, closes the dialog
            and shows a success notification. On SlotUnavailableError, shows
            an error message within the dialog.
            """
            place = place_field.value.strip()

            if not place:
                error_text.value = "Please enter a consultation place."
                error_text.visible = True
                page.update()
                return

            try:
                booking_service.create_booking(
                    student_id=user.id,
                    time_slot_id=slot.id,
                    lecturer_id=selected_lecturer["id"],
                    place=place,
                )
                # Close dialog and show success
                dialog.open = False
                page.update()
                show_notification(page, "Booking request submitted successfully!", type="success")
                # Refresh slots to show updated status
                load_slots()

            except SlotUnavailableError:
                # Slot was taken between viewing and submitting
                error_text.value = "This time slot is no longer available."
                error_text.visible = True
                page.update()

        def on_cancel(e):
            """Closes the booking dialog without creating a booking."""
            dialog.open = False
            page.update()

        # Build the booking dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Book Consultation"),
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"Lecturer: {selected_lecturer['name']}",
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"Date: {slot.date.strftime('%A, %d %B %Y')}",
                    ),
                    ft.Text(
                        f"Time: {slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}",
                    ),
                    ft.Divider(),
                    place_field,
                    error_text,
                ],
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel),
                ft.ElevatedButton("Submit", on_click=on_submit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def on_lecturer_selected(e):
        """
        Handles lecturer dropdown selection change.

        Updates the selected lecturer and refreshes the time slot display
        to show the newly selected lecturer's availability.

        Parameters:
            e: The Flet event object from the dropdown change.
        """
        if e.control.value:
            # The dropdown value stores the lecturer ID as a string
            lecturer_id = int(e.control.value)
            # Find the lecturer name from the options
            for option in lecturer_dropdown.options:
                if option.key == e.control.value:
                    selected_lecturer["name"] = option.text
                    break
            selected_lecturer["id"] = lecturer_id
            load_slots()

    # Load all lecturers for the dropdown
    lecturers = user_repo_module.find_all_lecturers()

    # Build lecturer dropdown
    lecturer_dropdown = ft.Dropdown(
        label="Select Lecturer",
        hint_text="Choose a lecturer to view their time slots",
        width=400,
        options=[
            ft.dropdown.Option(key=str(lec.id), text=lec.full_name)
            for lec in lecturers
        ],
        on_change=on_lecturer_selected,
    )

    # Assemble the complete booking view layout
    view_layout = ft.Column(
        controls=[
            ft.Text("Book a Consultation", size=24, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Select a lecturer and choose an available time slot to request a consultation.",
                size=14,
                color=ft.Colors.GREY_700,
            ),
            ft.Divider(),
            lecturer_dropdown,
            ft.Container(height=10),
            ft.Text("Available Time Slots", size=18, weight=ft.FontWeight.W_600),
            slots_container,
        ],
        spacing=10,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    # Show initial placeholder message
    load_slots()

    return view_layout
