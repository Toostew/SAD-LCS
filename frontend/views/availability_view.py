"""
availability_view.py - Lecturer weekly template management view.

This module provides the availability management interface where lecturers can
define recurring weekly consultation slots (by day-of-week and time), manage
exceptions for specific dates, and view a summary of their template.
"""

import flet as ft
from datetime import datetime

from frontend.components.notification_bar import show_notification


# Fixed hour options for the time picker (8:00 through 17:00)
HOUR_OPTIONS = [f"{h:02d}:00" for h in range(8, 18)]

# Day names indexed by weekday number (0=Monday, 4=Friday)
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def availability_view(page: ft.Page, user, availability_service, booking_service=None, user_repo_module=None):
    """
    Builds and returns the weekly template management view for a lecturer.

    Displays the weekly schedule template organized by weekday, allowing
    lecturers to add/remove recurring time slots. Also shows an exceptions
    section for marking specific dates as unavailable.

    Parameters:
        page (ft.Page): The Flet page instance for rendering and updates.
        user: The authenticated User object (lecturer) whose availability is managed.
        availability_service: An AvailabilityService instance for template operations.
        booking_service: Optional BookingService instance (unused in template view).
        user_repo_module: Optional user_repo module (unused in template view).

    Returns:
        ft.Column: The complete availability management view as a Flet Column control.
    """
    # Container for the weekly template grid
    template_container = ft.Column(spacing=5)

    # Container for the exceptions list
    exceptions_container = ft.Column(spacing=5)

    def load_template():
        """Fetches and renders the weekly template grid."""
        templates = availability_service.get_weekly_templates(user.id)
        template_container.controls.clear()

        # Group templates by day of week
        grouped = {i: [] for i in range(5)}
        for t in templates:
            grouped[t.day_of_week].append(t)

        for day_index in range(5):
            day_templates = grouped[day_index]
            day_name = DAY_NAMES[day_index]

            # Build slot chips for this day
            slot_chips = []
            for t in day_templates:
                end_hour = int(t.start_time.split(":")[0]) + 1
                end_time_str = f"{end_hour:02d}:00"
                chip = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(f"{t.start_time}-{end_time_str}", size=13),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=14,
                                tooltip="Remove",
                                on_click=lambda e, tid=t.id: handle_remove_template(tid),
                            ),
                        ],
                        spacing=2,
                        tight=True,
                    ),
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=ft.BorderRadius.all(4),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                )
                slot_chips.append(chip)

            # "Add" button for this day
            add_btn = ft.TextButton(
                "+ Add",
                on_click=lambda e, d=day_index: open_add_template_dialog(d),
            )

            # None indicator if no slots
            if not slot_chips:
                slot_chips.append(
                    ft.Text("(none)", italic=True, size=13, color=ft.Colors.GREY_500)
                )

            day_row = ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(day_name, size=14, weight=ft.FontWeight.W_500),
                        width=100,
                    ),
                    *slot_chips,
                    add_btn,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
            )
            template_container.controls.append(day_row)

        page.update()

    def load_exceptions():
        """Fetches and renders the exceptions list."""
        exceptions = availability_service.get_exceptions(user.id)
        exceptions_container.controls.clear()

        if not exceptions:
            exceptions_container.controls.append(
                ft.Text("No exceptions set.", italic=True, size=13, color=ft.Colors.GREY_500)
            )
        else:
            for exc in exceptions:
                end_hour = int(exc.start_time.split(":")[0]) + 1
                end_time_str = f"{end_hour:02d}:00"
                exc_row = ft.Row(
                    controls=[
                        ft.Text(
                            f"\u2022 {exc.exception_date.strftime('%Y-%m-%d')} "
                            f"({DAY_NAMES[exc.exception_date.weekday()]}) "
                            f"{exc.start_time}-{end_time_str}",
                            size=13,
                        ),
                        ft.TextButton(
                            "Remove",
                            on_click=lambda e, eid=exc.id: handle_remove_exception(eid),
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
                exceptions_container.controls.append(exc_row)

        page.update()

    def handle_remove_template(template_id):
        """Removes a weekly template slot and refreshes the view."""
        availability_service.remove_weekly_template(template_id)
        show_notification(page, "Template slot removed.", type="success")
        load_template()

    def handle_remove_exception(exception_id):
        """Removes an exception and refreshes the view."""
        availability_service.remove_exception(exception_id)
        show_notification(page, "Exception removed.", type="success")
        load_exceptions()

    def open_add_template_dialog(day_index):
        """Opens a dialog to add a time slot for the given day of week."""
        time_dropdown = ft.Dropdown(
            label="Start Time",
            width=150,
            options=[ft.dropdown.Option(h) for h in HOUR_OPTIONS],
        )

        error_text = ft.Text("", color=ft.Colors.RED, visible=False)

        def on_submit(e):
            time_value = time_dropdown.value
            if not time_value:
                error_text.value = "Please select a time."
                error_text.visible = True
                page.update()
                return

            availability_service.add_weekly_template(user.id, day_index, time_value)
            page.pop_dialog()
            show_notification(page, f"Added {time_value} on {DAY_NAMES[day_index]}.", type="success")
            load_template()

        def on_cancel(e):
            page.pop_dialog()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Add Slot - {DAY_NAMES[day_index]}"),
            content=ft.Column(
                controls=[
                    ft.Text("Select a start time for the 1-hour consultation slot:"),
                    time_dropdown,
                    error_text,
                ],
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel),
                ft.ElevatedButton("Add", on_click=on_submit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.show_dialog(dialog)

    def open_add_exception_dialog(e):
        """Opens a dialog to add a new exception (date + time to skip)."""
        # Get current templates to show valid time options
        templates = availability_service.get_weekly_templates(user.id)

        if not templates:
            show_notification(page, "No template slots to create exceptions for.", type="warning")
            return

        # Collect unique times from templates
        unique_times = sorted(set(t.start_time for t in templates))

        date_field = ft.TextField(
            label="Date (YYYY-MM-DD)",
            hint_text="Click calendar to pick",
            read_only=True,
            width=200,
        )

        time_dropdown = ft.Dropdown(
            label="Time Slot to Skip",
            width=150,
            options=[ft.dropdown.Option(t) for t in unique_times],
        )

        error_text = ft.Text("", color=ft.Colors.RED, visible=False)

        picked_date = {"value": None}

        def on_date_picked(e):
            if e.control.value:
                picked = e.control.value
                picked_date["value"] = picked
                date_field.value = picked.strftime("%Y-%m-%d")
                page.update()

        date_picker = ft.DatePicker(
            first_date=datetime.now(),
            on_change=on_date_picked,
        )

        def on_pick_date(e):
            page.show_dialog(date_picker)

        def on_submit(e):
            if not date_field.value or not date_field.value.strip():
                error_text.value = "Please select a date."
                error_text.visible = True
                page.update()
                return

            if not time_dropdown.value:
                error_text.value = "Please select a time slot to skip."
                error_text.visible = True
                page.update()
                return

            try:
                exc_date = datetime.strptime(date_field.value.strip(), "%Y-%m-%d").date()
            except ValueError:
                error_text.value = "Invalid date format."
                error_text.visible = True
                page.update()
                return

            # Validate that this date's weekday matches a template with the chosen time
            day_of_week = exc_date.weekday()
            matching = [t for t in templates if t.day_of_week == day_of_week and t.start_time == time_dropdown.value]
            if not matching:
                error_text.value = (
                    f"No template slot for {time_dropdown.value} on "
                    f"{DAY_NAMES[day_of_week] if day_of_week < 5 else 'weekend'}."
                )
                error_text.visible = True
                page.update()
                return

            availability_service.add_exception(user.id, exc_date, time_dropdown.value)
            page.pop_dialog()
            show_notification(page, "Exception added.", type="success")
            load_exceptions()

        def on_cancel(e):
            page.pop_dialog()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Exception"),
            content=ft.Column(
                controls=[
                    ft.Text("Mark a specific date and time as unavailable:"),
                    ft.Row(
                        controls=[
                            date_field,
                            ft.IconButton(
                                icon=ft.Icons.CALENDAR_MONTH,
                                tooltip="Pick a date",
                                on_click=on_pick_date,
                            ),
                        ],
                        spacing=5,
                    ),
                    time_dropdown,
                    error_text,
                ],
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel),
                ft.ElevatedButton("Add Exception", on_click=on_submit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.show_dialog(dialog)

    # Add Exception button
    add_exception_btn = ft.TextButton(
        "+ Add Exception",
        icon=ft.Icons.EVENT_BUSY,
        on_click=open_add_exception_dialog,
    )

    # Build the complete view layout
    view = ft.Column(
        controls=[
            ft.Text("My Availability", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(height=1),
            ft.Text("Weekly Schedule Template", size=16, weight=ft.FontWeight.W_500),
            ft.Text(
                "Define your recurring consultation slots. Students will see "
                "these auto-generated for the next 14 days.",
                size=12,
                color=ft.Colors.GREY_600,
            ),
            template_container,
            ft.Divider(height=1),
            ft.Text("Exceptions (days you're not available)", size=16, weight=ft.FontWeight.W_500),
            ft.Text(
                "Mark specific dates where you won't be available despite your template.",
                size=12,
                color=ft.Colors.GREY_600,
            ),
            exceptions_container,
            add_exception_btn,
        ],
        spacing=12,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    # Load data on initial render
    load_template()
    load_exceptions()

    return view
