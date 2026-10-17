# SecureCAI

**Secure Computer-Assisted Interpreting for high-stakes institutional settings**

SecureCAI is a research prototype for human-in-the-loop English–Arabic interpreting support. It is designed for demonstration, teaching, and research with synthetic or approved non-sensitive material.

## What the prototype does

- Loads a small, controlled English–Arabic terminology glossary.
- Analyses a briefing passage for glossary terms, names, numbers, negation, modality, and uncertainty.
- Displays candidate Arabic equivalents with transparent risk flags.
- Requires the interpreter to accept, edit, or reject each candidate.
- Records decisions in an auditable review table.
- Exports a CSV review report.

## What it does not do

SecureCAI is not an autonomous interpreter and must not be used with classified, personal, operational, or otherwise sensitive information. It does not guarantee accuracy, determine speaker intent, or replace professional judgement.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Research questions

The prototype can support future studies of terminology consistency, interpreter verification behaviour, time, correction patterns, perceived trust, and the relationship between AI assistance and professional judgement.

## Roadmap

1. Controlled glossary management
2. Risk flagging and human verification
3. Synthetic evaluation tasks
4. Optional approved speech-to-text integration
5. Anonymised interaction analytics
6. Institutional security review before any real deployment
