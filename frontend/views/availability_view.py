"""
availability_view.py - Lecturer availability management view.

This module provides the availability management interface where lecturers can
view their existing time slots, add new 1-hour consultation slots by selecting
a date and start time, and delete slots that have no active bookings.
"""

import flet as ft
from datetime import datetime, date as date_type

from frontend.components.time_slot_card import time_slot_card
from frontend.components.notification_bar import show_notification


# Fixed hour options for the time picker (8:00 through 17:00)
HOUR_OPTIONS = [f"{h:02d}:00" for h in range(8, 18)]


def availability_view(page: ft.Page, user, availability_service):
    """
    Builds and returns the availability management view for a lecturer.

    Displays existing time slots grouped by date with delete capability, and
    provides a form to add new 1-hour time slots using a date picker and a
    dropdown for selecting the start hour.

    Parameters:
        page (ft.Page): The Flet page instance for rendering and updates.
        user: The authenticated User object (lecturer) whose availability is managed.
        availability_service: An AvailabilityService instance for CRUD operations on time slots.

    Returns:
        ft.Column: The complete availability management view as a Flet Column control.
    """
    # Container that holds the list of existing time slot cards
    slots_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

    # State for the add-slot form
    selected_date = ft.Ref[ft.TextField]()
    selected_time = ft.Ref[ft.Dropdown]()

    def load_slots():
        """
        Fetches the lecturer's time slots from the service and rebuilds the slots list.

        Groups time slots by date and renders each slot using the time_slot_card
        component with a delete callback. Shows a placeholder message if no slots exist.

        Returns:
            None
        """
        slots = availability_service.get_lecturer_availability(user.id)
        slots_list.controls.clear()

        if not slots:
            slots_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No availability set. Add time slots using the form below.",
                        size=14,
                        color=ft.Colors.GREY_600,
                        italic=True,
                    ),
                    padding=20,
                )
            )
        else:
            # Group slots by date for organized display
            grouped = {}
            for slot in slots:
                slot_date = slot.date
                if slot_date not in grouped:
                    grouped[slot_date] = []
                grouped[slot_date].append(slot)

            # Render each date group with a header and its slot cards
            for slot_date in sorted(grouped.keys()):
                date_header = slot_date.strftime("%A, %d %B %Y") if hasattr(slot_date, "strftime") else str(slot_date)
                slots_list.controls.append(
                    ft.Text(date_header, size=14, weight=ft.FontWeight.BOLD)
                )
                date_slots_row = ft.Row(
                    controls=[
                        time_slot_card(slot, status="available", on_delete=lambda s: handle_delete(s))
                        for slot in grouped[slot_date]
                    ],
                    wrap=True,
                    spacing=10,
                )
                slots_list.controls.append(date_slots_row)

        page.update()

    def handle_delete(slot):
        """
        Handles the deletion of a time slot.

        Calls the availability service to remove the slot. Shows a success
        notification and refreshes the list on success, or an error notification
        if the slot has active bookings and cannot be deleted.

        Parameters:
            slot: The TimeSlot instance to delete.

        Returns:
            None
        """
        success = availability_service.remove_time_slot(slot.id)
        if success:
            show_notification(page, "Time slot removed successfully.", type="success")
            load_slots()
        else:
            show_notification(
                page,
                "Cannot delete this slot — it has pending or accepted bookings.",
                type="error",
            )

    def handle_add(e):
        """
        Handles the addition of a new time slot.

        Reads the selected date and start time from the form, validates inputs,
        constructs a start_time datetime, and calls the availability service to
        create the slot. Shows appropriate notifications and refreshes the list.

        Parameters:
            e: The Flet click event from the Add Slot button.

        Returns:
            None
        """
        date_value = selected_date.current.value
        time_value = selected_time.current.value

        # Validate that both fields are filled
        if not date_value or not date_value.strip():
            show_notification(page, "Please select a date.", type="warning")
            return
        if not time_value:
            show_notification(page, "Please select a start time.", type="warning")
            return

        try:
            # Parse the date string (expected format: YYYY-MM-DD)
            slot_date = datetime.strptime(date_value.strip(), "%Y-%m-%d").date()
        except ValueError:
            show_notification(page, "Invalid date format. Use YYYY-MM-DD.", type="error")
            return

        # Parse the hour from the selected time option
        hour = int(time_value.split(":")[0])
        start_time = datetime(slot_date.year, slot_date.month, slot_date.day, hour, 0, 0)

        try:
            availability_service.create_time_slot(
                lecturer_id=user.id,
                slot_date=slot_date,
                start_time=start_time,
            )
            show_notification(page, "Time slot added successfully.", type="success")
            # Clear the form fields after successful add
            selected_date.current.value = ""
            selected_time.current.value = None
            load_slots()
        except ValueError as ex:
            show_notification(page, f"Error: {ex}", type="error")

    def on_date_picked(e):
        """
        Handles the date picker result and updates the date text field.

        Formats the picked date as YYYY-MM-DD and writes it into the date
        input field for display and later use.

        Parameters:
            e: The Flet DatePicker change event containing the selected date.

        Returns:
            None
        """
        if e.control.value:
            picked = e.control.value
            selected_date.current.value = picked.strftime("%Y-%m-%d")
            page.update()

    # Build the date picker
    date_picker = ft.DatePicker(
        first_date=datetime.now(),
        on_change=on_date_picked,
    )

    # Date input field with a calendar icon button to open the picker
    date_field = ft.TextField(
        ref=selected_date,
        label="Date (YYYY-MM-DD)",
        hint_text="Click calendar to pick",
        read_only=True,
        width=200,
    )

    date_pick_button = ft.IconButton(
        icon=ft.Icons.CALENDAR_MONTH,
        tooltip="Pick a date",
        on_click=lambda e: page.show_dialog(date_picker),
    )

    # Dropdown for selecting the start time hour
    time_dropdown = ft.Dropdown(
        ref=selected_time,
        label="Start Time",
        width=150,
        options=[ft.dropdown.Option(h) for h in HOUR_OPTIONS],
    )

    # Add Slot button
    add_button = ft.ElevatedButton(
        "Add Slot",
        icon=ft.Icons.ADD,
        on_click=handle_add,
    )

    # Assemble the add-slot form row
    add_form = ft.Row(
        controls=[
            date_field,
            date_pick_button,
            time_dropdown,
            add_button,
        ],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
    )

    # Build the complete view layout
    view = ft.Column(
        controls=[
            ft.Text("My Availability", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(height=1),
            ft.Text("Add New Time Slot", size=16, weight=ft.FontWeight.W_500),
            add_form,
            ft.Divider(height=1),
            ft.Text("Existing Time Slots", size=16, weight=ft.FontWeight.W_500),
            slots_list,
        ],
        spacing=15,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    # Load existing slots on initial render
    load_slots()

    return view
