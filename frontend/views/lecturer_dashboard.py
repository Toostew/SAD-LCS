"""
lecturer_dashboard.py - Lecturer dashboard view for the Lecturer Consultation Service.

This module provides the lecturer dashboard UI built with Flet. It renders a
navigation rail with access to lecturer-specific features: managing availability,
viewing and managing booking requests (queue), and proposing edits to bookings.
The navigation wires actual feature views instead of placeholders.
"""

import flet as ft

from backend.models import User
from frontend.views.availability_view import availability_view
from frontend.views.queue_view import queue_view


def lecturer_dashboard(
    page: ft.Page,
    user: User,
    on_logout,
    availability_service,
    booking_service,
    edit_proposal_service,
    user_repo_module,
):
    """
    Builds and displays the lecturer dashboard on the given Flet page.

    Clears the current page content and renders a dashboard layout with a
    navigation rail on the left for switching between lecturer features, a
    header showing the user's name and a logout button, and a content area
    that renders actual feature views based on the selected navigation item.

    Parameters:
        page (ft.Page): The Flet page instance to render the dashboard on.
        user (User): The authenticated lecturer user object.
        on_logout (callable): Callback invoked when the user clicks logout.
        availability_service: AvailabilityService instance for time slot management.
        booking_service: BookingService instance for queue and booking operations.
        edit_proposal_service: EditProposalService instance for proposing edits.
        user_repo_module: The user_repo module for user lookups.

    Returns:
        None
    """
    # Define navigation destinations for lecturer features
    nav_items = [
        {"label": "My Availability", "icon": ft.icons.SCHEDULE},
        {"label": "Booking Requests", "icon": ft.icons.INBOX},
    ]

    # Content area that displays the selected section's actual view
    content_area = ft.Container(
        expand=True,
        padding=20,
    )

    def load_section(index: int):
        """
        Loads the actual feature view for the selected navigation index.

        Builds the appropriate view component and places it inside the
        content area container, then updates the page.

        Parameters:
            index (int): The navigation rail selected index.

        Returns:
            None
        """
        if index == 0:
            # My Availability — manage consultation time slots
            content_area.content = availability_view(
                page=page,
                user=user,
                availability_service=availability_service,
            )
        elif index == 1:
            # Booking Requests — view queue, accept/decline, propose edits
            content_area.content = queue_view(
                page=page,
                user=user,
                booking_service=booking_service,
                availability_service=availability_service,
                user_repo_module=user_repo_module,
                edit_proposal_service=edit_proposal_service,
            )
        else:
            content_area.content = ft.Text("Unknown section", size=16)

        page.update()

    def on_nav_change(e):
        """
        Handles navigation rail selection changes.

        Loads the corresponding feature view into the content area.

        Parameters:
            e: The Flet event object from the navigation rail change.

        Returns:
            None
        """
        load_section(e.control.selected_index)

    # Build the navigation rail
    nav_rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        destinations=[
            ft.NavigationRailDestination(
                icon=item["icon"],
                label=item["label"],
            )
            for item in nav_items
        ],
        on_change=on_nav_change,
    )

    # Build the header with user info and logout button
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    f"Welcome, {user.full_name}",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(expand=True),
                ft.Text("Lecturer", size=14, color=ft.colors.GREY_600),
                ft.ElevatedButton(
                    text="Logout",
                    icon=ft.icons.LOGOUT,
                    on_click=lambda e: on_logout(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.symmetric(horizontal=20, vertical=10),
        bgcolor=ft.colors.GREEN_50,
    )

    # Assemble the full dashboard layout
    dashboard_layout = ft.Column(
        controls=[
            header,
            ft.Row(
                controls=[
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    content_area,
                ],
                expand=True,
            ),
        ],
        expand=True,
        spacing=0,
    )

    # Clear the page and display the dashboard
    page.clean()
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.add(dashboard_layout)

    # Load the first section (My Availability) by default
    load_section(0)
