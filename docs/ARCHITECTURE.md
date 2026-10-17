# SecureCAI architecture

## Prototype layers

1. **Input layer**: synthetic passage or approved non-sensitive material.
2. **Terminology layer**: controlled English–Arabic glossary with domain and guidance fields.
3. **Risk layer**: transparent rules for modality, negation, numbers, names, and sensitive terms.
4. **Human decision layer**: accept, edit, reject, or escalate.
5. **Evidence layer**: anonymised session logs and downloadable review reports.

## Planned research extensions

- replace rule-based matching with evaluated NLP components;
- add local speech-to-text only after security review;
- version glossaries and record provenance;
- compare expert and novice verification behaviour;
- add segment-level quality and cognitive-load measures;
- publish a reproducible benchmark using synthetic and de-identified data.

## Explicit boundary

SecureCAI is a decision-support and research platform. It is not an autonomous interpreting system and should not be represented as an operational defence capability.
