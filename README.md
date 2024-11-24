# JargonTranslator

## Overview
**JargonTranslator** is a tool for **real-time transcription** and **jargon translation**. It listens to system audio, transcribes it, and uses **JamAI** to explain technical terms or jargon in the transcription. The results are displayed as desktop notifications.

## Features
- **Live Transcription**: Captures system audio and transcribes it in real time using FastWisper.
- **JamAI API Integration**: Sends transcription to JamAI for jargon explanations.
- **Notifications**: Displays jargon explanations as title-description desktop notifications.
- **Secure Configuration**: Stores sensitive information in a `.env` file.

---
## Models and Technologies Used

1. **[Faster-Whisper](https://github.com/guillaumekln/faster-whisper)**:
   - A fast implementation of OpenAI's Whisper model for audio transcription.
   - Used the `tiny` model for optimized speed.

2. **[JamAI Base](https://www.jamaibase.com/)**:
   - Retrieval-Augmented Generation (RAG) system that provides insights and jargon explanations.
   - Utilizes advanced LLMs like `Meta Llama-3.1-70B-Instruct`.

3. **[Plyer](https://github.com/kivy/plyer)**:
   - Cross-platform library for displaying desktop notifications.

4. **[PyAudio](https://people.csail.mit.edu/hubert/pyaudio/)**:
   - Captures system audio for transcription.

5. **[Python-Dotenv](https://github.com/theskumar/python-dotenv)**:
   - Manages environment variables securely.

---

## Setup

### 1. Setup your JamAI Base Project
- follow step 1(only) of the tutorial [here](https://docs.jamaibase.com/getting-started/quick-start/reactjs)
- next create a new table with 2 collum:
1. input
2. Output

you must have the table like so:
![image](https://github.com/user-attachments/assets/b55177d8-f254-44d0-863a-b4f4ed08edd2)

setup the Output cell like so:
```
Table name: "your_table_id"

input: ${input}

search within the input where NON-Laymen terms and give a brief explanation on what they are.keep it short and precise.IF THERE ARE NONE THEN RETURN NOTHING (" ").the maximum length of a title is 64 characters. follow this format:
word:
explanation...


Remember to act as a cell in a spreadsheet and provide concise, relevant information without explanations unless specifically requested.
DONT ADD UNECESSARY INFORMATION LIKE:
" Here are the non-laymen terms with brief explanations:","Let me know if you'd like me to expand on any of these terms!","Description:"
just output the non-laymen term and its explanation 
```

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/JargonTranslator.git
cd JargonTranslator
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure `.env`
Create a file named `.env` in the project folder and add:
```plaintext
API_KEY=your_jamai_api_key
PROJECT_ID=your_project_id
TABLE_ID=your_table_id

```

## 5. Configure faster-whisper
follow the tutorial [here](https://github.com/SYSTRAN/faster-whisper)

### 6. Install PyAudio
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

1. Run the script:
```bash
python JargonTranlator.py
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
