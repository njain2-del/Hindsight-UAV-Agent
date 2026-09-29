"""
Streamlit UI for the UAV Fleet Maintenance agent (Hindsight-backed).

Run from the same uav_fleet folder as uav_agent_code.py:
    streamlit run streamlit_app.py
"""
import streamlit as st
import uav_agent_code as agent

st.set_page_config(page_title="UAV Fleet Maintenance Agent", page_icon="🛩️", layout="wide")

if "chat" not in st.session_state:
    st.session_state.chat = []  # list of dicts: {question, answer, evidence}

st.title("🛩️ UAV Fleet Maintenance Agent")
st.caption("Advisory guidance backed by fleet maintenance history, via Hindsight memory.")

tab_chat, tab_log = st.tabs(["💬 Ask", "📝 Log new report"])

# ---------------------------------------------------------------- Chat tab
with tab_chat:
    with st.form("ask_form", clear_on_submit=True):
        question = st.text_area(
            "Describe the fault or aircraft",
            placeholder='e.g. "UAV-260 has motor vibration at 48 flight hours, worse at high RPM. '
                        'Motors are from batch M-B7. What should we check?"',
            height=90,
        )
        submitted = st.form_submit_button("Ask the agent", type="primary")

    if submitted and question.strip():
        with st.spinner("Recalling fleet history and generating guidance..."):
            try:
                evidence = agent.client.recall(bank_id=agent.BANK, query=question).results[:5]
            except Exception as e:
                evidence = []
                st.warning(f"Recall step failed: {e}")
            try:
                answer = agent.ask(question)
            except Exception as e:
                answer = f"Error generating answer: {e}"

        st.session_state.chat.insert(0, {
            "question": question,
            "answer": answer,
            "evidence": [getattr(r, "text", str(r)) for r in evidence],
        })

    for turn in st.session_state.chat:
        st.markdown(f"### 🧑‍✈️ {turn['question']}")
        col_answer, col_memory = st.columns([3, 2])

        with col_answer:
            st.markdown("**Agent guidance**")
            st.markdown(turn["answer"])

        with col_memory:
            st.markdown(f"**🧠 Memory used** ({len(turn['evidence'])} reports)")
            if turn["evidence"]:
                for i, text in enumerate(turn["evidence"], 1):
                    st.markdown(f"{i}. {text}")
            else:
                st.info("No matching history found — guidance is general, not fleet-specific.")

        st.divider()

# ------------------------------------------------------------ Log-report tab
with tab_log:
    st.markdown("Add a new inspection or maintenance report. It's stored immediately and "
                "available to the agent on the next question — this is the learning loop.")

    with st.form("log_form", clear_on_submit=True):
        report_text = st.text_area(
            "Report text",
            placeholder="e.g. UAV-260 - motor 3 bearing replaced after grinding noise at 50 flight hours. "
                        "Motor from batch M-B7. Vibration resolved.",
            height=120,
        )
        log_submitted = st.form_submit_button("Store report", type="primary")

    if log_submitted and report_text.strip():
        try:
            agent.log(report_text.strip())
            st.success("Stored. The agent will use this on the next question.")
        except Exception as e:
            st.error(f"Failed to store report: {e}")