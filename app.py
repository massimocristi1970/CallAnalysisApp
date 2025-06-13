# app.py
import streamlit as st

st.set_page_config(page_title="Call Analysis Scorecard", layout="wide", initial_sidebar_state="expanded")

import os
import time
import numpy as np
import yaml
from pathlib import Path
import logging
from typing import Dict, List, Any

# Import our modules
from transcriber import transcribe_audio, set_model_size, validate_audio_file, cleanup_temp_files
from analyser import (
    get_sentiment, find_keywords_enhanced, score_call_rule_based, 
    score_call_nlp_enhanced, extract_nlp_insights, redact_pii, load_config
)
from pdf_exporter import generate_pdf_report, generate_combined_pdf_report

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d1edff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "summary_pdfs" not in st.session_state:
    st.session_state["summary_pdfs"] = []
if "processing_complete" not in st.session_state:
    st.session_state["processing_complete"] = False
if "temp_files" not in st.session_state:
    st.session_state["temp_files"] = []

# Load configuration
@st.cache_data
def get_app_config():
    return load_config()

config = get_app_config()
audio_config = config.get('audio', {})
security_config = config.get('security', {})

# Sidebar controls
st.sidebar.title("⚙️ Configuration")

# Model settings
st.sidebar.subheader("🤖 Model Settings")
model_size = st.sidebar.selectbox(
    "Whisper model size", 
    ["base", "small", "medium", "large"], 
    index=2,
    help="Larger models are more accurate but slower"
)

call_type = st.sidebar.selectbox(
    "Call Type", 
    ["Customer Service", "Collections", "Sales", "Support"],
    help="Affects scoring criteria"
)

# Processing settings
st.sidebar.subheader("🔧 Processing Settings")
enable_parallel_processing = st.sidebar.checkbox(
    "Enable parallel processing", 
    value=True,
    help="Process large files in chunks for better performance"
)

max_workers = st.sidebar.slider(
    "Max parallel workers", 
    min_value=1, 
    max_value=4, 
    value=2,
    help="Number of parallel threads for processing"
)

enable_pii_redaction = st.sidebar.checkbox(
    "Enable PII redaction", 
    value=security_config.get('redact_pii', True),
    help="Automatically redact personally identifiable information"
)

# Advanced settings
with st.sidebar.expander("🔬 Advanced Settings"):
    fuzzy_threshold = st.slider(
        "Fuzzy matching threshold", 
        min_value=50, 
        max_value=100, 
        value=config.get('scoring', {}).get('fuzzy_threshold', 80)
    )
    
    semantic_threshold = st.slider(
        "Semantic similarity threshold", 
        min_value=0.0, 
        max_value=1.0, 
        value=config.get('scoring', {}).get('semantic_threshold', 0.7),
        step=0.1
    )
    
    show_debug_info = st.checkbox("Show debug information", value=False)

# Main title
st.markdown('<h1 class="main-header">📞 Call Analysis Scorecard</h1>', unsafe_allow_html=True)

# File upload section
st.subheader("📁 Upload Call Recordings")

col1, col2 = st.columns([3, 1])

with col1:
    uploaded_files = st.file_uploader(
        "Select call recordings",
        type=audio_config.get('supported_formats', ['mp3', 'wav', 'm4a', 'flac']),
        accept_multiple_files=True,
        help=f"Supported formats: {', '.join(audio_config.get('supported_formats', ['mp3', 'wav']))}"
    )

with col2:
    if uploaded_files:
        st.metric("Files Selected", len(uploaded_files))
        total_size = sum(file.size for file in uploaded_files) / (1024 * 1024)
        st.metric("Total Size", f"{total_size:.1f} MB")

# Display file information
if uploaded_files:
    with st.expander("📋 File Information", expanded=False):
        for i, file in enumerate(uploaded_files):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**{file.name}**")
            with col2:
                st.write(f"{file.size / (1024*1024):.1f} MB")
            with col3:
                st.write(file.type or "Unknown")

