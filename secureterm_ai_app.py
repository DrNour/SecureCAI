import io, re
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SecureTerm Pro AI", page_icon="🔗", layout="wide")

TERMS=pd.DataFrame([
["joint statement","البيان المشترك","Diplomatic","Approved","Use the institutional equivalent in formal statements."],
["delegation","الوفد","Institutional","Approved","Confirm delegation identity."],
["representative","ممثل","Institutional","Needs verification","Check rank and institutional role."],
["ceasefire","وقف إطلاق النار","Security","Approved","Verify scope and context."],
["rules of engagement","قواعد الاشتباك","Security","Needs verification","Confirm authorised institutional wording."],
["strategic communication","الاتصال الاستراتيجي","Defence","Approved","Keep register formal."],
["may","قد","Modality","Approved","Preserve possibility."],
["must","يجب","Modality","Approved","Preserve obligation."],
],columns=["Source term","Arabic equivalent","Domain","Status","Context note"])

DEMO=("The delegation will review the joint statement during the strategic communication briefing. "
"The representative may discuss the proposed ceasefire language and the rules of engagement.")

def split_segments(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+",text) if s.strip()]

def terms_in(segment, tb):
    low=segment.lower()
    return [r for _,r in tb.iterrows() if r["Source term"].lower() in low]

def fallback_translate(segment,tb):
    result=segment
    for _,r in sorted(tb.iterrows(),key=lambda x:len(x[1]["Source term"]),reverse=True):
        result=re.sub(re.escape(r["Source term"]),r["Arabic equivalent"],result,flags=re.IGNORECASE)
    return result

def optional_ai_translate(segment, terms):
    try:
        from openai import OpenAI
        key=st.secrets.get("OPENAI_API_KEY","")
        if not key:
            return None
        client=OpenAI(api_key=key)
        glossary="; ".join(f'{r["Source term"]} = {r["Arabic equivalent"]}' for r in terms)
        response=client.responses.create(model=st.secrets.get("OPENAI_MODEL","gpt-4.1-mini"),input=f"Translate the following English segment into formal Arabic. Preserve meaning and use these controlled equivalents where relevant: {glossary}. Return only the candidate translation. Segment: {segment}")
        return response.output_text.strip()
    except Exception:
        return None

st.title("SecureTerm Pro AI")
st.caption("Briefing analysis, terminology alignment, and human-verified English–Arabic candidate translation")
st.warning("Research prototype. Use synthetic or institutionally approved non-sensitive material. AI output is a candidate, not an authorised translation.")

with st.sidebar:
    project=st.text_input("Project or assignment","Strategic briefing")
    domain=st.selectbox("Domain",["Defence and diplomacy","Strategic communication","Institutional translation","Training simulation"])
    use_ai=st.checkbox("Use configured AI model",help="Requires OPENAI_API_KEY in Streamlit secrets. Without a key, the transparent termbase method is used.")
    st.caption("Every candidate requires professional review.")

if "termbase" not in st.session_state: st.session_state.termbase=TERMS.copy()
if "text" not in st.session_state: st.session_state.text=""

left,right=st.columns([1.05,1])
with left:
    st.subheader("1. Source briefing")
    if st.button("Load synthetic briefing"):
        st.session_state.text=DEMO
        st.rerun()
    text=st.text_area("Paste an approved briefing passage",value=st.session_state.text,height=190)
    st.session_state.text=text
with right:
    st.subheader("2. Controlled termbase")
    edited=st.data_editor(st.session_state.termbase,num_rows="dynamic",hide_index=True,use_container_width=True)
    st.session_state.termbase=edited

if text.strip():
    segments=split_segments(text)
    st.subheader("3. Alignment and key-term translation")
    st.caption("Each row aligns one source segment with the terms detected in it and a candidate Arabic rendering.")
    rows=[]
    for seg in segments:
        matched=terms_in(seg,st.session_state.termbase)
        ai_candidate=optional_ai_translate(seg,matched) if use_ai else None
        candidate=ai_candidate or fallback_translate(seg,st.session_state.termbase)
        rows.append({"Segment":seg,"Key terms":", ".join(r["Source term"] for r in matched) or "None","Candidate Arabic":candidate,"Method":"Configured AI model" if ai_candidate else "Controlled-termbase candidate","Review status":"Needs human review","Reviewer notes":""})
    alignment=pd.DataFrame(rows)
    reviewed=st.data_editor(alignment,hide_index=True,use_container_width=True,num_rows="fixed",height=260,column_config={"Review status":st.column_config.SelectboxColumn(options=["Needs human review","Accepted","Edited","Rejected","Escalate"],required=True)})
    st.download_button("Download alignment report",reviewed.to_csv(index=False).encode("utf-8"),"secureterm_alignment_report.csv","text/csv")
    st.subheader("4. Key-term alignment view")
    key_rows=[]
    for _,r in reviewed.iterrows():
        for term in terms_in(r["Segment"],st.session_state.termbase):
            key_rows.append({"Source segment":r["Segment"],"Source term":term["Source term"],"Arabic equivalent":term["Arabic equivalent"],"Domain":term["Domain"],"Status":term["Status"],"Human decision":r["Review status"]})
    if key_rows: st.dataframe(pd.DataFrame(key_rows),hide_index=True,use_container_width=True)
    else: st.info("No controlled terms detected.")
    st.subheader("5. Professional verification questions")
    questions=[]
    for _,r in reviewed.iterrows():
        if r["Review status"]!="Accepted": questions.append("Verify the candidate rendering for: "+r["Segment"])
    for _,r in st.session_state.termbase.iterrows():
        if r["Status"]!="Approved" and any(r["Source term"].lower() in s.lower() for s in segments): questions.append("Confirm the authorised equivalent for: "+r["Source term"])
    for q in questions[:12]: st.write("• "+q)
else:
    st.info("Load the synthetic briefing or paste approved text to begin alignment.")
