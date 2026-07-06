"""
Notification bar component using Flet's SnackBar for transient messages.

This module provides a simple function to display brief, auto-dismissing
notification messages to the user with color-coding by message type
(success, error, warning, info).
"""

import flet as ft


def show_notification(page, message, type="info"):
    """
    Displays a transient notification message using Flet's SnackBar.

    Shows a color-coded message at the bottom of the page that auto-dismisses
    after a few seconds. Useful for providing feedback on user actions such as
    successful bookings, errors, or warnings.

    Parameters:
        page: The Flet Page object where the SnackBar will be displayed.
        message: The text message to show in the notification.
        type: The notification type determining background color. One of:
              "success" (green), "error" (red), "warning" (amber), "info" (blue).

    Returns:
        None. The SnackBar is shown as a side effect on the page.
    """
    bgcolor = _get_notification_color(type)

    snack_bar = ft.SnackBar(
        content=ft.Text(message, color=ft.Colors.WHITE),
        bgcolor=bgcolor,
        duration=3000,
    )

    page.show_dialog(snack_bar)


def _get_notification_color(notification_type):
    """
    Maps a notification type string to its corresponding background color.

    Parameters:
        notification_type: A string indicating the notification severity.
                           One of "success", "error", "warning", or "info".

    Returns:
        A Flet color constant for the SnackBar background.
    """
    color_map = {
        "success": ft.Colors.GREEN,
        "error": ft.Colors.RED,
        "warning": ft.Colors.AMBER,
        "info": ft.Colors.BLUE,
    }
    return color_map.get(notification_type, ft.Colors.BLUE)
