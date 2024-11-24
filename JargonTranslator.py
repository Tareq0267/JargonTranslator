import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import keyboard
import pyautogui
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import ctypes
recognizer = None
is_transcribing = None
transcription_mode = None

# Function to initialize the Azure Speech SDK >>>>>>>>>>>
def init():
    global recognizer
    global is_transcribing
    global transcription_mode

    print("Initializing...")
    # Load environment variables from .env file
    load_dotenv()

    # Get API keys from environment variables >>>>>>>>>>>
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    service_region = os.getenv("AZURE_REGION")

    if not speech_key or not service_region:
        raise ValueError("API keys are missing!")

    # Configure Azure Speech SDK
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "en-AU"

    is_transcribing = False
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    # Prompt user to choose transcription mode
    print("Press 'Ctrl+C' to exit")
    mode = input("Choose transcription mode (1: Continuous, 2: One-shot): ").strip()
    if mode == '1':
        transcription_mode = 'continuous'
        print("Press 'F2' to start or stop continuous transcription")
    elif mode == '2':
        transcription_mode = 'one_shot'
        print("Press 'F2' to start a one-shot transcription")
    else:
        print("Invalid choice. Exiting...")
        return


# Function to mute/unmute system volume using pycaw >>>>>>>>>>>
def mute_system_volume(mute=True):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
    volume.SetMute(1 if mute else 0, None)


# Function to type text using pyautogui >>>>>>>>>>>
def type_text(text):
    pyautogui.write(text)


# Function to start transcription >>>>>>>>>>>
def start_transcription():  
    global recognizer
    global is_transcribing
    global transcription_mode
    print("Starting transcription...\n")
    print("Switch to the target window\r\n")
    transcribe_and_type(recognizer)


# Function to stop transcription >>>>>>>>>>>
def end_transcription():
    global recognizer
    global is_transcribing
    global transcription_mode

    print("Stopping transcription...\n")
    if transcription_mode == 'continuous':
        recognizer.stop_continuous_recognition_async()
        print("Press 'F2' to start or stop continuous transcription")
    elif transcription_mode == 'one_shot':
        print("Press 'F2' to start a one-shot transcription")

    mute_system_volume(mute=False)  # Unmute the system volume
    is_transcribing = False
    print("Press 'F2' to start transcription")


# Function to perform transcription >>>>>>>>>>>
def transcribe_and_type(recognizer):
    global transcription_mode
    # Set up microphone for real-time transcription
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    
    # Function to process transcription results >>>>>>>>>>>
    def recognized(evt):
        
        new_text = evt.result.text + " "  # Add a space at the end
        print(f"> {new_text}")  # Log it to the console
        type_text(new_text)

        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Recognized: {}".format(evt.result.text))
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print("No speech could be recognized: {}".format(evt.result.no_match_details))
        elif evt.result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = evt.result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
        # if new_text is empty, warn the user and stop the transcription
        if not evt.result.text:
            print("No speech detected. Stopping transcription.")
            end_transcription()
            return


    # Track if the event handler has been connected 
    if not hasattr(recognizer, 'handler_connected'):
        recognizer.recognized.connect(recognized)
        recognizer.handler_connected = True  # Flag indicating handler is connected

    # Mute system volume
    mute_system_volume(mute=True)

    # Start transcription based on the chosen mode
    if transcription_mode == 'continuous':
        recognizer.start_continuous_recognition_async()
        is_transcribing = True
    elif transcription_mode == 'one_shot':
        recognizer.recognize_once()
        end_transcription()


# Main function >>>>>>>>>>>
def main():
    global is_transcribing
    init()

    # Main loop for listening to hotkeys
    try:
        while True:
            # Wait for F2 key press
            keyboard.wait("F2")  # Blocks until F2 is pressed
            if not is_transcribing:
                 start_transcription()
            else:
                end_transcription()

    except KeyboardInterrupt:
        # Gracefully handle Ctrl+C and stop transcription
        if is_transcribing:
            end_transcription()

        print("Exiting...")
        exit(0)

# Entry point
if __name__ == "__main__":
    main()
