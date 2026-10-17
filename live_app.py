import io
import wave
from datetime import datetime, timezone
import av
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

st.set_page_config(page_title="SecureCAI Live Booth", page_icon="🎙️", layout="wide")

GLOSSARY = {
    "joint statement": ("البيان المشترك", "Approved diplomatic term"),
    "delegation": ("الوفد", "Verify delegation identity"),
    "representative": ("ممثل", "Verify rank and institutional role"),
    "ceasefire": ("وقف إطلاق النار", "Check scope and context"),
    "may": ("قد", "Preserve possibility"),
    "must": ("يجب", "Preserve obligation"),
}

@st.cache_resource
def load_model():
    from faster_whisper import WhisperModel
    return WhisperModel("tiny.en", device="cpu", compute_type="int8")

def wav_bytes(samples, sample_rate):
    samples = np.asarray(samples)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    samples = np.clip(samples, -1, 1)
    pcm = (samples * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()

def transcribe(samples, sample_rate):
    model = load_model()
    segments, _ = model.transcribe(io.BytesIO(wav_bytes(samples, sample_rate)), beam_size=3, vad_filter=True)
    return " ".join(s.text.strip() for s in segments).strip()

def analyse(text):
    lower = text.lower()
    terms = [{"Term":t,"Approved equivalent":v[0],"Guidance":v[1]} for t,v in GLOSSARY.items() if t in lower]
    flags = []
    if any(ch.isdigit() for ch in text): flags.append(["HIGH","Number/time","Verify digits, time zone, and delivery format."])
    if "may" in lower: flags.append(["HIGH","Modality: may","Preserve possibility."])
    if "must" in lower: flags.append(["HIGH","Modality: must","Preserve obligation."])
    if "not" in lower: flags.append(["CRITICAL","Negation","Check polarity before delivery."])
    if "ceasefire" in lower: flags.append(["HIGH","Sensitive terminology","Verify scope and context."])
    return pd.DataFrame(terms), pd.DataFrame(flags, columns=["Priority","Trigger","Action"])

st.title("SecureCAI Live Booth")
st.caption("Experimental live microphone support with local speech recognition")
st.warning("Experimental research prototype. Use synthetic or approved non-sensitive speech only. Do not use classified or operational audio.")

with st.sidebar:
    st.header("Live controls")
    st.selectbox("Language pair", ["English → Arabic"])
    st.selectbox("Context", ["Defence and diplomacy", "Strategic communication", "Training simulation"])
    st.metric("Transcription model", "Whisper tiny.en")
    st.metric("Autonomous delivery", "OFF")
    st.caption("The interpreter remains responsible for the delivered interpretation.")

if "live_transcript" not in st.session_state:
    st.session_state.live_transcript = ""
if "last_terms" not in st.session_state:
    st.session_state.last_terms = pd.DataFrame()
if "last_flags" not in st.session_state:
    st.session_state.last_flags = pd.DataFrame()

st.subheader("1. Microphone input")
st.write("Allow microphone access, start the stream, and speak in short segments. The system processes short audio windows and appends recognised text.")
ctx = webrtc_streamer(
    key="securecai-live",
    mode=WebRtcMode.RECVONLY,
    audio_receiver_size=1024,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

if ctx.state.playing:
    st.info("Live capture is active. Speak clearly in short segments.")
    try:
        frames = ctx.audio_receiver.get_frames(timeout=1)
        if frames:
            arrays, rate = [], None
            for frame in frames:
                arr = frame.to_ndarray()
                if arr.ndim == 2:
                    arr = arr.mean(axis=0)
                arrays.append(arr.astype(np.float32) / max(np.max(np.abs(arr)), 1))
                rate = frame.sample_rate
            if arrays and rate:
                text = transcribe(np.concatenate(arrays), rate)
                if text:
                    st.session_state.live_transcript = (st.session_state.live_transcript + " " + text).strip()
                    st.session_state.last_terms, st.session_state.last_flags = analyse(text)
    except Exception as exc:
        st.warning(f"Waiting for audio: {exc}")

st.subheader("2. Rolling transcript")
edited = st.text_area("Review or correct the transcript", value=st.session_state.live_transcript, height=150)
if edited != st.session_state.live_transcript:
    st.session_state.live_transcript = edited
    st.session_state.last_terms, st.session_state.last_flags = analyse(edited)

a,b,c = st.columns(3)
a.metric("Transcript words", len(st.session_state.live_transcript.split()))
b.metric("Terminology matches", len(st.session_state.last_terms))
c.metric("Risk flags", len(st.session_state.last_flags))

left, right = st.columns(2)
with left:
    st.subheader("Terminology alerts")
    if st.session_state.last_terms.empty: st.success("No terminology match detected.")
    else: st.dataframe(st.session_state.last_terms, hide_index=True, use_container_width=True)
with right:
    st.subheader("Risk alerts")
    if st.session_state.last_flags.empty: st.success("No risk flag detected.")
    else:
        st.dataframe(st.session_state.last_flags, hide_index=True, use_container_width=True)
        st.error("Human verification required.")

st.subheader("3. Interpreter action")
arabic = st.text_area("Arabic interpretation or notes", height=100)
decision = st.selectbox("Decision", ["Continue","Mark for review","Escalate","Stop assistance"])
if st.button("Save live review snapshot"):
    snapshot = pd.DataFrame([{"timestamp_utc":datetime.now(timezone.utc).isoformat(),"transcript":st.session_state.live_transcript,"arabic_notes":arabic,"decision":decision,"risk_flags":len(st.session_state.last_flags)}])
    st.download_button("Download snapshot", snapshot.to_csv(index=False).encode("utf-8"), "securecai_live_snapshot.csv", "text/csv")
