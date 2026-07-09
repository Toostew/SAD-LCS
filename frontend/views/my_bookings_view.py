"""
my_bookings_view.py - Student bookings management view.

This module provides the "My Bookings" interface where students can view all
their booking requests with status, lecturer name, date/time, and place.
Students can cancel their own pending bookings from this view.
"""

import flet as ft

from frontend.components.notification_bar import show_notification


def my_bookings_view(page: ft.Page, user, booking_service, user_repo_module, timeslot_repo, availability_service=None):
    """
    Builds and returns the student bookings management view.

    Displays all bookings made by the student with their current status,
    lecturer name, time slot details, and place. Pending bookings show
    Edit and Cancel buttons.

    Parameters:
        page (ft.Page): The Flet page instance for rendering and updates.
        user: The authenticated User object (student) viewing their bookings.
        booking_service: BookingService instance for cancellation operations.
        user_repo_module: The user_repo module for looking up lecturer names.
        timeslot_repo: TimeSlotRepository instance for looking up time slot details.
        availability_service: Optional AvailabilityService for generating available slots.

    Returns:
        ft.Column: The complete bookings management view as a Flet Column control.
    """
    bookings_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

    def load_bookings():
        """
        Fetches the student's bookings and rebuilds the bookings list display.

        For each booking, looks up the lecturer name and time slot details,
        renders a card with status indicator, and shows a Cancel button for
        pending bookings.
        """
        bookings = booking_service.booking_repo.find_by_student(user.id)
        bookings_list.controls.clear()

        if not bookings:
            bookings_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "You have no bookings yet. Go to 'Book Consultation' to make one.",
                        size=14,
                        color=ft.Colors.GREY_600,
                        italic=True,
                    ),
                    padding=20,
                )
            )
        else:
            for booking in bookings:
                # Look up lecturer name
                lecturer = user_repo_module.find_by_id(booking.lecturer_id)
                lecturer_name = lecturer.full_name if lecturer else f"Lecturer #{booking.lecturer_id}"

                # Look up time slot details
                time_slot = timeslot_repo.find_by_id(booking.time_slot_id)
                if time_slot:
                    date_text = time_slot.date.strftime("%A, %d %B %Y") if hasattr(time_slot.date, "strftime") else str(time_slot.date)
                    time_text = f"{time_slot.start_time.strftime('%H:%M')} - {time_slot.end_time.strftime('%H:%M')}"
                else:
                    date_text = "Unknown date"
                    time_text = "Unknown time"

                # Determine status display
                status_value = booking.status.value.capitalize()
                if booking.status.value == "pending":
                    status_color = ft.Colors.AMBER
                elif booking.status.value == "accepted":
                    status_color = ft.Colors.GREEN
                elif booking.status.value == "declined":
                    status_color = ft.Colors.RED
                elif booking.status.value == "invalidated":
                    status_color = ft.Colors.GREY
                else:
                    status_color = ft.Colors.GREY

                # Build card content
                card_controls = [
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CIRCLE, color=status_color, size=12),
                            ft.Text(status_value, color=status_color, weight=ft.FontWeight.W_500),
                        ],
                        spacing=8,
                    ),
                    ft.Text(f"Lecturer: {lecturer_name}", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{date_text}  •  {time_text}", size=13),
                    ft.Text(f"Place: {booking.place}", size=13, color=ft.Colors.GREY_700),
                ]

                # Add action buttons for pending bookings
                if booking.status.value == "pending":
                    edit_btn = ft.TextButton(
                        "Edit Booking",
                        icon=ft.Icons.EDIT,
                        on_click=lambda e, b=booking: open_edit_dialog(b),
                    )
                    cancel_btn = ft.OutlinedButton(
                        "Cancel Booking",
                        icon=ft.Icons.CANCEL_OUTLINED,
                        on_click=lambda e, b=booking: handle_cancel(b),
                    )
                    card_controls.append(ft.Row(controls=[edit_btn, cancel_btn], spacing=8))

                card = ft.Container(
                    content=ft.Column(controls=card_controls, spacing=6),
                    padding=ft.Padding.all(12),
                    border=ft.Border.all(1, ft.Colors.OUTLINE),
                    border_radius=ft.BorderRadius.all(8),
                    width=400,
                )
                bookings_list.controls.append(card)

        page.update()

    def handle_cancel(booking):
        """
        Handles the cancellation of a pending booking.

        Calls booking_service.cancel_booking and shows success/error notification.

        Parameters:
            booking: The Booking instance to cancel.
        """
        try:
            booking_service.cancel_booking(booking.id, user.id)
            show_notification(page, "Booking cancelled successfully.", type="success")
            load_bookings()
        except ValueError as ex:
            show_notification(page, f"Cannot cancel: {ex}", type="error")

    def open_edit_dialog(booking):
        """
        Opens a dialog for the student to edit their pending booking.

        Allows the student to change both the time slot (from the lecturer's
        available slots) and the consultation place before the lecturer accepts.

        Parameters:
            booking: The Booking instance to edit.
        """
        # Get available slots for this lecturer (excluding taken ones)
        available_slots = []
        if availability_service:
            all_slots = availability_service.generate_slots_for_student(booking.lecturer_id)
            for s in all_slots:
                slot_status = booking_service.get_slot_status(s.id)
                # Only show available or queued slots, and the current slot
                if slot_status != "taken" or s.id == booking.time_slot_id:
                    available_slots.append(s)

        # Build time slot dropdown options
        current_slot = timeslot_repo.find_by_id(booking.time_slot_id)
        slot_options = []
        for s in available_slots:
            label = f"{s.date.strftime('%Y-%m-%d')} | {s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
            if s.id == booking.time_slot_id:
                label += " (current)"
            slot_options.append(ft.dropdown.Option(key=str(s.id), text=label))

        time_slot_dropdown = ft.Dropdown(
            label="Time Slot",
            width=350,
            value=str(booking.time_slot_id),
            options=slot_options,
        )

        place_field = ft.TextField(
            label="Consultation Place",
            value=booking.place,
            hint_text="e.g. Room 301, Library, Online",
            width=350,
        )

        error_text = ft.Text("", color=ft.Colors.RED, visible=False)

        def on_submit(e):
            """Saves the updated time slot and/or place to the booking."""
            new_place = place_field.value.strip() if place_field.value else ""
            if not new_place:
                error_text.value = "Place cannot be empty."
                error_text.visible = True
                page.update()
                return

            # Update time slot if changed
            new_slot_id = int(time_slot_dropdown.value) if time_slot_dropdown.value else booking.time_slot_id
            booking.time_slot_id = new_slot_id
            booking.place = new_place
            booking_service.booking_repo.update(booking)

            page.pop_dialog()
            show_notification(page, "Booking updated successfully.", type="success")
            load_bookings()

        def on_cancel(e):
            """Closes the dialog without changes."""
            page.pop_dialog()

        # Build dialog content
        content_controls = []
        if available_slots:
            content_controls.append(ft.Text("Select a different time slot (optional):"))
            content_controls.append(time_slot_dropdown)
        else:
            content_controls.append(
                ft.Text("No other available time slots.", italic=True, color=ft.Colors.GREY_600)
            )
        content_controls.append(ft.Divider(height=1))
        content_controls.append(ft.Text("Update the consultation location:"))
        content_controls.append(place_field)
        content_controls.append(error_text)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Booking"),
            content=ft.Column(
                controls=content_controls,
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel),
                ft.ElevatedButton("Save", on_click=on_submit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.show_dialog(dialog)

    # Build the complete view layout
    view = ft.Column(
        controls=[
            ft.Text("My Bookings", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(height=1),
            bookings_list,
        ],
        spacing=15,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    # Load bookings on initial render
    load_bookings()

    return view
