# app.py
import streamlit as st

st.set_page_config(page_title="Call Transcriber", layout="centered")  # ← must be first Streamlit command

import os
import time
import torch
import numpy as np
from transcriber import transcribe_audio, set_model_size
from analyser import get_sentiment, find_keywords

# Choose Whisper model size from sidebar
model_size = st.sidebar.selectbox("Select Whisper model size", ["small", "base"])

# Set the model based on selection
set_model_size(model_size)

# ✅ GPU Availability Notice
st.sidebar.write("GPU available:", torch.cuda.is_available())
if not torch.cuda.is_available():
    st.sidebar.warning("⚠️ Running on CPU — transcriptions may take longer.")

st.title("📞 Call Analysis Scorecard")

# ✅ Multi-file uploader
uploaded_files = st.file_uploader(
    "Upload call recordings (MP3/WAV)", type=["mp3", "wav"], accept_multiple_files=True
)

if uploaded_files:
    progress_bar = st.progress(0, text="Processing uploaded files...")
    durations = []

    for i, uploaded_file in enumerate(uploaded_files, start=1):
        progress = i / len(uploaded_files)
        progress_bar.progress(progress, text=f"Processing file {i} of {len(uploaded_files)}")

        st.markdown("---")
        st.markdown(f"### 📁 Processing file {i} of {len(uploaded_files)}: `{uploaded_file.name}`")

        # Save uploaded file
        save_path = os.path.join("audio_samples", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Show "estimating..." if first file
        if not durations:
            st.info("⏳ Estimating time... (processing first file)")

        with st.spinner("Transcribing..."):
            start = time.time()
            transcript = transcribe_audio(save_path)
            duration = time.time() - start
            durations.append(duration)

        st.success(f"✅ Transcription completed in {duration:.2f} seconds.")

        # ✅ Estimate remaining time AFTER first file
        avg_duration = np.mean(durations)
        files_left = len(uploaded_files) - i
        if files_left > 0:
            eta = avg_duration * files_left
            st.info(f"⏳ Estimated time remaining: {eta:.0f} seconds for {files_left} file(s)")

        # Show transcript
        # Keyword highlighting
        keyword_matches = find_keywords(transcript)
        highlighted = transcript
        offset = 0  # adjust for <mark> tags

        for match in keyword_matches:
            start = match['start'] + offset
            end = match['end'] + offset
            phrase = highlighted[start:end]
            highlighted_phrase = f'<mark style="background-color: #ffff00">{phrase}</mark>'
            highlighted = highlighted[:start] + highlighted_phrase + highlighted[end:]
            offset += len(highlighted_phrase) - len(phrase)

        # Display highlighted transcript
        st.subheader("📝 Transcript with Highlights")
        st.markdown(highlighted, unsafe_allow_html=True)

        # Keywords
        if keyword_matches:
            st.markdown("**🔍 Keywords Detected:**")
            for kw in sorted(set(m["phrase"] for m in keyword_matches)):
                st.markdown(f"- {kw}")
        else:
            st.markdown("**✅ No key phrases detected.**")


    # ✅ Done!
    progress_bar.empty()


# ✅ TEMP TEST: Controlled by sidebar checkbox
if st.sidebar.checkbox("Run test with sample transcript"):
    transcript = transcript = (
    "I want to file a complaint because I'm facing financial difficulties, feeling low, "
    "and unable to pay. I’ve been signed off work due to mental health issues, possibly PTSD or depression, "
    "and I recently had surgery. The stress is overwhelming and I’m grieving the loss of a loved one. "
    "I’ve even thought about suicide. I’m currently unemployed and struggling to cover funeral costs, "
    "and I’ve had to speak to the police after a domestic abuse incident. I think the manager was irresponsible "
    "in how they handled my case."
)

    sentiment = get_sentiment(transcript)
    st.markdown(f"**😊 Sentiment (test):** {sentiment}")
    keywords_found = find_keywords(transcript)
    if keywords_found:
        st.markdown("**🔍 Keywords Detected (test):**")
        for kw in keywords_found:
            st.markdown(f"- {kw}")
    else:
        st.markdown("**✅ No key phrases detected (test).**")
