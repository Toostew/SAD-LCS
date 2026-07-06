"""
Reusable time slot card component for displaying time slot information.

This module provides a function to build a Flet Container that renders a single
time slot with its date, time range, and a color-coded status indicator showing
whether the slot is available, queued, or taken.
"""

import flet as ft


def time_slot_card(time_slot, status="available", pending_count=0, on_book=None, on_delete=None):
    """
    Creates a visual card representing a single time slot with status indicator.

    Renders a card showing the slot's date, time range, and a color-coded status
    indicator. Optionally includes a Book button (for students) and/or a Delete
    button (for lecturers) depending on the callbacks provided.

    Parameters:
        time_slot: A TimeSlot dataclass instance with date, start_time, and end_time fields.
        status: The slot's current status string — one of "available", "queued", or "taken".
                Determines the indicator color and text displayed.
        pending_count: Number of pending booking requests for this slot (shown when queued).
        on_book: Optional callback function triggered when the Book button is clicked.
                 If None, the Book button is not displayed.
        on_delete: Optional callback function triggered when the Delete button is clicked.
                   If None, the Delete button is not displayed.

    Returns:
        A ft.Container wrapping the time slot card layout with status indicator and action buttons.
    """
    # Determine indicator color and text based on status
    if status == "available":
        indicator_color = ft.Colors.GREEN
        indicator_text = "Available"
        book_enabled = True
    elif status == "queued":
        indicator_color = ft.Colors.AMBER
        suffix = "request" if pending_count == 1 else "requests"
        indicator_text = f"Queued ({pending_count} pending {suffix})"
        book_enabled = True
    else:  # "taken"
        indicator_color = ft.Colors.RED
        indicator_text = "Taken"
        book_enabled = False

    # Format date and time display
    date_text = time_slot.date.strftime("%A, %d %B %Y") if hasattr(time_slot.date, "strftime") else str(time_slot.date)
    time_text = f"{time_slot.start_time.strftime('%H:%M')} - {time_slot.end_time.strftime('%H:%M')}"

    # Build action buttons row
    action_buttons = []
    if on_book is not None:
        action_buttons.append(
            ft.ElevatedButton(
                "Book",
                icon=ft.Icons.BOOKMARK_ADD,
                disabled=not book_enabled,
                on_click=lambda e: on_book(time_slot) if book_enabled else None,
            )
        )
    if on_delete is not None:
        action_buttons.append(
            ft.OutlinedButton(
                "Delete",
                icon=ft.Icons.DELETE_OUTLINE,
                on_click=lambda e: on_delete(time_slot),
            )
        )

    # Build the card content
    card_content = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CIRCLE, color=indicator_color, size=12),
                    ft.Text(indicator_text, color=indicator_color, weight=ft.FontWeight.W_500),
                ],
                spacing=8,
            ),
            ft.Text(date_text, size=14, weight=ft.FontWeight.BOLD),
            ft.Text(time_text, size=13),
        ]
        + ([ft.Row(controls=action_buttons, spacing=8)] if action_buttons else []),
        spacing=6,
    )

    return ft.Container(
        content=card_content,
        padding=ft.Padding.all(12),
        border=ft.Border.all(1, ft.Colors.OUTLINE),
        border_radius=ft.BorderRadius.all(8),
        width=300,
    )
