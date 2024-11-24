import requests
from plyer import notification
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

#retreive the api keys from the .env file
PROJECT_ID = os.getenv("PROJECT_ID")
API_KEY = os.getenv("API_KEY")

# JamAI API Configuration
url = "https://api.jamaibase.com/api/v1/gen_tables/action/rows/add"
payload = {
    "data": [
        {
            "input": "Deep learning is an artificial intelligence (AI) method that teaches computers to process data in a way inspired by the human brain. Deep learning models can recognize complex pictures, text, sounds, and other data patterns to produce accurate insights and predictions."
        }
    ],
    "table_id": "pwd",
    "stream": False,
}
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": "Bearer " + API_KEY,
    "X-PROJECT-ID": PROJECT_ID,
}

def send_request_and_get_output():
    """Send text to JamAI and extract the output."""
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes

        # Parse the JSON response
        response_data = response.json()

        # Extract the "Output" field
        rows = response_data.get("rows", [])
        if rows:
            output = rows[0]["columns"]["Output"]["choices"][0]["message"]["content"]
            return output
        else:
            return "No output received from JamAI."

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with JamAI: {e}")
        return "Error: Could not fetch response from JamAI."

def split_output_to_notifications(output):
    """Split the output into title-description pairs."""
    notifications = []
    lines = output.strip().split("\n")  # Split by lines

    title = None  # Temporary variable to store the current title
    for line in lines:
        line = line.strip()  # Remove extra spaces
        if line.endswith(":"):  # Line is a title
            if title:  # If a previous title exists without a description, add a placeholder
                notifications.append((title, "No description provided."))
            title = line[:-1]  # Remove the colon at the end
        elif line:  # Line is a description
            if title:  # If there's an active title, pair it with the description
                notifications.append((title, line))
                title = None  # Reset title after pairing
            else:  # If there's no title, skip this line (unexpected case)
                continue

    # Handle the last title without a description
    if title:
        notifications.append((title, "No description provided."))

    return notifications

def show_notification(title, message):
    """Display a notification with the given title and message."""
    notification.notify(
        title=f"{title}",
        message=message,
        app_name="JamAI Client",
        timeout=10,  # Notification duration in seconds
    )

if __name__ == "__main__":
    print("Sending text to JamAI...")
    jamai_response = send_request_and_get_output()

    print("Raw Response:")
    print(jamai_response)

    # Split the response into notifications
    notifications_queue = split_output_to_notifications(jamai_response)

    # Display each notification in the queue
    for title, description in notifications_queue:
        print(f"Displaying Notification - Title: {title}, Description: {description}")
        show_notification(title, description)
