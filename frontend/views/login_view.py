"""
login_view.py - Login view for the Lecturer Consultation Service.

This module provides the login UI built with Flet. It renders a login form
with username and password fields, connects to the AuthService for credential
validation, and routes the user to the appropriate dashboard on success.
"""

import flet as ft

from backend.services.auth_service import AuthService


def login_view(page: ft.Page, auth_service: AuthService, on_login_success):
    """
    Builds and displays the login form on the given Flet page.

    Clears the current page content and renders a centered login form with
    username and password text fields and a submit button. On submission,
    credentials are validated via the auth_service. If authentication fails,
    a SnackBar error message is shown. If authentication succeeds, the
    on_login_success callback is invoked with the authenticated User object.

    Parameters:
        page (ft.Page): The Flet page instance to render the login form on.
        auth_service (AuthService): The authentication service used to validate credentials.
        on_login_success (callable): A callback function that receives the authenticated
            User object when login is successful. Typically routes to the appropriate dashboard.

    Returns:
        None
    """
    # Create the username input field
    username_field = ft.TextField(
        label="Username",
        width=300,
        autofocus=True,
    )

    # Create the password input field with hidden text
    password_field = ft.TextField(
        label="Password",
        width=300,
        password=True,
        can_reveal_password=True,
    )

    def handle_login(e):
        """
        Handles the login button click event.

        Reads the username and password from the text fields, calls
        auth_service.authenticate() to validate them. If authentication
        fails (returns None), displays an error SnackBar. If it succeeds,
        calls the on_login_success callback with the authenticated User.

        Parameters:
            e: The Flet event object from the button click.

        Returns:
            None
        """
        username = username_field.value.strip() if username_field.value else ""
        password = password_field.value.strip() if password_field.value else ""

        # Validate that both fields are filled
        if not username or not password:
            page.show_dialog(ft.SnackBar(
                content=ft.Text("Please enter both username and password"),
                bgcolor=ft.Colors.RED_400,
            ))
            return

        # Attempt authentication
        user = auth_service.authenticate(username, password)

        if user is None:
            # Authentication failed — show error message
            page.show_dialog(ft.SnackBar(
                content=ft.Text("Invalid username or password"),
                bgcolor=ft.Colors.RED_400,
            ))
        else:
            # Authentication succeeded — invoke the success callback
            on_login_success(user)

    # Create the submit button
    login_button = ft.ElevatedButton(
        "Login",
        width=300,
        on_click=handle_login,
    )

    # Build the login form layout
    login_form = ft.Column(
        controls=[
            ft.Text(
                "Lecturer Consultation Service",
                size=28,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Text(
                "Please log in to continue",
                size=16,
                color=ft.Colors.GREY_700,
            ),
            ft.Container(height=20),
            username_field,
            password_field,
            ft.Container(height=10),
            login_button,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
    )

    # Clear the page and display the login form
    page.clean()
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(login_form)
    page.update()
