# SecureCAI Live Booth

This is an experimental live microphone version of SecureCAI. It receives browser audio, transcribes short windows with a local Whisper model, and displays a rolling transcript with terminology and risk alerts.

## Run

    pip install -r requirements-live.txt
    streamlit run live_app.py

## Use

1. Open the app in a browser with microphone permission.
2. Click Start on the microphone component.
3. Speak in short English segments.
4. Review the rolling transcript.
5. Inspect terminology and risk alerts.
6. Record the interpreter's decision and Arabic notes.

## Limitations

This is not an operational booth system. Short-window transcription may introduce latency, duplicate text, dropped segments, or recognition errors. Names, numbers, accents, and specialist terminology require human verification. The current prototype uses the Whisper tiny.en model and CPU processing.

For institutional deployment, audio processing should occur in an approved local environment with security review, retention controls, failure recovery, and professional interpreter testing.
