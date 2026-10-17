from datetime import datetime, timezone
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SecureCAI Advanced", page_icon="🔐", layout="wide")

GLOSSARY = pd.DataFrame([
    ["joint statement","البيان المشترك","Diplomatic","Approved","Use the approved institutional equivalent."],
    ["delegation","الوفد","Institutional","Approved","Confirm the delegation name in context."],
    ["representative","ممثل","Institutional","Approved","Verify rank and institutional role."],
    ["ceasefire","وقف إطلاق النار","Security","Approved","Check scope and legal/diplomatic context."],
    ["may","قد","Modality","Approved","Do not strengthen possibility into certainty."],
    ["must","يجب","Modality","Approved","Preserve obligation."],
], columns=["Source term","Approved Arabic","Domain","Control","Guidance"])

DEMO = "The delegation may review the updated joint statement at 1400. The representative must confirm whether the proposed ceasefire language is acceptable."

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
    if any(ch.isupper() for ch in text):
        flags.append(["Names/acronyms", "Entity recognition", "Medium", "Confirm names, titles, and abbreviations."])
    return pd.DataFrame(flags, columns=["Trigger","Risk category","Severity","Why it matters"])

def glossary_matches(text):
    lower = text.lower()
    rows = []
    for _, r in GLOSSARY.iterrows():
        if r["Source term"].lower() in lower:
            rows.append(r.tolist())
    return pd.DataFrame(rows, columns=GLOSSARY.columns)

st.title("SecureCAI Advanced")
st.caption("Human-in-the-loop AI support for high-stakes English–Arabic interpreting")
st.warning("Demonstration mode. Use synthetic or institutionally approved material only. Never enter classified, personal, operational, or confidential information.")

with st.sidebar:
    st.header("Assignment profile")
    st.selectbox("Language pair", ["English → Arabic"])
    st.selectbox("Interpreting context", ["Defence and diplomacy", "Strategic communication", "Institutional briefing", "Training simulation"])
    sensitivity = st.selectbox("Information sensitivity", ["Synthetic demonstration", "Approved non-sensitive", "Restricted: do not process here"])
    st.divider()
    st.metric("Human decision authority", "Required")
    st.metric("Autonomous delivery", "Disabled")

if "passage" not in st.session_state:
    st.session_state.passage = ""
if "decisions" not in st.session_state:
    st.session_state.decisions = []

c1, c2 = st.columns([1.1, 1])
with c1:
    st.subheader("1. Source and candidate rendering")
    if st.button("Load synthetic case"):
        st.session_state.passage = DEMO
    passage = st.text_area("Source passage", value=st.session_state.passage, height=160)
    candidate = st.text_area("Interpreter or AI-assisted Arabic rendering", height=120, placeholder="Enter the candidate rendering for human review.")
    st.caption("SecureCAI does not deliver speech automatically. It supports preparation, verification, and documentation.")

with c2:
    st.subheader("2. Controlled terminology")
    st.dataframe(GLOSSARY, hide_index=True, use_container_width=True)
    st.caption("The glossary is a governance artefact, not merely a list of translations.")

if passage.strip():
    matches = glossary_matches(passage)
    risks = risk_scan(passage)
    st.subheader("3. Situation awareness")
    a, b, c = st.columns(3)
    a.metric("Glossary matches", len(matches))
    b.metric("Risk flags", len(risks))
    c.metric("Critical/high flags", int((risks["Severity"].isin(["Critical","High"])).sum()) if not risks.empty else 0)
    tab1, tab2, tab3 = st.tabs(["Terminology", "Risk flags", "Decision record"])
    with tab1:
        st.dataframe(matches, hide_index=True, use_container_width=True)
    with tab2:
        st.dataframe(risks, hide_index=True, use_container_width=True)
        st.info("Risk flags indicate where professional attention is needed. They do not determine the correct interpretation.")
    with tab3:
        st.write("Record the interpreter's decision for each flagged or terminology-sensitive item.")
        if not risks.empty:
            decision_rows = []
            for _, r in risks.iterrows():
                decision_rows.append({"Trigger":r["Trigger"],"Severity":r["Severity"],"Decision":"Pending","Rationale":""})
            decisions = st.data_editor(pd.DataFrame(decision_rows), hide_index=True, use_container_width=True,
                column_config={"Decision": st.column_config.SelectboxColumn(options=["Pending","Accept","Edit","Reject","Escalate"], required=True)})
            if st.button("Record reviewed case"):
                record = decisions.copy()
                record["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
                record["source_word_count"] = len(passage.split())
                record["candidate_provided"] = bool(candidate.strip())
                st.session_state.decisions.append(record)
                st.success("Reviewed case recorded for the current session.")
else:
    st.info("Load the synthetic case or enter approved non-sensitive text to begin.")

with st.expander("Research and evaluation view"):
    st.write("SecureCAI is designed to support empirical questions about professional judgement, not merely to demonstrate model fluency.")
    st.markdown("- Which risk categories produce the most interpreter edits?")
    st.markdown("- Does terminology support reduce search effort or shift effort to verification?")
    st.markdown("- How do experts and novices respond to the same confidence or risk flag?")
    st.markdown("- Which errors remain invisible to an automated quality score?")
    st.markdown("- How can anonymised interaction logs support interpreter education and institutional policy?")
    if st.session_state.decisions:
        all_decisions = pd.concat(st.session_state.decisions, ignore_index=True)
        st.dataframe(all_decisions, hide_index=True, use_container_width=True)
        st.download_button("Download anonymised session log", all_decisions.to_csv(index=False).encode("utf-8"), "securecai_session_log.csv", "text/csv")
