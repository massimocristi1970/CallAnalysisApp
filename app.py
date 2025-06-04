# app.py
import streamlit as st
import os
from transcriber import transcribe_audio

st.set_page_config(page_title="Call Transcriber", layout="centered")

st.title("📞 Call Recording Transcriber")

uploaded_file = st.file_uploader("Upload a call recording (MP3/WAV)", type=["mp3", "wav"])

if uploaded_file:
    # Save uploaded file
    save_path = os.path.join("audio_samples", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"Uploaded: {uploaded_file.name}")

    with st.spinner("Transcribing..."):
        transcript = transcribe_audio(save_path)

    st.subheader("📝 Transcript")
    st.text_area("Transcription Result", transcript, height=400)
