import speech_recognition as sr

def transcribe_audio():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    print("Calibrating microphone... Please wait.")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=3)
        print(f"Microphone calibrated with ambient noise level: {recognizer.energy_threshold}")

    print("Listening for audio. Press Ctrl+C to stop.")
    try:
        with microphone as source:
            while True:
                print("Listening...")
                try:
                    # Capture audio from the microphone
                    audio = recognizer.listen(source)
                    print("Transcribing...")
                    
                    # Use Google's Web Speech API for transcription
                    transcription = recognizer.recognize_google(audio)
                    print(f"Transcription: {transcription}")
                    
                    # Here you can send the transcription to JamAI Base's API
                    # Example: send_to_jamai_base(transcription)

                except sr.UnknownValueError:
                    print("Could not understand audio.")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")
    except KeyboardInterrupt:
        print("\nExiting.")
        return

# Example function to send transcription to JamAI Base (modify based on your API setup)
def send_to_jamai_base(transcription):
    import requests

    # Replace with your JamAI Base REST API endpoint
    jamai_base_url = "https://your-jamai-base-api-endpoint.com/add-transcription"
    payload = {"transcription": transcription}
    headers = {"Content-Type": "application/json"}

    response = requests.post(jamai_base_url, json=payload)
    if response.status_code == 200:
        print("Transcription successfully sent to JamAI Base.")
    else:
        print(f"Failed to send transcription. Status code: {response.status_code}")

if __name__ == "__main__":
    transcribe_audio()
