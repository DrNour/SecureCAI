# SecureCAI Booth Mode

Booth Mode presents SecureCAI as a silent interpreter assistant rather than an autonomous interpreting system.

## Run

    streamlit run booth_app.py

## Workshop demonstration

1. Open Booth Mode.
2. Keep the language pair as English to Arabic.
3. Select Simulation.
4. Read the rolling transcript as if it were arriving from the speaker.
5. Inspect the terminology and risk panels.
6. Ask the interpreter to decide whether to continue, mark for review, escalate, or stop assistance.
7. Use Next segment to continue the simulated assignment.
8. Open Post-session review and download the booth review log.

## Design principles

- The interpreter hears the speaker through the normal booth audio system.
- SecureCAI provides silent visual support on a separate screen.
- The application never speaks the translation automatically.
- High-risk terms remain the interpreter's responsibility.
- Emergency offline mode leaves the local glossary and manual notes available.
- The first version uses simulation/manual input. A future version can add local microphone capture and low-latency speech recognition after testing.

## Future live-booth extension

A production-oriented extension would require local audio capture, segmentation, latency monitoring, speaker identification, terminology shortcuts, local model optimisation, failure recovery, and institutional security approval. It must be evaluated with professional interpreters before operational use.
