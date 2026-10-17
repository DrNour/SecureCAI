# Speech transcription workflow

SecureCAI Speech adds local audio transcription to the human-in-the-loop workflow.

## Run locally

    pip install -r requirements-speech.txt
    streamlit run speech_app.py

## Workflow

1. Upload a synthetic or approved non-sensitive audio file.
2. Select the Whisper model.
3. Click Transcribe audio.
4. Review and correct the transcript.
5. Inspect terminology matches and risk flags.
6. Enter the Arabic rendering.
7. Accept, edit, reject, or escalate the interpretation.
8. Download the anonymised review report.

## Model choice

- tiny.en is faster and lighter for demonstrations.
- base.en is generally more accurate but requires more memory.

The first run downloads the selected model. The application processes the audio locally through Whisper in the Python environment. This prototype does not provide live microphone transcription and does not perform autonomous interpreting.

## Security boundary

Do not upload classified, personal, operational, or confidential recordings. Institutional deployment requires a security review, retention policy, access control, and an approved processing environment.
