"""
Shared utility functions for JargonTranslator.
"""

from typing import List, Tuple
from plyer import notification


def split_output_to_notifications(output: str) -> List[Tuple[str, str]]:
    """
    Split the API output into title-description pairs for notifications.
    
    Args:
        output: The raw output string from JamAI API.
        
    Returns:
        A list of tuples containing (title, description) pairs.
        
    Example:
        >>> split_output_to_notifications("AI:\\nArtificial Intelligence")
        [('AI', 'Artificial Intelligence')]
    """
    notifications = []
    lines = output.strip().split("\n")

    title = None
    for line in lines:
        line = line.strip()
        if line.endswith(":"):  # Line is a title
            if title:  # Previous title without description
                notifications.append((title, "No description provided."))
            title = line[:-1]  # Remove the colon
        elif line:  # Line is a description
            if title:
                notifications.append((title, line))
                title = None
            # Skip lines without a preceding title

    # Handle trailing title without description
    if title:
        notifications.append((title, "No description provided."))

    return notifications


def show_notification(title: str, message: str, timeout: int = 10) -> None:
    """
    Display a desktop notification.
    
    Args:
        title: The notification title (max 64 characters).
        message: The notification message body.
        timeout: Duration in seconds to show the notification.
    """
    # Truncate title if too long (Windows limitation)
    if len(title) > 64:
        title = title[:61] + "..."
    
    notification.notify(
        title=title,
        message=message,
        app_name="JargonTranslator",
        timeout=timeout,
    )
