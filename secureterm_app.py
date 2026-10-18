import io, re, csv
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SecureTerm Pro", page_icon="📚", layout="wide")

DEFAULT_TERMS = pd.DataFrame([
    ["joint statement","البيان المشترك","Diplomatic","Approved","Use the institutional equivalent in formal statements."],
    ["delegation","الوفد","Institutional","Approved","Confirm the delegation identity in the briefing."],
    ["representative","ممثل","Institutional","Needs verification","Check rank and institutional role."],
    ["ceasefire","وقف إطلاق النار","Security","Approved","Verify scope and contextual use."],
    ["rules of engagement","قواعد الاشتباك","Security","Needs verification","Confirm authorised institutional wording."],
    ["strategic communication","الاتصال الاستراتيجي","Defence","Approved","Keep register formal and institutional."],
], columns=["Source term","Arabic equivalent","Domain","Status","Context note"])

def extract_text(uploaded):
    name=uploaded.name.lower()
    data=uploaded.getvalue()
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    if name.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
    return ""

def extract_items(text):
    sentences=[s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    numbers=sorted(set(re.findall(r"\b\d+(?:[:.]\d+)?\b", text)))
    acronyms=sorted(set(re.findall(r"\b[A-Z]{2,}(?:\s[A-Z]{2,})*\b", text)))
    entities=sorted(set(re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3}\b", text)))
    return sentences,numbers,acronyms,entities

def term_matches(text, termbase):
    low=text.lower()
    rows=[]
    for _,r in termbase.iterrows():
        if r["Source term"].lower() in low:
            rows.append(r.to_dict())
    return pd.DataFrame(rows, columns=termbase.columns)

st.title("SecureTerm Pro")
st.caption("AI-assisted briefing and terminology workspace for professional English–Arabic interpreting and translation")
st.warning("Research prototype. Use synthetic or institutionally approved non-sensitive documents. Do not upload classified or confidential material.")

with st.sidebar:
    st.header("Project controls")
    project=st.text_input("Project or assignment name","Strategic briefing")
    domain=st.selectbox("Domain",["Defence and diplomacy","Strategic communication","Institutional translation","Training simulation"])
    st.caption("The professional validates all terminology before use.")

if "termbase" not in st.session_state:
    st.session_state.termbase=DEFAULT_TERMS.copy()
if "briefing_text" not in st.session_state:
    st.session_state.briefing_text=""

left,right=st.columns([1.15,1])
with left:
    st.subheader("1. Briefing corpus")
    files=st.file_uploader("Upload TXT, DOCX, or PDF briefing files", type=["txt","docx","pdf"], accept_multiple_files=True)
    if files and st.button("Extract briefing content"):
        chunks=[]
        for f in files:
            chunks.append(f"\n\n--- "+f.name+" ---\n"+extract_text(f))
        st.session_state.briefing_text="".join(chunks)
    text=st.text_area("Review or paste approved briefing text", value=st.session_state.briefing_text, height=260)
    st.session_state.briefing_text=text
    if st.button("Load synthetic briefing"):
        st.session_state.briefing_text=("The delegation will review the joint statement during the strategic communication briefing. "
        "The representative will discuss the proposed ceasefire language and the rules of engagement. "
        "The National Coordination Office will issue an updated position at 1400.")
        st.rerun()

with right:
    st.subheader("2. Project termbase")
    edited=st.data_editor(st.session_state.termbase, num_rows="dynamic", hide_index=True, use_container_width=True)
    st.session_state.termbase=edited
    st.download_button("Download termbase", edited.to_csv(index=False).encode("utf-8"), "secureterm_termbase.csv", "text/csv")

if text.strip():
    sentences,numbers,acronyms,entities=extract_items(text)
    matches=term_matches(text,st.session_state.termbase)
    st.subheader("3. Briefing intelligence")
    a,b,c,d=st.columns(4)
    a.metric("Sentences",len(sentences)); b.metric("Numbers / times",len(numbers)); c.metric("Acronyms",len(acronyms)); d.metric("Named entities",len(entities))
    tabs=st.tabs(["Terminology matches","Numbers and times","Names and entities","Preparation questions"])
    with tabs[0]:
        if matches.empty: st.info("No controlled terminology match detected.")
        else: st.dataframe(matches,hide_index=True,use_container_width=True)
    with tabs[1]:
        st.write(numbers if numbers else "No numbers or times detected.")
    with tabs[2]:
        st.write({"Possible entities":entities,"Acronyms":acronyms})
    with tabs[3]:
        questions=[]
        for r in matches.to_dict("records") if not matches.empty else []:
            if r["Status"]!="Approved": questions.append("Confirm the authorised equivalent for '"+r["Source term"]+"'.")
        if numbers: questions.append("Confirm the time, date, units, and delivery convention for every numeric expression.")
        if entities: questions.append("Confirm names, ranks, institutional roles, and official Arabic forms.")
        questions.append("Identify any terms whose meaning depends on classified, political, legal, or operational context.")
        for q in questions: st.write("• "+q)

st.subheader("4. Assignment briefing sheet")
if text.strip():
    sheet=pd.DataFrame({
        "Project":[project],
        "Domain":[domain],
        "Prepared UTC":[datetime.now(timezone.utc).isoformat()],
        "Controlled terms":[len(term_matches(text,st.session_state.termbase))],
        "Numbers/times":[len(extract_items(text)[1])],
        "Entities":[len(extract_items(text)[3])],
        "Status":["Requires professional validation"],
    })
    st.dataframe(sheet,hide_index=True,use_container_width=True)
    st.download_button("Download briefing sheet",sheet.to_csv(index=False).encode("utf-8"),"secureterm_briefing_sheet.csv","text/csv")
else:
    st.info("Load or upload a briefing corpus to generate the preparation workspace.")
