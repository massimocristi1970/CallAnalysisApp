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

def clean_text(text):
    text = unicodedata.normalize("NFKD", text)
    return text.encode("ascii", "ignore").decode("ascii")


# Sidebar: Choose Whisper model size
model_size = st.sidebar.selectbox("Select Whisper model size", ["small", "base"])
call_type = st.sidebar.selectbox("Select Call Type", ["Customer Service", "Collections"])
set_model_size(model_size)

st.title("📞 Call Analysis Scorecard")

uploaded_files = st.file_uploader(
    "Upload call recordings (MP3/WAV)", type=["mp3", "wav"], accept_multiple_files=True
)

def generate_pdf(title, transcript, sentiment, keywords, qa_results):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.multi_cell(0, 10, txt=clean_text(title), align='L')
    pdf.ln()

    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, clean_text("Transcript:"), ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, clean_text(transcript))
    pdf.ln()

    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, clean_text(f"Sentiment: {sentiment}"), ln=True)

    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, clean_text("Keywords:"), ln=True)
    pdf.set_font("Arial", size=12)
    for kw in sorted(set(keywords)):
        pdf.cell(0, 10, clean_text(f"- {kw}"), ln=True)
    pdf.ln()

    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, clean_text("Rule-Based QA Scoring:"), ln=True)
    pdf.set_font("Arial", size=12)
    for section, result in qa_results.items():
        line = f"- {section}: {result['score']} - {result['explanation']}"
        pdf.cell(0, 10, clean_text(line), ln=True)

    pdf.ln()

    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, clean_text("NLP-Based QA Scoring:"), ln=True)
    pdf.set_font("Arial", size=12)
    qa_results_nlp = score_call_nlp(transcript)  # 🔹 Call NLP-based scoring
    for section, result in qa_results_nlp.items():
        line = f"- {section}: {result['score']} - {result['explanation']}"
        pdf.cell(0, 10, clean_text(line), ln=True)


    return pdf


if uploaded_files:
    progress_bar = st.progress(0, text="Processing uploaded files...")
    durations = []

    for i, uploaded_file in enumerate(uploaded_files, start=1):
        progress = i / len(uploaded_files)
        progress_bar.progress(progress, text=f"Processing file {i} of {len(uploaded_files)}")

        st.markdown("---")
        st.markdown(f"### 📁 Processing file {i} of {len(uploaded_files)}: `{uploaded_file.name}`")

        save_path = os.path.join("audio_samples", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if not durations:
            st.info("⏳ Estimating time... (processing first file)")

        with st.spinner("Transcribing..."):
            start = time.time()
            transcript = transcribe_audio(save_path)
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
        qa_results_nlp = score_call_nlp(transcript)

        st.markdown("#### 🔍 Rule-Based Scoring")
        for section, result in qa_results.items():
            emoji = "✅" if result["score"] >= 1 else "❌"
            st.markdown(f"- {emoji} **{section}**: {result['explanation']}")

        total_score = sum(result["score"] for result in qa_results.values())
        st.markdown(f"**🏁 Total Rule-Based Score: {total_score}/4**")

        st.markdown("---")

        st.markdown("#### 🧠 NLP-Based Scoring")
        for section, result in qa_results_nlp.items():
            emoji = "✅" if result["score"] >= 1 else "❌"
            st.markdown(f"- {emoji} **{section}**: {result['explanation']}")

        total_score_nlp = sum(result["score"] for result in qa_results_nlp.values())
        st.markdown(f"**🏁 Total NLP-Based Score: {total_score_nlp}/4**")


        total_score = sum(result["score"] for result in qa_results.values())

        # Generate and display PDF download button for this call
        pdf = generate_pdf(
            title=f"Call Summary – {uploaded_file.name}",
            transcript=transcript,
            sentiment=sentiment,
            keywords=[m["phrase"] for m in keyword_matches],
            qa_results=qa_results
        )

        pdf_bytes = BytesIO()
        pdf_output = pdf.output(dest='S')
        pdf_bytes.write(pdf_output)
        pdf_bytes.seek(0)


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


    progress_bar.empty()

    # ✅ Combined summary report
    if "summary_pdfs" in st.session_state and st.session_state["summary_pdfs"]:
        combined_pdf = FPDF()
        for name, transcript, sentiment, keyword_matches, qa_results in st.session_state["summary_pdfs"]:
            combined_pdf.add_page()
            combined_pdf.set_font("Arial", size=12)
           
            combined_pdf.multi_cell(0, 10, txt=clean_text(f"Call: {name}"), align='L')
            combined_pdf.ln()
            combined_pdf.multi_cell(0, 10, clean_text(transcript))
            combined_pdf.ln()
            
            combined_pdf.cell(0, 10, clean_text(f"Sentiment: {sentiment}"), ln=True)
            combined_pdf.cell(0, 10, clean_text("Keywords:"), ln=True)
            for kw in sorted(set(m["phrase"] for m in keyword_matches)):
                combined_pdf.cell(0, 10, clean_text(f"- {kw}"), ln=True)
            # Rule-Based QA Scoring
            combined_pdf.cell(0, 10, clean_text("Rule-Based QA Scoring:"), ln=True)
            for section, result in qa_results.items():
                combined_pdf.cell(0, 10, clean_text(f"- {section}: {result['score']} - {result['explanation']}"), ln=True)

            combined_pdf.ln()

            # NLP-Based QA Scoring
            qa_results_nlp = score_call_nlp(transcript)
            combined_pdf.cell(0, 10, clean_text("NLP-Based QA Scoring:"), ln=True)
            for section, result in qa_results_nlp.items():
                combined_pdf.cell(0, 10, clean_text(f"- {section}: {result['score']} - {result['explanation']}"), ln=True)



        pdf_all = BytesIO()
        pdf_output = pdf.output(dest='S')
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

    qa_results_nlp = score_call_nlp(transcript)

    st.markdown("---")
    st.subheader("🧠 NLP-Based Scoring Summary (test)")
    for section, result in qa_results_nlp.items():
        emoji = "✅" if result["score"] == 1 else "❌"
        st.markdown(f"- {emoji} **{section}**: {result['explanation']}")

    total_score_nlp = sum(r["score"] for r in qa_results_nlp.values())
    st.markdown(f"### 🧠 Total NLP Score (test): **{total_score_nlp}/4**")

    
