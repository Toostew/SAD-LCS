"""
queue_view.py - Booking queue management view for lecturers.

This module provides the queue view where lecturers can see all pending
booking requests grouped by time slot, accept or decline bookings, and
receive feedback about conflicts and daily limit enforcement.
"""

import flet as ft

from frontend.components.booking_card import booking_card
from frontend.components.notification_bar import show_notification
from frontend.views.propose_edit_dialog import show_propose_edit_dialog


def queue_view(page, user, booking_service, availability_service, user_repo_module, edit_proposal_service=None):
    """
    Builds and returns the booking queue management view for a lecturer.

    Retrieves the lecturer's time slots, groups pending bookings per slot,
    and displays each booking with student name, place, and submission order.
    Provides accept, decline, and propose edit buttons with appropriate feedback
    for conflicts and daily limit enforcement.

    Parameters:
        page: The Flet Page object for rendering and notifications.
        user: The authenticated lecturer User object.
        booking_service: An instance of BookingService for queue and accept/decline actions.
        availability_service: An instance of AvailabilityService to get lecturer time slots.
        user_repo_module: The user_repo module providing find_by_id() for student name lookup.
        edit_proposal_service: Optional EditProposalService instance for proposing edits.
            If None, the propose edit button will not be shown.

    Returns:
        A ft.Container wrapping the complete queue management view.
    """

    def build_content():
        """
        Builds the full content column with all time slots and their booking queues.

        Iterates over the lecturer's time slots, retrieves the pending booking
        queue for each, and creates booking cards with accept/decline actions.

        Returns:
            A ft.Column containing all slot sections or an empty state message.
        """
        slots = availability_service.get_lecturer_availability(user.id)
        slot_sections = []

        for slot in slots:
            queue = booking_service.get_booking_queue(user.id, slot.id)

            if not queue:
                # Skip slots with no pending bookings
                continue

            # Check if the lecturer can still accept bookings on this date
            can_accept = booking_service.can_accept_on_date(user.id, slot.date)

            # Build the slot header with date and time info
            slot_header = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ACCESS_TIME, size=18, color=ft.Colors.BLUE),
                        ft.Text(
                            f"{slot.date.strftime('%Y-%m-%d')}  |  "
                            f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}",
                            size=15,
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.Text(
                            f"({len(queue)} pending)",
                            size=13,
                            color=ft.Colors.GREY_600,
                        ),
                    ],
                    spacing=8,
                ),
                padding=ft.Padding.only(bottom=8, top=4),
            )

            # Build booking cards for each queued booking
            booking_cards = []
            for order_index, bk in enumerate(queue, start=1):
                # Look up the student name
                student = user_repo_module.find_by_id(bk.student_id)
                student_name = student.full_name if student else f"Student #{bk.student_id}"

                # Create accept handler for this booking
                def make_accept_handler(booking):
                    """Creates a closure for the accept button click handler."""
                    def handle_accept(b):
                        success, message = booking_service.accept_booking(b.id)
                        if success:
                            show_notification(page, "Booking accepted successfully.", "success")
                        elif "conflict" in message:
                            show_notification(
                                page,
                                "Another booking already accepted for this time slot.",
                                "warning",
                            )
                        elif "daily_limit_reached" in message:
                            show_notification(
                                page,
                                "Daily booking limit (5) reached for this date.",
                                "warning",
                            )
                        refresh_view()
                    return handle_accept
                
                # Create decline handler for this booking
                def make_decline_handler(booking):
                    """Creates a closure for the decline button click handler."""
                    def handle_decline(b):
                        booking_service.decline_booking(b.id)
                        show_notification(page, "Booking declined.", "info")
                        refresh_view()
                    return handle_decline

                # Create propose edit handler for this booking
                def make_propose_edit_handler(booking):
                    """Creates a closure for the propose edit button click handler."""
                    def handle_propose_edit(b):
                        show_propose_edit_dialog(
                            page=page,
                            booking=b,
                            edit_proposal_service=edit_proposal_service,
                            availability_service=availability_service,
                            lecturer_id=user.id,
                            on_done=refresh_view,
                        )
                    return handle_propose_edit

                # Build the card with order number, using the booking_card component
                # If daily limit reached, pass None for on_accept to disable the button
                accept_handler = make_accept_handler(bk) if can_accept else None
                decline_handler = make_decline_handler(bk)
                propose_edit_handler = make_propose_edit_handler(bk) if edit_proposal_service else None

                card = booking_card(
                    booking=bk,
                    student_name=f"#{order_index} — {student_name}",
                    on_accept=accept_handler,
                    on_decline=decline_handler,
                    on_propose_edit=propose_edit_handler,
                )
                booking_cards.append(card)

            # Add daily limit warning if limit reached
            limit_warning = []
            if not can_accept:
                limit_warning.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.WARNING, size=16, color=ft.Colors.AMBER),
                                ft.Text(
                                    "Daily booking limit reached — accept buttons disabled for this date.",
                                    size=12,
                                    color=ft.Colors.AMBER_700,
                                    italic=True,
                                ),
                            ],
                            spacing=6,
                        ),
                        padding=ft.Padding.only(top=4, bottom=4),
                    )
                )

            # Assemble the slot section
            slot_section = ft.Container(
                content=ft.Column(
                    controls=[slot_header] + limit_warning + booking_cards,
                    spacing=10,
                ),
                padding=ft.Padding.all(12),
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=ft.BorderRadius.all(8),
            )
            slot_sections.append(slot_section)

        # Handle empty state — no pending bookings at all
        if not slot_sections:
            return ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.INBOX, size=48, color=ft.Colors.GREY_400),
                                ft.Text(
                                    "No pending booking requests",
                                    size=16,
                                    color=ft.Colors.GREY_600,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=12,
                        ),
                        alignment=ft.Alignment.CENTER,
                        padding=ft.Padding.all(40),
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        return ft.Column(controls=slot_sections, spacing=16, scroll=ft.ScrollMode.AUTO)

    # Container that holds the dynamic content
    content_container = ft.Container(expand=True)

    def refresh_view():
        """
        Rebuilds the queue view content and updates the page.

        Called after any accept or decline action to reflect the updated
        booking queue state.
        """
        content_container.content = build_content()
        page.update()

    # Build the view header
    view_header = ft.Container(
        content=ft.Text(
            "Booking Queue Management",
            size=20,
            weight=ft.FontWeight.BOLD,
        ),
        padding=ft.Padding.only(bottom=12),
    )

    # Initial content build
    content_container.content = build_content()

    # Assemble the full view
    view_layout = ft.Column(
        controls=[view_header, content_container],
        expand=True,
        spacing=8,
    )

    return ft.Container(
        content=view_layout,
        padding=ft.Padding.all(20),
        expand=True,
    )
