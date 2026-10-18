import io,re
from collections import Counter
from datetime import datetime,timezone
from urllib.parse import urlparse
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

st.set_page_config(page_title="SecureTerm Pro",page_icon="🔎",layout="wide")
DEFAULT=pd.DataFrame([
["joint statement","البيان المشترك","Diplomatic","Approved"],
["delegation","الوفد","Institutional","Approved"],
["representative","ممثل","Institutional","Needs verification"],
["ceasefire","وقف إطلاق النار","Security","Approved"],
["rules of engagement","قواعد الاشتباك","Security","Needs verification"],
["strategic communication","الاتصال الاستراتيجي","Defence","Approved"],
],columns=["Source term","Arabic equivalent","Domain","Status"])

STOP=set("the a an and or of to in for on at by with from as is are was were will be this that during into about their its our your which what how".split())
def extract_page(url):
    p=urlparse(url)
    if p.scheme not in ("http","https"): raise ValueError("URL must begin with http:// or https://")
    r=requests.get(url,headers={"User-Agent":"SecureTermPro/1.0"},timeout=20)
    r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    title=soup.title.get_text(" ",strip=True) if soup.title else url
    for tag in soup(["script","style","nav","footer","header","aside","form"]): tag.decompose()
    return title," ".join(soup.get_text(" ").split())

def extract_file(f):
    data=f.getvalue();name=f.name.lower()
    if name.endswith(".txt"): return f.name,data.decode("utf-8",errors="ignore")
    if name.endswith(".docx"):
        from docx import Document
        return f.name," ".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return f.name," ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
    return f.name,""

def candidates(text):
    words=re.findall(r"[A-Za-z][A-Za-z'-]*",text.lower())
    grams=Counter()
    for n in (2,3,4):
        for i in range(len(words)-n+1):
            g=words[i:i+n]
            if g[0] in STOP or g[-1] in STOP or any(x in STOP for x in g): continue
            grams[" ".join(g)]+=1
    repeated=[(x,c) for x,c in grams.most_common(100) if c>=1 and len(x)>5]
    entities=sorted(set(re.findall(r"\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,4}\b",text)))
    acronyms=sorted(set(re.findall(r"\b[A-Z]{2,}\b",text)))
    numbers=sorted(set(re.findall(r"\b\d+(?:[:.]\d+)?\b",text)))
    return repeated,entities,acronyms,numbers

def split_text(text): return [x.strip() for x in re.split(r"(?<=[.!?])\s+",text) if x.strip()]
def fallback(seg,tb):
    out=seg
    for _,r in sorted(tb.iterrows(),key=lambda z:len(z[1]["Source term"]),reverse=True):
        out=re.sub(re.escape(r["Source term"]),r["Arabic equivalent"],out,flags=re.I)
    return out

st.title("SecureTerm Pro")
st.caption("Document and web-source analysis, term extraction, alignment, and human-verified English–Arabic candidates")
st.warning("Use public, permitted, or institutionally approved non-sensitive sources only. Candidate translations require professional validation.")

if "text" not in st.session_state: st.session_state.text=""
if "sources" not in st.session_state: st.session_state.sources=[]
if "tb" not in st.session_state: st.session_state.tb=DEFAULT.copy()

with st.sidebar:
    st.header("Project")
    st.text_input("Assignment","Strategic briefing")
    st.selectbox("Domain",["Defence and diplomacy","Strategic communication","Institutional translation","Training simulation"])
    st.caption("Extraction finds candidates. It does not establish official terminology.")

a,b=st.columns([1.1,1])
with a:
    st.subheader("1. Add source material")
    url=st.text_input("Public webpage URL")
    if st.button("Fetch URL"):
        try:
            title,text=extract_page(url);st.session_state.text+="\n\n"+text;st.session_state.sources.append({"source":title,"url":url,"retrieved_utc":datetime.now(timezone.utc).isoformat()});st.success(f"Fetched {len(text):,} characters.")
        except Exception as e: st.error(f"Fetch failed: {e}")
    uploads=st.file_uploader("Upload TXT, DOCX, or PDF",type=["txt","docx","pdf"],accept_multiple_files=True)
    if uploads and st.button("Extract uploaded files"):
        for f in uploads:
            title,text=extract_file(f);st.session_state.text+="\n\n"+text;st.session_state.sources.append({"source":title,"url":"Uploaded file","retrieved_utc":datetime.now(timezone.utc).isoformat()})
    st.session_state.text=st.text_area("Working corpus",value=st.session_state.text,height=240)
with b:
    st.subheader("2. Controlled termbase")
    st.session_state.tb=st.data_editor(st.session_state.tb,num_rows="dynamic",hide_index=True,use_container_width=True)
    st.download_button("Download termbase",st.session_state.tb.to_csv(index=False).encode(),"secureterm_termbase.csv","text/csv")

if st.session_state.text.strip():
    text=st.session_state.text;repeated,entities,acronyms,numbers=candidates(text);segs=split_text(text)
    st.subheader("3. Extraction results")
    x,y,z,q=st.columns(4);x.metric("Characters",len(text));y.metric("Candidate phrases",len(repeated));z.metric("Entities",len(entities));q.metric("Numbers/times",len(numbers))
    t1,t2,t3,t4=st.tabs(["Candidate terms","Entities and numbers","Alignment","Sources"])
    with t1:
        term_rows=[]
        for phrase,count in repeated:
            hit=st.session_state.tb[st.session_state.tb["Source term"].str.lower()==phrase]
            term_rows.append({"Candidate term":phrase,"Frequency":count,"Arabic equivalent":hit.iloc[0]["Arabic equivalent"] if not hit.empty else "Add translation","Status":hit.iloc[0]["Status"] if not hit.empty else "Needs verification"})
        found=pd.DataFrame(term_rows)
        edited=st.data_editor(found,hide_index=True,use_container_width=True,num_rows="dynamic")
        st.download_button("Download extracted terms",edited.to_csv(index=False).encode(),"secureterm_extracted_terms.csv","text/csv")
    with t2:
        st.write({"Possible named entities":entities,"Acronyms":acronyms,"Numbers and times":numbers})
    with t3:
        rows=[]
        for seg in segs[:100]:
            ms=st.session_state.tb[st.session_state.tb["Source term"].apply(lambda x:x.lower() in seg.lower())]
            rows.append({"Source segment":seg,"Key terms":", ".join(ms["Source term"].tolist()) or "Candidate review required","Candidate Arabic":fallback(seg,st.session_state.tb),"Review status":"Needs human review","Notes":""})
        alignment=st.data_editor(pd.DataFrame(rows),hide_index=True,use_container_width=True,height=330,column_config={"Review status":st.column_config.SelectboxColumn(options=["Needs human review","Accepted","Edited","Rejected","Escalate"],required=True)})
        st.download_button("Download alignment",alignment.to_csv(index=False).encode(),"secureterm_alignment.csv","text/csv")
    with t4:
        st.dataframe(pd.DataFrame(st.session_state.sources) if st.session_state.sources else pd.DataFrame({"source":["Pasted text"]}),hide_index=True,use_container_width=True)
else:
    st.info("Add a URL, upload a document, or paste text. Extraction results will appear here.")
