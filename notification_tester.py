from plyer import notification

def send_windows_notification(title, message, timeout=5):
    """
    Sends a Windows notification.

    Parameters:
    - title (str): The title of the notification.
    - message (str): The message content of the notification.
    - timeout (int): Duration for the notification to stay visible (in seconds).
    """
    notification.notify(
        title=title,
        message=message,
        app_name="Python Notification",
        timeout=timeout
    )

# Example usage
if __name__ == "__main__":
    send_windows_notification(
        title="Deep Learning",
        message="Deep learning is a subset of machine learning in artificial intelligence (AI) that has networks capable of learning unsupervised from data that is unstructured or unlabeled.",
        timeout=10
    )
