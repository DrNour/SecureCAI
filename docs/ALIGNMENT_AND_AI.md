# Alignment and AI translation

SecureTerm Pro AI adds segment alignment and candidate Arabic translation.

## Features

- splits the briefing into source segments;
- identifies controlled terms in each segment;
- creates a transparent termbase-based candidate rendering;
- optionally calls a configured AI model through OPENAI_API_KEY;
- displays source segment, key terms, candidate Arabic, method, review status, and reviewer notes in one aligned table;
- exports an alignment report;
- generates verification questions for unresolved or unaccepted items.

The AI candidate remains provisional. The professional validates terminology, register, institutional meaning, and contextual appropriateness.

## Optional AI configuration

Add OPENAI_API_KEY and optionally OPENAI_MODEL to Streamlit secrets. If no key is provided, the application uses the transparent controlled-termbase method and labels it clearly.
