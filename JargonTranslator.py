import pyaudio
from faster_whisper import WhisperModel
import numpy as np
import requests
from plyer import notification
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

#retreive the api keys from the .env file
PROJECT_ID = os.getenv("PROJECT_ID")
API_KEY = os.getenv("API_KEY")
TABLE_ID = os.getenv("TABLE_ID")

# Constants for audio recording
SAMPLE_RATE = 16000  # Whisper works well with 16kHz audio
CHANNELS = 1         # Mono audio reduces processing load
CHUNK_SIZE = 1024    # Frames per buffer
BUFFER_DURATION = 10  # Process every 10 seconds
LOOPBACK_DEVICE_INDEX = 1  # Replace with your Stereo Mix index

# JamAI API Configuration
API_URL = "https://api.jamaibase.com/api/v1/gen_tables/action/rows/add"
API_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": "Bearer " + API_KEY,
    "X-PROJECT-ID": PROJECT_ID,
}

def send_to_jamai(input_text):
    """Send transcription to JamAI API and return the response."""
    payload = {
        "data": [{"input": input_text}],
        "table_id": TABLE_ID,
        "stream": False,
    }
    try:
        response = requests.post(API_URL, json=payload, headers=API_HEADERS)
        response.raise_for_status()  # Raise an error for bad status codes
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
        title=title,
        message=message,
        app_name="JamAI Client",
        timeout=10,  # Notification duration in seconds
    )

def live_transcription():
    """Capture system audio, transcribe it, send to API, and display notifications."""
    print("Loading Whisper model...")
    model = WhisperModel("tiny", device="cpu")  # Use "tiny" for speed

    # NOTE: If you have a GPU, you can use "cuda" for faster processing(replace "cpu" with "cuda")
    
    print("Model loaded.")

    # Initialize PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
        input_device_index=LOOPBACK_DEVICE_INDEX,
    )
    print("Live transcription started. Press Ctrl+C to stop.")

    # Buffer for audio data
    audio_buffer = b""

    try:
        while True:
            # Read audio data from the stream
            audio_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_buffer += audio_data

            # Process transcription when buffer is full
            if len(audio_buffer) >= SAMPLE_RATE * CHANNELS * BUFFER_DURATION * 2:
                # Convert buffer to NumPy array
                audio_np = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0

                # Transcribe with reduced beam size for faster output
                transcription = ""
                segments, _ = model.transcribe(audio_np, beam_size=1)
                for segment in segments:
                    transcription += segment.text + " "

                print(f"Transcription: {transcription.strip()}")
                
                if transcription.strip() and transcription.strip() != "." and transcription.strip() != "" and transcription.strip() != " ":
                    
                    # Send transcription to JamAI API
                    api_response = send_to_jamai(transcription.strip())
                    print(f"API Response: {api_response}")

                    # Split API response into notifications
                    notifications = split_output_to_notifications(api_response)

                    # Display each notification
                    for title, description in notifications:
                        print(f"Displaying Notification - Title: {title}, Description: {description}")
                        show_notification(title, description)                 
                else:
                    print("No transcription, skipping API call.")

                # Clear buffer
                audio_buffer = b""

    except KeyboardInterrupt:
        print("\nTranscription stopped.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    live_transcription()
