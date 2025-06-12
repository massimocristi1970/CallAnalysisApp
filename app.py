# app.py
import streamlit as st

st.set_page_config(page_title="Call Transcriber", layout="centered")

import os
import time
import torch
import numpy as np
from transcriber import transcribe_audio, set_model_size
from analyser import get_sentiment, find_keywords, score_call, score_call_nlp
from pdf_exporter import generate_pdf_report, generate_combined_pdf_report

# Sidebar controls
model_size = st.sidebar.selectbox("Select Whisper model size", ["medium", "small", "base"])
call_type = st.sidebar.selectbox("Select Call Type", ["Customer Service", "Collections"])
set_model_size(model_size)

st.title("📞 Call Analysis Scorecard")

uploaded_files = st.file_uploader(
    "Upload call recordings (MP3/WAV)", type=["mp3", "wav"], accept_multiple_files=True
)

if uploaded_files:
    progress_bar = st.progress(0, text="Processing uploaded files...")
    durations = []

    if "summary_pdfs" not in st.session_state:
        st.session_state["summary_pdfs"] = []

    for i, uploaded_file in enumerate(uploaded_files, start=1):
        progress = i / len(uploaded_files)
        progress_bar.progress(progress, text=f"Processing file {i} of {len(uploaded_files)}")

        st.markdown("---")
        st.markdown(f"### 📁 File: `{uploaded_file.name}`")

        # Save audio locally
        save_path = os.path.join("audio_samples", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if not durations:
            st.info("⏳ Estimating time... (first file)")

        # Transcription
        with st.spinner("Transcribing..."):
            start = time.time()
            transcript = transcribe_audio(save_path)
            durations.append(time.time() - start)

        st.success(f"✅ Transcription completed in {durations[-1]:.2f} seconds.")
        eta = np.mean(durations) * (len(uploaded_files) - i)
        if eta > 0:
            st.info(f"⏳ Estimated time remaining: {eta:.0f} seconds")

        # Highlight keywords
        keyword_matches = find_keywords(transcript)
        highlighted = transcript
        offset = 0
        for match in keyword_matches:
            start = match["start"] + offset
            end = match["end"] + offset
            phrase = highlighted[start:end]
            highlight_html = f'<mark style="background-color: #ffff00">{phrase}</mark>'
            highlighted = highlighted[:start] + highlight_html + highlighted[end:]
            offset += len(highlight_html) - len(phrase)

        # Display transcript
        st.subheader("📝 Transcript with Highlights")
        st.markdown(highlighted, unsafe_allow_html=True)

        # Sentiment
        sentiment = get_sentiment(transcript)
        st.markdown(f"**😊 Sentiment:** {sentiment}")

        # Keywords
        if keyword_matches:
            st.markdown("**🔍 Keywords Detected:**")
            for kw in sorted(set(m["phrase"] for m in keyword_matches)):
                st.markdown(f"- {kw}")
        else:
            st.markdown("**✅ No key phrases detected.**")

        # QA Scoring
        st.subheader("📊 QA Scoring Summary")

        qa_results = score_call(transcript, call_type)
        qa_results_nlp = score_call_nlp(transcript, call_type)

        st.markdown("#### 🔍 Rule-Based Scoring")
        for section, result in qa_results.items():
            emoji = "✅" if result["score"] >= 1 else "❌"
            st.markdown(f"- {emoji} **{section}**: {result['explanation']}")

        st.markdown(f"**🏁 Total Rule-Based Score: {sum(r['score'] for r in qa_results.values())}/4**")
        st.markdown("---")

        st.markdown("#### 🧠 NLP-Based Scoring")
        for section, result in qa_results_nlp.items():
            emoji = "✅" if result["score"] >= 1 else "❌"
            st.markdown(f"- {emoji} **{section}**: {result['explanation']}")

        st.markdown(f"**🏁 Total NLP-Based Score: {sum(r['score'] for r in qa_results_nlp.values())}/4**")

        # Export individual PDF
        pdf_bytes = generate_pdf_report(
            title=f"Call Summary – {uploaded_file.name}",
            transcript=transcript,
            sentiment=sentiment,
            keywords=[m["phrase"] for m in keyword_matches],
            qa_results=qa_results,
            qa_results_nlp=qa_results_nlp
        )

        st.download_button(
            label="📥 Download PDF for this Call",
            data=pdf_bytes,
            file_name=f"{uploaded_file.name}_summary.pdf",
            mime="application/pdf",
            key=f"download_{i}"  # 👈 ensure uniqueness using loop index
        )


        # Save for combined PDF
        st.session_state["summary_pdfs"].append({
            "filename": uploaded_file.name,
            "transcript": transcript,
            "sentiment": sentiment,
            "keywords": [m["phrase"] for m in keyword_matches],
            "qa_results": qa_results,
            "qa_results_nlp": qa_results_nlp
        })

    progress_bar.empty()

    # Export combined summary
    if st.session_state["summary_pdfs"]:
        combined_bytes = generate_combined_pdf_report(st.session_state["summary_pdfs"])
        st.download_button(
            label="📄 Download Summary Report (All Calls)",
            data=combined_bytes,
            file_name="Combined_Call_Summary.pdf",
            mime="application/pdf"
        )

# Test mode
if st.sidebar.checkbox("Run test with sample transcript"):
    transcript = (
        "Hello, I’m really struggling to pay. I’ve been in hospital with anxiety and side effects from surgery. "
        "I was signed off work. Can you help? I feel vulnerable and might need breathing space. "
        "I want to file a complaint about the last agent who refused to help."
    )
    st.subheader("Test Transcript")
    st.write(transcript)

    sentiment = get_sentiment(transcript)
    st.markdown(f"**😊 Sentiment (test):** {sentiment}")

    keywords_found = find_keywords(transcript)
    if keywords_found:
        st.markdown("**🔍 Keywords Detected (test):**")
        for kw in sorted(set(m["phrase"] for m in keywords_found)):
            st.markdown(f"- {kw}")
    else:
        st.markdown("**✅ No key phrases detected (test).**")

    qa_results = score_call(transcript, call_type)
    qa_results_nlp = score_call_nlp(transcript, call_type)

    st.subheader("📊 QA Scoring Summary (test)")
    for section, result in qa_results.items():
        emoji = "✅" if result["score"] >= 1 else "❌"
        st.markdown(f"- {emoji} **{section}**: {result['explanation']}")
    st.markdown(f"### 🏁 Total Rule-Based Score: {sum(r['score'] for r in qa_results.values())}/4")

    st.markdown("---")
    st.subheader("🧠 NLP-Based Scoring Summary (test)")
    for section, result in qa_results_nlp.items():
        emoji = "✅" if result["score"] >= 1 else "❌"
        st.markdown(f"- {emoji} **{section}**: {result['explanation']}")
    st.markdown(f"### 🧠 Total NLP Score: {sum(r['score'] for r in qa_results_nlp.values())}/4")
