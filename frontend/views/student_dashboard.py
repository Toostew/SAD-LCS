"""
student_dashboard.py - Student dashboard view for the Lecturer Consultation Service.

This module provides the student dashboard UI built with Flet. It renders a
navigation rail with access to student-specific features: browsing lecturers
and viewing availability, booking consultations, and responding to edit proposals.
The navigation wires actual feature views instead of placeholders.
"""

import flet as ft

from backend.models import User
from frontend.views.booking_view import booking_view
from frontend.views.my_bookings_view import my_bookings_view
from frontend.views.edit_proposal_view import edit_proposal_view


def student_dashboard(
    page: ft.Page,
    user: User,
    on_logout,
    booking_service,
    availability_service,
    edit_proposal_service,
    booking_repo,
    timeslot_repo,
    user_repo_module,
):
    """
    Builds and displays the student dashboard on the given Flet page.

    Clears the current page content and renders a dashboard layout with a
    navigation rail on the left for switching between student features, a
    header showing the user's name and a logout button, and a content area
    that renders actual feature views based on the selected navigation item.

    Parameters:
        page (ft.Page): The Flet page instance to render the dashboard on.
        user (User): The authenticated student user object.
        on_logout (callable): Callback invoked when the user clicks logout.
        booking_service: BookingService instance for booking operations.
        availability_service: AvailabilityService instance for time slot queries.
        edit_proposal_service: EditProposalService instance for proposal responses.
        booking_repo: BookingRepository instance for booking data access.
        timeslot_repo: TimeSlotRepository instance for time slot data access.
        user_repo_module: The user_repo module for user lookups.

    Returns:
        None
    """
    # Define navigation destinations for student features
    nav_items = [
        {"label": "Book Consultation", "icon": ft.Icons.CALENDAR_MONTH},
        {"label": "My Bookings", "icon": ft.Icons.LIST_ALT},
        {"label": "Edit Proposals", "icon": ft.Icons.EDIT_NOTE},
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
            # Book Consultation — browse lecturers, view availability, and book
            content_area.content = booking_view(
                page=page,
                user=user,
                booking_service=booking_service,
                availability_service=availability_service,
                user_repo_module=user_repo_module,
            )
        elif index == 1:
            # My Bookings — view, edit, and cancel own bookings
            content_area.content = my_bookings_view(
                page=page,
                user=user,
                booking_service=booking_service,
                user_repo_module=user_repo_module,
                timeslot_repo=timeslot_repo,
                availability_service=availability_service,
            )
        elif index == 2:
            # Edit Proposals — respond to lecturer-proposed booking changes
            content_area.content = edit_proposal_view(
                page=page,
                user=user,
                edit_proposal_service=edit_proposal_service,
                booking_repo=booking_repo,
                booking_service=booking_service,
                timeslot_repo=timeslot_repo,
                availability_service=availability_service,
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
                ft.Text("Student", size=14, color=ft.Colors.GREY_600),
                ft.ElevatedButton(
                    "Logout",
                    icon=ft.Icons.LOGOUT,
                    on_click=lambda e: on_logout(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=10),
        bgcolor=ft.Colors.BLUE_50,
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

    # Load the first section (Book Consultation) by default
    load_section(0)
