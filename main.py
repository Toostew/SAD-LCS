"""
main.py - Entry point for the Lecturer Consultation Service web application.

This module initializes the database, seeds hardcoded users, and launches the
Flet web application. It wires the full navigation flow:
Login → Dashboard → Feature Views → Logout → Login.
"""

import flet as ft

from backend.database import init_db
from backend.models import User, Role
from backend.services.auth_service import AuthService, seed_users
from backend.services.availability_service import AvailabilityService
from backend.services.booking_service import BookingService
from backend.services.edit_proposal_service import EditProposalService
from backend.repositories.timeslot_repo import TimeSlotRepository
from backend.repositories.booking_repo import BookingRepository
from backend.repositories import user_repo, edit_proposal_repo
from frontend.views.login_view import login_view
from frontend.views.student_dashboard import student_dashboard
from frontend.views.lecturer_dashboard import lecturer_dashboard


def main(page: ft.Page):
    """
    Main function that configures the Flet page and wires the full application flow.

    Sets up page configuration, creates all service instances with proper
    dependency injection, defines navigation callbacks (login, dashboard routing,
    logout), and starts the app on the login view.

    Parameters:
        page (ft.Page): The Flet page instance provided by the framework.

    Returns:
        None
    """
    # Configure page appearance and layout
    page.title = "Lecturer Consultation Service"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Create repository instances
    timeslot_repo = TimeSlotRepository()
    booking_repo = BookingRepository()

    # Create service instances with injected dependencies
    auth_service = AuthService()
    availability_service = AvailabilityService(timeslot_repo, booking_repo)
    booking_service = BookingService(booking_repo, timeslot_repo)
    edit_proposal_service = EditProposalService(edit_proposal_repo, booking_repo)

    def show_login():
        """
        Displays the login view on the page.

        Clears any existing content and renders the login form. On successful
        authentication, routes to the appropriate dashboard via on_login_success.
        """
        login_view(page, auth_service, on_login_success)

    def on_login_success(user: User):
        """
        Routes an authenticated user to the correct dashboard based on their role.

        Called by the login view after successful credential validation.
        Students are routed to the student dashboard, lecturers to the lecturer
        dashboard. Both dashboards receive the service instances needed to
        render their feature views.

        Parameters:
            user (User): The authenticated user object with role information.
        """
        if user.role == Role.STUDENT:
            student_dashboard(
                page=page,
                user=user,
                on_logout=on_logout,
                booking_service=booking_service,
                availability_service=availability_service,
                edit_proposal_service=edit_proposal_service,
                booking_repo=booking_repo,
                timeslot_repo=timeslot_repo,
                user_repo_module=user_repo,
            )
        elif user.role == Role.LECTURER:
            lecturer_dashboard(
                page=page,
                user=user,
                on_logout=on_logout,
                availability_service=availability_service,
                booking_service=booking_service,
                edit_proposal_service=edit_proposal_service,
                user_repo_module=user_repo,
            )

    def on_logout():
        """
        Handles user logout by returning to the login view.

        Clears all page content and re-displays the login form, allowing
        a different user to log in.
        """
        show_login()

    # Start the application with the login view
    show_login()


# Initialize database schema and seed users on startup
init_db()
seed_users()

# Launch the Flet app as a web application
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
