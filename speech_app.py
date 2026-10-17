from datetime import datetime, timezone
import tempfile
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SecureCAI Speech", page_icon="🎙️", layout="wide")
GLOSSARY = pd.DataFrame([
    ["joint statement","البيان المشترك","Diplomatic","Approved","Use the approved institutional equivalent."],
    ["delegation","الوفد","Institutional","Approved","Confirm the delegation name in context."],
    ["representative","ممثل","Institutional","Approved","Verify rank and institutional role."],
    ["ceasefire","وقف إطلاق النار","Security","Approved","Check scope and legal or diplomatic context."],
    ["may","قد","Modality","Approved","Do not strengthen possibility into certainty."],
    ["must","يجب","Modality","Approved","Preserve obligation."],
], columns=["Source term","Approved Arabic","Domain","Control","Guidance"])
DEMO = "The delegation may review the updated joint statement at 1400. The representative must confirm whether the proposed ceasefire language is acceptable."

@st.cache_resource
def load_model(model_size):
    from faster_whisper import WhisperModel
    return WhisperModel(model_size, device="cpu", compute_type="int8")

def transcribe_audio(uploaded_file, model_size):
    suffix = Path(uploaded_file.name).suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(uploaded_file.getbuffer())
        audio_path = f.name
    model = load_model(model_size)
    segments, info = model.transcribe(audio_path, beam_size=5, vad_filter=True)
    rows, transcript_parts = [], []
    for segment in segments:
        text = segment.text.strip()
        transcript_parts.append(text)
        rows.append({"Start":round(segment.start,2), "End":round(segment.end,2), "Transcript":text})
    return " ".join(transcript_parts), pd.DataFrame(rows), info.language, info.language_probability

def glossary_matches(text):
    lower = text.lower()
    rows = [r.tolist() for _, r in GLOSSARY.iterrows() if r["Source term"].lower() in lower]
    return pd.DataFrame(rows, columns=GLOSSARY.columns)

def risk_scan(text):
    lower = text.lower()
    flags = []
    for term, category, severity, rationale in [
        ("may", "Modality", "High", "Possibility must not become certainty."),
        ("must", "Modality", "High", "Obligation must not be weakened."),
        ("not", "Negation", "Critical", "Polarity errors can reverse meaning."),
        ("ceasefire", "Sensitive terminology", "High", "Verify scope and institutional usage."),
    ]:
        if term in lower:
            flags.append([term, category, severity, rationale])
    if any(ch.isdigit() for ch in text):
        flags.append(["Number/time", "Numeric detail", "High", "Check digits, time zone, and delivery format."])
    return pd.DataFrame(flags, columns=["Trigger","Risk category","Severity","Why it matters"])

st.title("SecureCAI Speech")
st.caption("Speech transcription, terminology control, and human verification for high-stakes interpreting")
st.warning("Research prototype only. Use synthetic or institutionally approved non-sensitive audio. Do not upload classified, personal, operational, or confidential recordings.")

with st.sidebar:
    st.header("Assignment profile")
    st.selectbox("Language pair", ["English → Arabic"])
    st.selectbox("Context", ["Defence and diplomacy", "Strategic communication", "Training simulation"])
    model_size = st.selectbox("Whisper model", ["tiny.en", "base.en"], help="tiny.en is faster; base.en is generally more accurate but requires more memory.")
    st.divider()
    st.metric("Transcription mode", "Local Whisper")
    st.metric("Autonomous interpreting", "Disabled")

if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "segments" not in st.session_state:
    st.session_state.segments = pd.DataFrame()

st.subheader("1. Provide speech")
uploaded = st.file_uploader("Upload an English WAV, MP3, M4A, OGG, or WebM file", type=["wav","mp3","m4a","ogg","webm"])
demo_text = st.checkbox("Use synthetic demonstration text instead of audio")
if demo_text:
    transcript = DEMO
    segments = pd.DataFrame([{"Start":0.0,"End":8.0,"Transcript":DEMO}])
    detected_language, probability = "en", 1.0
elif uploaded:
    if st.button("Transcribe audio"):
        with st.spinner("Transcribing locally with Whisper. The first run may take longer while the model loads."):
            try:
                transcript, segments, detected_language, probability = transcribe_audio(uploaded, model_size)
                st.session_state.transcript = transcript
                st.session_state.segments = segments
                st.session_state.language = detected_language
                st.session_state.probability = probability
            except Exception as exc:
                st.error(f"Transcription failed: {exc}")
                st.info("Try a WAV file or use the synthetic demonstration.")
    transcript = st.session_state.transcript
    segments = st.session_state.segments
    detected_language = st.session_state.get("language", "")
    probability = st.session_state.get("probability", 0.0)
else:
    transcript, segments, detected_language, probability = "", pd.DataFrame(), "", 0.0

if transcript:
    st.subheader("2. Transcript verification")
    st.write(f"Detected language: **{detected_language}** | Model confidence estimate: **{probability:.2f}**")
    corrected = st.text_area("Edit the transcript before interpretation", value=transcript, height=150)
    st.dataframe(segments, hide_index=True, use_container_width=True)

    st.subheader("3. Terminology and risk analysis")
    matches, risks = glossary_matches(corrected), risk_scan(corrected)
    a,b,c = st.columns(3)
    a.metric("Glossary matches", len(matches))
    b.metric("Risk flags", len(risks))
    c.metric("High or critical flags", int(risks["Severity"].isin(["High","Critical"]).sum()) if not risks.empty else 0)
    tab1, tab2 = st.tabs(["Controlled terminology", "Risk flags"])
    with tab1:
        st.dataframe(matches, hide_index=True, use_container_width=True)
    with tab2:
        st.dataframe(risks, hide_index=True, use_container_width=True)
        st.info("A flag identifies a verification point. It does not determine the correct interpretation.")

    st.subheader("4. Interpreter rendering and decision")
    arabic = st.text_area("Enter the human or AI-assisted Arabic rendering", height=120)
    decision = st.selectbox("Overall professional decision", ["Pending","Accept","Edit","Reject","Escalate for specialist review"])
    rationale = st.text_area("Rationale for the decision", height=80)
    report = pd.DataFrame([{"timestamp_utc":datetime.now(timezone.utc).isoformat(),"detected_language":detected_language,"transcript":corrected,"arabic_rendering":arabic,"decision":decision,"rationale":rationale,"risk_flag_count":len(risks),"glossary_match_count":len(matches)}])
    st.download_button("Download anonymised review report", report.to_csv(index=False).encode("utf-8"), "securecai_speech_review.csv", "text/csv")
else:
    st.info("Upload an audio file and click Transcribe audio, or select Use synthetic demonstration text.")
