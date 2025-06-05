# app.py
import streamlit as st
import os
import time
import torch
from transcriber import transcribe_audio
from analyser import get_sentiment, find_keywords

st.set_page_config(page_title="Call Transcriber", layout="centered")

# ✅ GPU Availability Notice
st.sidebar.write("GPU available:", torch.cuda.is_available())
if not torch.cuda.is_available():
    st.sidebar.warning("⚠️ Running on CPU — transcriptions may take longer.")

st.title("📞 Call Recording Transcriber")

# ✅ Multi-file uploader
uploaded_files = st.file_uploader(
    "Upload call recordings (MP3/WAV)", type=["mp3", "wav"], accept_multiple_files=True
)

if uploaded_files:
    for i, uploaded_file in enumerate(uploaded_files, start=1):
        st.markdown("---")
        st.markdown(f"### 📁 Processing file {i} of {len(uploaded_files)}: `{uploaded_file.name}`")

        # ✅ Save uploaded file
        save_path = os.path.join("audio_samples", uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # ✅ Transcription with timing
        with st.spinner("Transcribing..."):
            start = time.time()
            transcript = transcribe_audio(save_path)
            duration = time.time() - start
        st.success(f"✅ Transcription completed in {duration:.2f} seconds.")

        # ✅ Display transcript
        st.subheader("📝 Transcript")
        st.text_area("Transcription Result", transcript, height=300, key=uploaded_file.name)

        # ✅ Sentiment analysis
        sentiment = get_sentiment(transcript)
        st.markdown(f"**😊 Sentiment:** {sentiment}")

        # ✅ Keyword detection
        keywords_found = find_keywords(transcript)
        if keywords_found:
            st.markdown("**🔍 Keywords Detected:**")
            for kw in keywords_found:
                st.markdown(f"- {kw}")
        else:
            st.markdown("**✅ No key phrases detected.**")

# ✅ TEMP TEST: Controlled by sidebar checkbox
if st.sidebar.checkbox("Run test with sample transcript"):
    transcript = "I want to file a complaint because I'm facing financial difficulties and unable to pay."
    sentiment = get_sentiment(transcript)
    st.markdown(f"**😊 Sentiment (test):** {sentiment}")
    keywords_found = find_keywords(transcript)
    if keywords_found:
        st.markdown("**🔍 Keywords Detected (test):**")
        for kw in keywords_found:
            st.markdown(f"- {kw}")
    else:
        st.markdown("**✅ No key phrases detected (test).**")
