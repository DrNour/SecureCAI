import io, wave, tempfile
from datetime import datetime, timezone
import av
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_webrtc import WebRtcMode, webrtc_streamer

st.set_page_config(page_title="SecureCAI Live Booth", page_icon="🎙️", layout="wide")
GLOSSARY={"joint statement":("البيان المشترك","Approved diplomatic term"),"delegation":("الوفد","Verify delegation identity"),"representative":("ممثل","Verify rank and institutional role"),"ceasefire":("وقف إطلاق النار","Check scope and context"),"may":("قد","Preserve possibility"),"must":("يجب","Preserve obligation")}
@st.cache_resource
def load_model():
    from faster_whisper import WhisperModel
    return WhisperModel("tiny.en",device="cpu",compute_type="int8")
def to_wav(samples,rate):
    samples=np.asarray(samples)
    if samples.ndim>1:samples=samples.mean(axis=1)
    pcm=np.clip(samples,-1,1)
    pcm=(pcm*32767).astype(np.int16)
    out=io.BytesIO()
    with wave.open(out,"wb") as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(rate);wf.writeframes(pcm.tobytes())
    return out.getvalue()
def transcribe(samples,rate):
    model=load_model()
    with tempfile.NamedTemporaryFile(suffix=".wav",delete=False) as f:
        f.write(to_wav(samples,rate));path=f.name
    segments,_=model.transcribe(path,beam_size=3,vad_filter=True)
    return " ".join(s.text.strip() for s in segments).strip()
def analyse(text):
    low=text.lower();terms=[];flags=[]
    for term,(ar,note) in GLOSSARY.items():
        if term in low:terms.append({"Term":term,"Approved equivalent":ar,"Guidance":note})
    if any(ch.isdigit() for ch in text):flags.append(["HIGH","Number/time","Verify digits, time zone, and delivery format."])
    if "may" in low:flags.append(["HIGH","Modality: may","Preserve possibility."])
    if "must" in low:flags.append(["HIGH","Modality: must","Preserve obligation."])
    if "not" in low:flags.append(["CRITICAL","Negation","Check polarity."])
    if "ceasefire" in low:flags.append(["HIGH","Sensitive terminology","Verify scope and context."])
    return pd.DataFrame(terms),pd.DataFrame(flags,columns=["Priority","Trigger","Action"])
st.title("SecureCAI Live Booth")
st.caption("Experimental live microphone support with local speech recognition")
st.warning("Use synthetic or approved non-sensitive speech only. This is not an operational interpreting system.")
if "transcript" not in st.session_state:st.session_state.transcript=""
if "last_audio" not in st.session_state:st.session_state.last_audio=b""
st_autorefresh(interval=3000,key="audio_poll")
ctx=webrtc_streamer(key="securecai-live-fixed",mode=WebRtcMode.RECVONLY,audio_receiver_size=1024,media_stream_constraints={"audio":True,"video":False},async_processing=True)
st.write("1. Click Start, allow microphone access, then speak in short English segments.")
if ctx.state.playing:
    try:
        frames=ctx.audio_receiver.get_frames(timeout=1)
        if frames:
            arrays=[];rate=None
            for frame in frames:
                arr=frame.to_ndarray()
                if arr.ndim==2:arr=arr.mean(axis=0)
                arrays.append(arr.astype(np.float32)/max(float(np.max(np.abs(arr))),1.0));rate=frame.sample_rate
            if arrays and rate:
                text=transcribe(np.concatenate(arrays),rate)
                if text:st.session_state.transcript=(st.session_state.transcript+" "+text).strip()
    except Exception as exc:
        st.caption("Waiting for an audio batch: "+str(exc))
st.subheader("2. Rolling transcript")
edited=st.text_area("Review and correct the transcript",value=st.session_state.transcript,height=150)
if edited!=st.session_state.transcript:st.session_state.transcript=edited
terms,flags=analyse(st.session_state.transcript)
a,b,c=st.columns(3);a.metric("Transcript words",len(st.session_state.transcript.split()));b.metric("Terminology matches",len(terms));c.metric("Risk flags",len(flags))
left,right=st.columns(2)
with left:
    st.subheader("Terminology alerts")
    st.dataframe(terms,hide_index=True,use_container_width=True) if not terms.empty else st.success("No match detected.")
with right:
    st.subheader("Risk alerts")
    st.dataframe(flags,hide_index=True,use_container_width=True) if not flags.empty else st.success("No flag detected.")
st.subheader("3. Interpreter decision")
arabic=st.text_area("Arabic interpretation or notes",height=100)
decision=st.selectbox("Decision",["Continue","Mark for review","Escalate","Stop assistance"])
if st.button("Save review snapshot"):
    report=pd.DataFrame([{"timestamp_utc":datetime.now(timezone.utc).isoformat(),"transcript":st.session_state.transcript,"arabic_notes":arabic,"decision":decision,"risk_flags":len(flags)}])
    st.download_button("Download snapshot",report.to_csv(index=False).encode("utf-8"),"securecai_live_snapshot.csv","text/csv")
