from datetime import datetime, timezone
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SecureCAI Booth Mode", page_icon="🎧", layout="wide")
GLOSSARY = {"joint statement":("البيان المشترك","Approved diplomatic term"),"delegation":("الوفد","Verify delegation identity"),"representative":("ممثل","Verify rank and institutional role"),"ceasefire":("وقف إطلاق النار","Check scope and context"),"may":("قد","Preserve possibility"),"must":("يجب","Preserve obligation")}
DEMO_SEGMENTS = ["The delegation may review the updated joint statement at 1400.","The representative must confirm whether the proposed ceasefire language is acceptable.","The delegation will report the outcome to the coordinating office."]

def analyse(segment):
    lower=segment.lower(); terms=[]; flags=[]
    for term,(arabic,note) in GLOSSARY.items():
        if term in lower: terms.append({"Term":term,"Approved equivalent":arabic,"Guidance":note})
    if any(ch.isdigit() for ch in segment): flags.append({"Priority":"HIGH","Trigger":"Number or time","Action":"Verify digits, time zone, and delivery format."})
    if "may" in lower: flags.append({"Priority":"HIGH","Trigger":"Modality: may","Action":"Do not strengthen possibility into certainty."})
    if "must" in lower: flags.append({"Priority":"HIGH","Trigger":"Modality: must","Action":"Preserve obligation."})
    if "not" in lower: flags.append({"Priority":"CRITICAL","Trigger":"Negation","Action":"Check polarity before delivery."})
    if "ceasefire" in lower: flags.append({"Priority":"HIGH","Trigger":"Sensitive terminology","Action":"Verify scope and institutional context."})
    return pd.DataFrame(terms),pd.DataFrame(flags)

if "segment_index" not in st.session_state: st.session_state.segment_index=0
if "history" not in st.session_state: st.session_state.history=[]

st.title("SecureCAI Booth Mode")
st.caption("Silent interpreter support: rolling transcript, terminology retrieval, risk awareness, and human control")
st.warning("Demonstration mode. Use synthetic or approved non-sensitive material only. The system does not speak or deliver an interpretation automatically.")

with st.sidebar:
    st.header("Booth controls")
    mode=st.radio("Input mode",["Simulation","Manual segment"])
    st.selectbox("Language pair",["English → Arabic"])
    st.selectbox("Context",["Defence and diplomacy","Strategic communication","Institutional briefing"])
    st.divider(); st.metric("Audio output","Interpreter only"); st.metric("Autonomous delivery","OFF")
    offline=st.toggle("Emergency offline mode",value=False)
    st.caption("Offline mode leaves only the local glossary and manual notes available.")

st.subheader("Booth status")
a,b,c,d=st.columns(4); a.metric("Connection","Local" if offline else "Ready"); b.metric("Transcript delay","Manual" if mode=="Manual segment" else "Simulation"); c.metric("Current segment",st.session_state.segment_index+1); d.metric("Risk alerts","Review" if st.session_state.history else "None")

if mode=="Simulation":
    segment=DEMO_SEGMENTS[st.session_state.segment_index % len(DEMO_SEGMENTS)]
    col1,col2=st.columns([1.4,1])
    with col1:
        st.subheader("Rolling transcript"); st.info(segment); st.caption("A future microphone-enabled version would update this area from local speech recognition.")
    with col2:
        st.subheader("Interpreter notes"); st.text_area("Private notes",height=100,key="notes_"+str(st.session_state.segment_index))
        st.button("Next segment",on_click=lambda:st.session_state.update(segment_index=st.session_state.segment_index+1))
else:
    segment=st.text_area("Enter the current source segment",height=120,placeholder="Paste a synthetic segment to simulate the booth feed.")
    if st.button("Analyse current segment"): st.session_state.history.append({"segment":segment,"time":datetime.now(timezone.utc).isoformat()})

if segment:
    terms,flags=analyse(segment); left,right=st.columns([1,1])
    with left:
        st.subheader("Terminology panel")
        if offline: st.caption("Local glossary only")
        if terms.empty: st.success("No glossary match detected.")
        else: st.dataframe(terms,hide_index=True,use_container_width=True)
    with right:
        st.subheader("Risk panel")
        if flags.empty: st.success("No rule-based risk flag detected.")
        else: st.dataframe(flags,hide_index=True,use_container_width=True); st.error("Professional verification required before relying on any flagged item.")
    st.subheader("Interpreter action")
    action=st.radio("Decision for this segment",["Continue","Mark for review","Escalate","Stop assistance"],horizontal=True)
    interpretation=st.text_area("Arabic interpretation or post-session reconstruction",height=100)
    if st.button("Record segment decision"):
        st.session_state.history.append({"segment":segment,"action":action,"interpretation":interpretation,"risk_flags":len(flags),"timestamp_utc":datetime.now(timezone.utc).isoformat()}); st.success("Segment decision recorded.")

with st.expander("Post-session review"):
    if st.session_state.history:
        log=pd.DataFrame(st.session_state.history); st.dataframe(log,hide_index=True,use_container_width=True)
        st.download_button("Download booth review log",log.to_csv(index=False).encode("utf-8"),"securecai_booth_review.csv","text/csv")
    else: st.info("No booth decisions recorded yet.")