# Processing section
if uploaded_files:
    
    # Clear previous results button
    if st.session_state["summary_pdfs"]:
        if st.button("🗑️ Clear Previous Results"):
            st.session_state["summary_pdfs"] = []
            st.session_state["processing_complete"] = False
            cleanup_temp_files(st.session_state.get("temp_files", []))
            st.session_state["temp_files"] = []
            st.rerun()
    
    # Start processing button
    process_button = st.button("🚀 Start Processing", type="primary", use_container_width=True)
    
    if process_button or not st.session_state["processing_complete"]:
        
        # Create audio samples directory
        os.makedirs("audio_samples", exist_ok=True)
        
        # Initialize progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        durations = []
        
        # Load Whisper model only once
        with st.spinner(f"Loading {model_size} Whisper model..."):
            set_model_size(model_size)
        
        # Process each file
        for i, uploaded_file in enumerate(uploaded_files, start=1):
            progress = (i - 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"Processing file {i} of {len(uploaded_files)}: {uploaded_file.name}")
            
            # Create expandable section for each file
            with st.expander(f"📁 {uploaded_file.name}", expanded=True):
                
                # Save audio file locally
                save_path = os.path.join("audio_samples", uploaded_file.name)
                try:
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.session_state["temp_files"].append(save_path)
                    
                    # Validate audio file
                    validation = validate_audio_file(save_path)
                    
                    if not validation['valid']:
                        st.markdown(
                            f'<div class="error-box">❌ <strong>File Validation Failed:</strong><br>{"<br>".join(validation["errors"])}</div>',
                            unsafe_allow_html=True
                        )
                        continue
                    
                    # Show warnings if any
                    if validation['warnings']:
                        st.markdown(
                            f'<div class="warning-box">⚠️ <strong>Warnings:</strong><br>{"<br>".join(validation["warnings"])}</div>',
                            unsafe_allow_html=True
                        )
                    
                    # Show file metadata
                    if show_debug_info and validation['metadata']:
                        metadata = validation['metadata']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Duration", f"{metadata.get('duration_minutes', 0):.1f} min")
                        with col2:
                            st.metric("Sample Rate", f"{metadata.get('sample_rate', 0)} Hz")
                        with col3:
                            st.metric("Channels", metadata.get('channels', 0))
                    
                    # Transcription
                    transcription_start = time.time()
                    with st.spinner("🎙️ Transcribing audio..."):
                        transcript = transcribe_audio(save_path)
                    
                    transcription_time = time.time() - transcription_start
                    durations.append(transcription_time)
                    
                    # Check for transcription errors
                    if transcript.startswith("[ERROR]"):
                        st.markdown(
                            f'<div class="error-box">❌ <strong>Transcription Failed:</strong><br>{transcript}</div>',
                            unsafe_allow_html=True
                        )
                        continue
                    
                    st.markdown(
                        f'<div class="success-box">✅ <strong>Transcription completed in {transcription_time:.1f} seconds</strong></div>',
                        unsafe_allow_html=True
                    )
                    
                    # Show ETA for remaining files
                    if len(durations) > 0 and i < len(uploaded_files):
                        eta = np.mean(durations) * (len(uploaded_files) - i)
                        status_text.text(f"⏳ Estimated time remaining: {eta:.0f} seconds")
                    
                    # Apply PII redaction if enabled
                    if enable_pii_redaction:
                        transcript = redact_pii(transcript)
                    
                    # Enhanced keyword detection
                    with st.spinner("🔍 Analyzing keywords..."):
                        keyword_matches = find_keywords_enhanced(transcript)
                    
                    # Highlight keywords in transcript
                    highlighted = transcript
                    offset = 0
                    
                    # Sort matches by position to avoid offset issues
                    keyword_matches_sorted = sorted(keyword_matches, key=lambda x: x["start"])
                    
                    for match in keyword_matches_sorted:
                        start = match["start"] + offset
                        end = match["end"] + offset
                        phrase = highlighted[start:end]
                        
                        # Color code by priority
                        color = {
                            'high_priority': '#ff6b6b',
                            'medium_priority': '#feca57', 
                            'low_priority': '#48dbfb'
                        }.get(match.get('priority', 'medium_priority'), '#feca57')
                        
                        confidence = match.get('confidence', 0)
                        title = f"Confidence: {confidence:.2f}, Priority: {match.get('priority', 'medium')}"
                        
                        highlight_html = f'<mark style="background-color: {color}; border-radius: 3px; padding: 2px;" title="{title}">{phrase}</mark>'
                        highlighted = highlighted[:start] + highlight_html + highlighted[end:]
                        offset += len(highlight_html) - len(phrase)
                    
                    # Display transcript with highlights
                    st.subheader("📝 Transcript with Highlighted Keywords")
                    st.markdown(highlighted, unsafe_allow_html=True)
                    
                    # Sentiment analysis
                    sentiment = get_sentiment(transcript)
                    sentiment_color = {
                        'Positive': 'green',
                        'Negative': 'red', 
                        'Neutral': 'gray'
                    }.get(sentiment, 'gray')
                    
                    st.markdown(f"**😊 Sentiment:** <span style='color: {sentiment_color}'>{sentiment}</span>", 
                               unsafe_allow_html=True)
                    
                    # Enhanced keywords display
                    if keyword_matches:
                        st.subheader("🔍 Detected Keywords")
                        
                        # Group by priority
                        keywords_by_priority = {}
                        for match in keyword_matches:
                            priority = match.get('priority', 'medium_priority')
                            if priority not in keywords_by_priority:
                                keywords_by_priority[priority] = []
                            keywords_by_priority[priority].append(match)
                        
                        for priority in ['high_priority', 'medium_priority', 'low_priority']:
                            if priority in keywords_by_priority:
                                priority_label = priority.replace('_', ' ').title()
                                color = {
                                    'high_priority': 'red',
                                    'medium_priority': 'orange',
                                    'low_priority': 'blue'
                                }.get(priority, 'gray')
                                
                                st.markdown(f"**<span style='color: {color}'>{priority_label}</span>:**", 
                                           unsafe_allow_html=True)
                                
                                for match in keywords_by_priority[priority]:
                                    confidence = match.get('confidence', 0)
                                    match_type = match.get('match_type', 'exact')
                                    st.markdown(f"- **{match['phrase']}** (confidence: {confidence:.2f}, {match_type} match)")
                    else:
                        st.markdown("**✅ No significant keywords detected.**")
                    
                    # QA Scoring
                    st.subheader("📊 QA Scoring Analysis")
                    
                    # Rule-based scoring
                    with st.spinner("Calculating rule-based scores..."):
                        qa_results = score_call_rule_based(transcript, call_type)
                    
                    # NLP-enhanced scoring
                    with st.spinner("Performing NLP analysis..."):
                        qa_results_nlp = score_call_nlp_enhanced(transcript, call_type)
                    
                    # Display scoring results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🔍 Rule-Based Scoring")
                        rule_total = 0
                        for section, result in qa_results.items():
                            emoji = "✅" if result["score"] >= 1 else "❌"
                            confidence = result.get('confidence', 0)
                            st.markdown(f"- {emoji} **{section}**: {result['explanation']}")
                            if show_debug_info:
                                st.markdown(f"  *Confidence: {confidence:.2f}*")
                            rule_total += result['score']
                        
                        st.markdown(f"**🏁 Total Rule-Based Score: {rule_total}/{len(qa_results)}**")
                    
                    with col2:
                        st.markdown("#### 🧠 NLP-Enhanced Scoring")
                        nlp_total = 0
                        for section, result in qa_results_nlp.items():
                            emoji = "✅" if result["score"] >= 1 else "❌"
                            confidence = result.get('confidence', 0)
                            st.markdown(f"- {emoji} **{section}**: {result['explanation']}")
                            if show_debug_info:
                                st.markdown(f"  *Confidence: {confidence:.2f}*")
                            nlp_total += result['score']
                        
                        st.markdown(f"**🏁 Total NLP Score: {nlp_total}/{len(qa_results_nlp)}**")
                    
                    # NLP Insights (if debug mode is enabled)
                    if show_debug_info:
                        with st.expander("🔬 Advanced NLP Insights", expanded=False):
                            insights = extract_nlp_insights(transcript)
                            
                            if insights['entities']:
                                st.markdown("**Named Entities:**")
                                for entity in insights['entities'][:10]:  # Limit to first 10
                                    st.markdown(f"- {entity['text']} ({entity['label']})")
                            
                            if insights['emotional_indicators']:
                                st.markdown("**Emotional Indicators:**")
                                for indicator in insights['emotional_indicators'][:5]:  # Limit to first 5
                                    st.markdown(f"- {indicator['word']}: {indicator['context']}")
                            
                            st.markdown(f"**Text Complexity Score:** {insights['complexity_score']:.2f}")
                    
                    # Store results for PDF generation
                    st.session_state["summary_pdfs"].append({
                        "filename": uploaded_file.name,
                        "transcript": transcript,
                        "sentiment": sentiment,
                        "keywords": [match["phrase"] for match in keyword_matches],
                        "qa_results": qa_results,
                        "qa_results_nlp": qa_results_nlp,
                        "processing_time": transcription_time,
                        "metadata": validation.get('metadata', {})
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing {uploaded_file.name}: {e}")
                    st.markdown(
                        f'<div class="error-box">❌ <strong>Processing Error:</strong><br>{str(e)}</div>',
                        unsafe_allow_html=True
                    )
        
        # Complete processing
        progress_bar.progress(1.0)
        status_text.text("✅ Processing complete!")
        st.session_state["processing_complete"] = True
        
        # Show summary statistics
        if st.session_state["summary_pdfs"]:
            st.subheader("📈 Processing Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Files Processed", len(st.session_state["summary_pdfs"]))
            with col2:
                avg_time = np.mean([call.get('processing_time', 0) for call in st.session_state["summary_pdfs"]])
                st.metric("Avg Processing Time", f"{avg_time:.1f}s")
            with col3:
                total_rule_score = sum(sum(call['qa_results'][section]['score'] for section in call['qa_results']) 
                                     for call in st.session_state["summary_pdfs"])
                max_rule_score = len(st.session_state["summary_pdfs"]) * 5  # Assuming 5 categories
                st.metric("Overall Rule Score", f"{total_rule_score}/{max_rule_score}")
            with col4:
                total_nlp_score = sum(sum(call['qa_results_nlp'][section]['score'] for section in call['qa_results_nlp']) 
                                    for call in st.session_state["summary_pdfs"])
                max_nlp_score = len(st.session_state["summary_pdfs"]) * 5  # Assuming 5 categories
                st.metric("Overall NLP Score", f"{total_nlp_score}/{max_nlp_score}")

# PDF Export section
if st.session_state["summary_pdfs"]:
    st.subheader("📄 Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Individual Call Reports:**")
        for idx, call in enumerate(st.session_state["summary_pdfs"]):
            if st.button(f"📥 Download PDF: {call['filename']}", key=f"download_{idx}"):
                with st.spinner("Generating PDF..."):
                    pdf_bytes = generate_pdf_report(
                        title=f"Call Analysis Report – {call['filename']}",
                        transcript=call["transcript"],
                        sentiment=call["sentiment"],
                        keywords=call["keywords"],
                        qa_results=call["qa_results"],
                        qa_results_nlp=call["qa_results_nlp"]
                    )
                st.download_button(
                    label=f"📥 Save {call['filename']}_report.pdf",
                    data=pdf_bytes,
                    file_name=f"{call['filename']}_report.pdf",
                    mime="application/pdf",
                    key=f"save_{idx}"
                )
    
    with col2:
        st.markdown("**Combined Summary Report:**")
        if st.button("📄 Generate Combined Report", type="primary"):
            with st.spinner("Generating combined PDF report..."):
                combined_bytes = generate_combined_pdf_report(st.session_state["summary_pdfs"])
            
            st.download_button(
                label="📥 Download Combined Report",
                data=combined_bytes,
                file_name="Combined_Call_Analysis_Report.pdf",
                mime="application/pdf",
                key="combined_report"
            )

# Test mode section
st.sidebar.markdown("---")
if st.sidebar.checkbox("🧪 Test Mode"):
    st.subheader("🧪 Test with Sample Transcript")
    
    # Sample transcript for testing
    sample_transcript = st.text_area(
        "Sample transcript:",
        value=(
            "Hello, I'm really struggling to pay. I've been in hospital with anxiety and side effects from surgery. "
            "I was signed off work. Can you help? I feel vulnerable and might need breathing space. "
            "I want to file a complaint about the last agent who refused to help. "
            "Hi, I'm not sure I really understood the last part — could you go over that again? I've been off work recovering from surgery and feeling quite anxious lately. I'm struggling financially after losing my job and I'm behind on rent. Can you help me work out a payment plan or pause things for now? I appreciate you explaining the options clearly. "
            "We're here to help you through this difficult time. Let me explain your options clearly so you understand what's available. "
            "We can set up a payment plan that works for your situation and we won't pressure you into anything. "
            "Since you mentioned feeling vulnerable, we can send you a breathing space form and pause your account while you recover."
        ),
        height=200
    )
    
    if st.button("🔬 Analyze Test Transcript"):
        with st.spinner("Analyzing test transcript..."):
            # Apply PII redaction if enabled
            test_transcript = redact_pii(sample_transcript) if enable_pii_redaction else sample_transcript
            
            # Sentiment analysis
            sentiment = get_sentiment(test_transcript)
            st.markdown(f"**😊 Sentiment:** {sentiment}")
            
            # Enhanced keyword detection
            keywords_found = find_keywords_enhanced(test_transcript)
            
            if keywords_found:
                st.markdown("**🔍 Keywords Detected:**")
                for match in keywords_found[:10]:  # Limit display
                    confidence = match.get('confidence', 0)
                    priority = match.get('priority', 'medium_priority').replace('_', ' ').title()
                    st.markdown(f"- **{match['phrase']}** (confidence: {confidence:.2f}, {priority})")
            else:
                st.markdown("**✅ No significant keywords detected.**")
            
            # QA Scoring
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔍 Rule-Based Test Results")
                qa_results = score_call_rule_based(test_transcript, call_type)
                rule_total = 0
                for section, result in qa_results.items():
                    emoji = "✅" if result["score"] >= 1 else "❌"
                    confidence = result.get('confidence', 0)
                    st.markdown(f"- {emoji} **{section}**: {result['explanation']}")
                    if show_debug_info:
                        st.markdown(f"  *Confidence: {confidence:.2f}*")
                    rule_total += result['score']
                st.markdown(f"**🏁 Total Rule Score: {rule_total}/{len(qa_results)}**")
            
            with col2:
                st.markdown("#### 🧠 NLP-Enhanced Test Results")
                qa_results_nlp = score_call_nlp_enhanced(test_transcript, call_type)
                nlp_total = 0
                for section, result in qa_results_nlp.items():
                    emoji = "✅" if result["score"] >= 1 else "❌"
                    confidence = result.get('confidence', 0)
                    st.markdown(f"- {emoji} **{section}**: {result['explanation']}")
                    if show_debug_info:
                        st.markdown(f"  *Confidence: {confidence:.2f}*")
                    nlp_total += result['score']
                st.markdown(f"**🧠 Total NLP Score: {nlp_total}/{len(qa_results_nlp)}**")
            
            # Advanced insights in test mode
            if show_debug_info:
                with st.expander("🔬 Test NLP Insights", expanded=False):
                    insights = extract_nlp_insights(test_transcript)
                    st.json(insights)

# Footer with system information
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 System Information")

# Show configuration status
config_status = "✅ Loaded" if config else "❌ Missing"
st.sidebar.markdown(f"**Configuration:** {config_status}")

# Show model status
try:
    import whisper
    st.sidebar.markdown(f"**Whisper Model:** {model_size}")
except ImportError:
    st.sidebar.markdown("**Whisper Model:** ❌ Not available")

# Show security features
security_features = []
if enable_pii_redaction:
    security_features.append("PII Redaction")
if security_config.get('secure_temp_files', False):
    security_features.append("Secure Files")
if security_config.get('auto_cleanup', True):
    security_features.append("Auto Cleanup")

if security_features:
    st.sidebar.markdown(f"**Security:** {', '.join(security_features)}")
else:
    st.sidebar.markdown("**Security:** Basic")

# Cleanup on app close
if st.sidebar.button("🧹 Clean Temp Files"):
    cleanup_temp_files(st.session_state.get("temp_files", []))
    st.session_state["temp_files"] = []
    st.sidebar.success("Temporary files cleaned up!")

# Help section
with st.sidebar.expander("❓ Help & Tips"):
    st.markdown("""
    **Tips for best results:**
    - Use clear, high-quality audio recordings
    - Supported formats: MP3, WAV, M4A, FLAC
    - Enable PII redaction for sensitive calls
    - Use parallel processing for large files
    - Check debug mode for detailed insights
    
    **Scoring System:**
    - Rule-based: Pattern matching
    - NLP-enhanced: Semantic analysis
    - Confidence scores show match quality
    
    **Keywords:**
    - High priority: Red highlights
    - Medium priority: Yellow highlights  
    - Low priority: Blue highlights
    """)

st.sidebar.markdown("---")
st.sidebar.markdown("**Version:** 2.0 Enhanced | **Status:** Production Ready")
