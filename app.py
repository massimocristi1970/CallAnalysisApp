# app.py
import streamlit as st
import os
from transcriber import transcribe_audio
from analyser import get_sentiment, find_keywords

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

    # ✅ Sentiment
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
