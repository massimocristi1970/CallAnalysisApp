# streamlit_app.py
import streamlit as st

st.set_page_config(page_title="Call Transcriber", layout="centered")

import os
import time
import torch
import numpy as np
from transcriber import transcribe_audio, set_model_size
from analyser import get_sentiment, find_keywords, score_call, score_call_nlp
from fpdf import FPDF
from io import BytesIO
import unicodedata
import ftfy
from pdf_exporter import generate_pdf_report

def clean_text(text):
    text = unicodedata.normalize("NFKD", text)
    return ftfy.fix_text(text)

# Sidebar: Choose Whisper model size
model_size = st.sidebar.selectbox("Select Whisper model size", ["small", "base"])
call_type = st.sidebar.selectbox("Select Call Type", ["Customer Service", "Collections"])
set_model_size(model_size)

st.title("📞 Call Analysis Scorecard")

uploaded_files = st.file_uploader(
    "Upload call recordings (MP3/WAV)", type=["mp3", "wav"], accept_multiple_files=True
)

@st.cache_data
def cached_transcribe(file_path):
    return transcribe_audio(file_path)

if uploaded_files:
    progress_bar = st.progress(0, text="Processing uploaded files...")
    durations = []

    for i, uploaded_file in enumerate(uploaded_files, start=1):
        progress = i / len(uploaded_files)
        progress_bar.progress(progress, text=f"Processing file {i} of {len(uploaded_files)}")

        st.markdown("---")
        st.markdown(f"### 📁 Processing file {i} of {len(uploaded_files)}: `{uploaded_file.name}`")

        if uploaded_file.size > 10 * 1024 * 1024:  # 10MB limit
            st.error(f"File {uploaded_file.name} too large. Max size: 10MB")
            continue
        save_path = os.path.join("audio_samples", uploaded_file.name)
        try:
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        except Exception as e:
            st.error(f"Failed to save file {uploaded_file.name}: {str(e)}")
            continue
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)

        if not durations:
            st.info("⏳ Estimating time... (processing first file)")

        with st.spinner("Transcribing..."):
            start = time.time()
            transcript = cached_transcribe(save_path)
            duration = time.time() - start
            durations.append(duration)

        st.success(f"✅ Transcription completed in {duration:.2f} seconds.")

        avg_duration = np.mean(durations)
        files_left = len(uploaded_files) - i
        if files_left > 0:
            eta = avg_duration * files_left
            st.info(f"⏳ Estimated time remaining: {eta:.0f} seconds for {files_left} file(s)")

        # Highlight Keywords
        keyword_matches = find_keywords(transcript)
        highlighted = transcript
        offset = 0
        for match in keyword_matches:
            start = match['start'] + offset
            end = match['end'] + offset
            phrase = highlighted[start:end]
            highlight_html = f'<mark style="background-color: #ffff00">{phrase}</mark>'
            highlighted = highlighted[:start] + highlight_html + highlighted[end:]
            offset += len(highlight_html) - len(phrase)

        # Transcript
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

        # QA Scoring (Dual Approach)
        st.subheader("📊 QA Scoring Summary")

        qa_results = score_call(transcript, call_type)
        qa_results_nlp = score_call_nlp(transcript, call_type)

        st.markdown("#### 🔍 Rule-Based Scoring")
        for section, result in qa_results.items():
            emoji = "✅" if result["score"] >= 1 else "❌"
            st.markdown(f"- {emoji} **{section}**: {result['explanation']}")

        total_score = sum(result["score"] for result in qa_results.values())
        max_score = len(qa_results) * 3  # Max score is 3 per category
        st.markdown(f"**🏁 Total Rule-Based Score: {total_score}/{max_score}**")

        st.markdown("---")

        st.markdown("#### 🧠 NLP-Based Scoring")
        for section, result in qa_results_nlp.items():
            emoji = "✅" if result["score"] >= 1 else "❌"
            st.markdown(f"- {emoji} **{section}**: {result['explanation']}")

        total_score_nlp = sum(result["score"] for result in qa_results_nlp.values())
        st.markdown(f"**🏁 Total NLP-Based Score: {total_score_nlp}/4**")

        # Single-call PDF
        call_data = [{
            "filename": uploaded_file.name,
            "transcript": transcript,
            "sentiment": sentiment,
            "keywords": [m["phrase"] for m in keyword_matches],
            "qa_scores": qa_results,
            "call_type": call_type
        }]
        pdf_bytes = generate_pdf_report(call_data)
        st.download_button(
            label="📥 Download PDF for this Call",
            data=pdf_bytes,
            file_name=f"{uploaded_file.name}_summary.pdf",
            mime="application/pdf"
        )

        # Save for combined summary
        if "summary_pdfs" not in st.session_state:
            st.session_state["summary_pdfs"] = []

        st.session_state["summary_pdfs"].append((
            uploaded_file.name, transcript, sentiment, keyword_matches, qa_results, qa_results_nlp
        ))

    # Clean up progress bar
    progress_bar.empty()

    # Combined summary report
    from pdf_exporter import generate_pdf_report
    if "summary_pdfs" in st.session_state and st.session_state["summary_pdfs"]:
        call_data = [
            {
                "filename": name,
                "transcript": transcript,
                "sentiment": sentiment,
                "keywords": [m["phrase"] for m in keyword_matches],
                "qa_scores": qa_results,
                "call_type": call_type
            }
            for name, transcript, sentiment, keyword_matches, qa_results, qa_results_nlp in st.session_state["summary_pdfs"]
        ]
        pdf_all = BytesIO()
        pdf_output = generate_pdf_report(call_data)
        pdf_all.write(pdf_output)
        pdf_all.seek(0)
        st.download_button(
            label="📄 Download Summary Report (All Calls)",
            data=pdf_all,
            file_name="Combined_Call_Summary.pdf",
            mime="application/pdf"
        )

# Test
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
    st.subheader("📊 QA Scoring Summary (test)")
    for section, result in qa_results.items():
        emoji = "✅" if result["score"] == 1 else "❌"
        st.markdown(f"- {emoji} **{section}**: {result['explanation']}")
    total_score = sum(r["score"] for r in qa_results.values())
    st.markdown(f"### 🏁 Total Score (test): **{total_score}/4**")

    qa_results_nlp = score_call_nlp(transcript, call_type)

    st.markdown("---")
    st.subheader("🧠 NLP-Based Scoring Summary (test)")
    for section, result in qa_results_nlp.values():
        emoji = "✅" if result["score"] == 1 else "❌"
        st.markdown(f"- {emoji} **{section}**: {result['explanation']}")

    total_score_nlp = sum(r["score"] for r in qa_results_nlp.values())
    st.markdown(f"### 🧠 Total NLP Score (test): **{total_score_nlp}/4**")
