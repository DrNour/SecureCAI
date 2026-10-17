import io
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SecureCAI", page_icon="🔐", layout="wide")

@st.cache_data
def load_glossary():
    return pd.read_csv("data/glossary.csv")

def analyse(text, glossary):
    rows = []
    lower = text.lower()
    for _, r in glossary.iterrows():
        if r["source_term"].lower() in lower:
            rows.append({
                "Source term": r["source_term"],
                "Approved Arabic": r["target_term"],
                "Category": r["category"],
                "Status": "Approved glossary match" if bool(r["approved"]) else "Review required",
                "Risk note": r["notes"],
                "Decision": "Pending",
                "Interpreter version": r["target_term"],
            })
    if any(ch.isdigit() for ch in text):
        rows.append({"Source term":"Number or time expression","Approved Arabic":"Human verification required","Category":"numeric","Status":"Risk flag","Risk note":"Check digits, time zone, and delivery format.","Decision":"Pending","Interpreter version":""})
    if any(w in lower.split() for w in ["may","must","not","cannot","could"]):
        rows.append({"Source term":"Modality or negation","Approved Arabic":"Human verification required","Category":"meaning","Status":"Risk flag","Risk note":"Check force, polarity, and degree of certainty.","Decision":"Pending","Interpreter version":"","Interpreter version":""})
    return pd.DataFrame(rows)

st.title("SecureCAI")
st.caption("Human-in-the-loop interpreting support for high-stakes institutional settings")
st.warning("Research prototype only. Use synthetic or approved non-sensitive material. Do not enter classified, personal, operational, or confidential information.")

with st.sidebar:
    st.header("Assignment controls")
    language_pair = st.selectbox("Language pair", ["English → Arabic"])
    mode = st.selectbox("Mode", ["Preparation and verification", "Post-assignment review"])
    st.divider()
    st.write("Human responsibility remains with the interpreter.")

glossary = load_glossary()
left, right = st.columns([1.15, 1])
with left:
    st.subheader("1. Source passage")
    demo = st.button("Load synthetic demonstration")
    default = "The delegation may review the updated joint statement at 1400." if demo else ""
    passage = st.text_area("Paste synthetic or approved text", value=default, height=180)
    st.subheader("2. Candidate output")
    candidate = st.text_area("Interpreter or AI-assisted Arabic version", value="", height=120, placeholder="Enter a candidate version for human review.")

with right:
    st.subheader("3. Controlled glossary")
    st.dataframe(glossary, use_container_width=True, hide_index=True)
    if passage.strip():
        findings = analyse(passage, glossary)
        st.subheader("4. Risk and terminology review")
        st.dataframe(findings[["Source term","Approved Arabic","Category","Status","Risk note"]], use_container_width=True, hide_index=True)
    else:
        findings = pd.DataFrame()
        st.info("Enter a synthetic passage to generate transparent flags.")

if not findings.empty:
    st.subheader("5. Interpreter decision log")
    editable = findings.copy()
    editable["Interpreter version"] = editable["Interpreter version"].replace("", candidate)
    reviewed = st.data_editor(editable[["Source term","Approved Arabic","Decision","Interpreter version"]], use_container_width=True, hide_index=True, num_rows="fixed", column_config={
        "Decision": st.column_config.SelectboxColumn("Decision", options=["Pending","Accept","Edit","Reject"], required=True)
    })
    report = reviewed.copy()
    report["timestamp_utc"] = datetime.utcnow().isoformat()
    report["language_pair"] = language_pair
    report["mode"] = mode
    st.download_button("Download review report", report.to_csv(index=False).encode("utf-8"), "securecai_review.csv", "text/csv")
