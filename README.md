# JargonTranslator

## Overview
**JargonTranslator** is a tool for **real-time transcription** and **jargon translation**. It listens to system audio, transcribes it, and uses **JamAI** to explain technical terms or jargon in the transcription. The results are displayed as desktop notifications.

## Features
- **Live Transcription**: Captures system audio and transcribes it in real time using FastWisper.
- **JamAI API Integration**: Sends transcription to JamAI for jargon explanations.
- **Notifications**: Displays jargon explanations as title-description desktop notifications.
- **Secure Configuration**: Stores sensitive information in a `.env` file.

---

## Setup

### 0. Setup your JamAI Base Project
- follow step 1(only) of the tutorial [here](https://docs.jamaibase.com/getting-started/quick-start/reactjs)
- next create a new table with 2 collum:
1. input
2. Output

you must have the table like so:
![image](https://github.com/user-attachments/assets/b55177d8-f254-44d0-863a-b4f4ed08edd2)


### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/JargonTranslator.git
cd JargonTranslator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure `.env`
Create a file named `.env` in the project folder and add:
```plaintext
JAMAI_API_URL=https://api.jamaibase.com/api/v1/gen_tables/action/rows/add
JAMAI_API_KEY=your_jamai_api_key
JAMAI_PROJECT_ID=your_project_id
```

## 4. Configure faster-whisper
follow the tutorial [here](https://github.com/SYSTRAN/faster-whisper)

### 5. Install PyAudio
#### Windows:
```bash
pip install pipwin
pipwin install pyaudio
```

#### macOS:
```bash
brew install portaudio
pip install pyaudio
```

#### Linux:
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

---

## Usage

1. Run the main script:
```bash
python main.py
```

2. The script will:
   - Transcribe system audio in 10-second chunks.
   - Send the transcription to JamAI for jargon explanations.
   - Display the results as desktop notifications.

---

## Troubleshooting

1. **Stereo Mix Issues**:
   - Ensure **Stereo Mix** is enabled (Windows users).
   - Update `LOOPBACK_DEVICE_INDEX` in the script if needed.

2. **API Issues**:
   - Double-check your `.env` file for correct API credentials.

3. **Notifications**:
   - Long titles will be truncated to avoid errors.

---

## Example Output
- **Notification Title**: Artificial Intelligence (AI)
- **Notification Message**: Computer science that enables machines to think and learn like humans.
---
**Author**: Tareq Adam  
**GitHub**: [Tareq0267](https://github.com/Tareq0267)
---
