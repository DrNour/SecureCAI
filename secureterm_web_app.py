import re
from datetime import datetime, timezone
from urllib.parse import urlparse
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

st.set_page_config(page_title="SecureTerm Web", page_icon="🌐", layout="wide")

TERMS=pd.DataFrame([
["joint statement","البيان المشترك","Diplomatic","Approved"],
["delegation","الوفد","Institutional","Approved"],
["representative","ممثل","Institutional","Needs verification"],
["ceasefire","وقف إطلاق النار","Security","Approved"],
["rules of engagement","قواعد الاشتباك","Security","Needs verification"],
["strategic communication","الاتصال الاستراتيجي","Defence","Approved"],
["may","قد","Modality","Approved"],
["must","يجب","Modality","Approved"],
],columns=["Source term","Arabic equivalent","Domain","Status"])

def scrape(url):
    parsed=urlparse(url)
    if parsed.scheme not in {"http","https"}: raise ValueError("Use an http or https URL.")
    response=requests.get(url,headers={"User-Agent":"SecureTerm-Research/1.0"},timeout=20)
    response.raise_for_status()
    soup=BeautifulSoup(response.text,"html.parser")
    for tag in soup(["script","style","nav","footer","header","aside"]): tag.decompose()
    title=soup.title.get_text(" ",strip=True) if soup.title else url
    text=" ".join(soup.get_text(" ").split())
    return title,text

def segments(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+",text) if s.strip()]

def matched(seg,tb):
    low=seg.lower()
    return [r for _,r in tb.iterrows() if r["Source term"].lower() in low]

def candidate(seg,tb):
    out=seg
    for _,r in sorted(tb.iterrows(),key=lambda x:len(x[1]["Source term"]),reverse=True):
        out=re.sub(re.escape(r["Source term"]),r["Arabic equivalent"],out,flags=re.I)
    return out

st.title("SecureTerm Web")
st.caption("Traceable web-source collection, terminology alignment, and human-verified English–Arabic candidates")
st.warning("Use public, permitted, non-sensitive sources only. Check terms of use, copyright, robots policies, and institutional security rules before collecting or reusing content.")

if "corpus" not in st.session_state: st.session_state.corpus=""
if "sources" not in st.session_state: st.session_state.sources=[]
if "tb" not in st.session_state: st.session_state.tb=TERMS.copy()

with st.sidebar:
    st.header("Source controls")
    timeout=st.slider("Request timeout (seconds)",5,30,20)
    st.caption("The app stores source URLs and retrieval times in the exported report.")

left,right=st.columns([1,1])
with left:
    st.subheader("1. Add web sources")
    url=st.text_input("Public webpage URL")
    if st.button("Fetch webpage"):
        try:
            title,text=scrape(url)
            st.session_state.corpus += "\n\n"+text
            st.session_state.sources.append({"title":title,"url":url,"retrieved_utc":datetime.now(timezone.utc).isoformat(),"characters":len(text)})
            st.success("Readable page text added to the working corpus.")
        except Exception as exc: st.error("Could not fetch this page: "+str(exc))
    st.subheader("2. Working corpus")
    pasted=st.text_area("Review, edit, or add approved text",value=st.session_state.corpus,height=220)
    st.session_state.corpus=pasted
with right:
    st.subheader("3. Controlled termbase")
    st.session_state.tb=st.data_editor(st.session_state.tb,num_rows="dynamic",hide_index=True,use_container_width=True)
    if st.session_state.sources: st.dataframe(pd.DataFrame(st.session_state.sources),hide_index=True,use_container_width=True)

if st.session_state.corpus.strip():
    st.subheader("4. Web-source alignment")
    rows=[]
    for seg in segments(st.session_state.corpus)[:80]:
        ms=matched(seg,st.session_state.tb)
        rows.append({"Source segment":seg,"Key terms":", ".join(r["Source term"] for r in ms) or "None","Candidate Arabic":candidate(seg,st.session_state.tb),"Review status":"Needs human review","Notes":""})
    aligned=st.data_editor(pd.DataFrame(rows),hide_index=True,use_container_width=True,height=320,column_config={"Review status":st.column_config.SelectboxColumn(options=["Needs human review","Accepted","Edited","Rejected","Escalate"],required=True)})
    st.download_button("Download web-source alignment",aligned.to_csv(index=False).encode("utf-8"),"secureterm_web_alignment.csv","text/csv")
    st.subheader("5. Source register")
    st.dataframe(pd.DataFrame(st.session_state.sources) if st.session_state.sources else pd.DataFrame({"Source":["Pasted text"],"Retrieved":["Current session"]}),hide_index=True,use_container_width=True)
else:
    st.info("Add a public webpage URL or paste approved text to begin.")
