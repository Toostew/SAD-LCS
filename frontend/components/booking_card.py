"""
Reusable booking card component for displaying booking details.

This module provides a function to build a Flet Container that renders a single
booking with student/lecturer information, place, status badge, and optional
action buttons for lecturers to accept, decline, or propose edits.
"""

import flet as ft


def booking_card(booking, student_name="", lecturer_name="", on_accept=None, on_decline=None, on_propose_edit=None):
    """
    Creates a visual card representing a single booking with status and action buttons.

    Renders a card showing the booking's student name, lecturer name, place, and a
    color-coded status badge. Optionally includes Accept, Decline, and Propose Edit
    buttons for the lecturer's queue management view.

    Parameters:
        booking: A Booking dataclass instance with status, place, and other fields.
        student_name: Display name of the student who made the booking.
        lecturer_name: Display name of the lecturer being consulted.
        on_accept: Optional callback triggered when Accept is clicked. If None, button is hidden.
        on_decline: Optional callback triggered when Decline is clicked. If None, button is hidden.
        on_propose_edit: Optional callback triggered when Propose Edit is clicked. If None, button is hidden.

    Returns:
        A ft.Container wrapping the booking card layout with status badge and action buttons.
    """
    # Determine status badge color and text
    status_value = booking.status.value if hasattr(booking.status, "value") else str(booking.status)
    badge_color = _get_status_color(status_value)
    badge_text = status_value.capitalize()

    # Build info rows
    info_controls = []
    if student_name:
        info_controls.append(
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PERSON, size=16),
                    ft.Text(f"Student: {student_name}", size=13),
                ],
                spacing=6,
            )
        )
    if lecturer_name:
        info_controls.append(
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SCHOOL, size=16),
                    ft.Text(f"Lecturer: {lecturer_name}", size=13),
                ],
                spacing=6,
            )
        )
    info_controls.append(
        ft.Row(
            controls=[
                ft.Icon(ft.Icons.PLACE, size=16),
                ft.Text(f"Place: {booking.place}", size=13),
            ],
            spacing=6,
        )
    )

    # Status badge
    status_badge = ft.Container(
        content=ft.Text(badge_text, size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
        bgcolor=badge_color,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border_radius=ft.BorderRadius.all(12),
    )

    # Build action buttons
    action_buttons = []
    if on_accept is not None and status_value == "pending":
        action_buttons.append(
            ft.ElevatedButton(
                "Accept",
                icon=ft.Icons.CHECK,
                bgcolor=ft.Colors.GREEN,
                color=ft.Colors.WHITE,
                on_click=lambda e: on_accept(booking),
            )
        )
    if on_decline is not None and status_value == "pending":
        action_buttons.append(
            ft.OutlinedButton(
                "Decline",
                icon=ft.Icons.CLOSE,
                on_click=lambda e: on_decline(booking),
            )
        )
    if on_propose_edit is not None and status_value == "pending":
        action_buttons.append(
            ft.TextButton(
                "Propose Edit",
                icon=ft.Icons.EDIT,
                on_click=lambda e: on_propose_edit(booking),
            )
        )

    # Assemble card content
    card_content = ft.Column(
        controls=[
            ft.Row(
                controls=[ft.Text("Booking", weight=ft.FontWeight.BOLD, size=14), status_badge],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        ]
        + info_controls
        + ([ft.Row(controls=action_buttons, spacing=8)] if action_buttons else []),
        spacing=8,
    )

    return ft.Container(
        content=card_content,
        padding=ft.Padding.all(12),
        border=ft.Border.all(1, ft.Colors.OUTLINE),
        border_radius=ft.BorderRadius.all(8),
        width=350,
    )


def _get_status_color(status_value):
    """
    Maps a booking status string to its corresponding badge background color.

    Parameters:
        status_value: A string representing the booking status
                      ("pending", "accepted", "declined", or "invalidated").

    Returns:
        A Flet color constant for the badge background.
    """
    color_map = {
        "pending": ft.Colors.AMBER,
        "accepted": ft.Colors.GREEN,
        "declined": ft.Colors.RED,
        "invalidated": ft.Colors.GREY,
    }
    return color_map.get(status_value, ft.Colors.GREY)
