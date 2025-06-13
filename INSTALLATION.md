# 🚀 Installation Guide

## 📋 System Requirements
- **Python**: 3.8 - 3.12 (tested on 3.12)
- **Operating System**: Windows 10/11, macOS, Linux
- **Memory**: 4GB RAM minimum (8GB recommended for large files)
- **Storage**: 2GB free space for models and dependencies

## 🔧 Step-by-Step Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/CallAnalysisApp.git
cd CallAnalysisApp
```

### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv call_analysis_env

# Activate virtual environment
# Windows:
call_analysis_env\Scripts\activate
# Mac/Linux:
source call_analysis_env/bin/activate
```

### 3. Upgrade pip and Install Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install requirements (this handles NumPy compatibility automatically)
pip install -r requirements.txt

# Install PyTorch with CPU support (if above fails)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 4. Download spaCy Language Model
```bash
# Download English language model
python -m spacy download en_core_web_sm

# Optional: Download larger model for better semantic analysis
python -m spacy download en_core_web_md
```

### 5. Install System Dependencies (If Needed)

**For Audio Processing:**

**Windows:** Usually no additional setup needed

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 6. Test Installation
```bash
# Quick test
python -c "import streamlit, whisper, spacy, torch; print('✅ All dependencies installed successfully!')"

# Run the app
streamlit run app.py
```

## 🚨 Common Installation Issues & Solutions

### Issue 1: NumPy Compatibility Error
**Error:** `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x`

**Solution:**
```bash
pip install "numpy<2.0.0"
```

### Issue 2: PyTorch Version Issues
**Error:** `Could not find a version that satisfies the requirement torch==X.X.X`

**Solution:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Issue 3: spaCy Model Not Found
**Error:** `Can't find model 'en_core_web_sm'`

**Solution:**
```bash
python -m spacy download en_core_web_sm
```

### Issue 4: Cryptography Installation Fails
**Error:** `Failed building wheel for cryptography`

**Solutions:**
- **Windows:** Install Microsoft C++ Build Tools
- **macOS:** `xcode-select --install`
- **Linux:** `sudo apt-get install build-essential libffi-dev python3-dev`

**Alternative:** Disable cryptography features by commenting out security imports in `analyser.py`

### Issue 5: Audio Format Not Supported
**Error:** Audio file cannot be processed

**Solution:** Install ffmpeg (see system dependencies above)

## 🔍 Verification Checklist

After installation, verify everything works:

- [ ] App starts without errors: `streamlit run app.py`
- [ ] Can upload audio files (test with a small MP3/WAV)
- [ ] Transcription works (try test mode in sidebar)
- [ ] Sentiment analysis shows results
- [ ] QA scoring displays properly
- [ ] PDF export functions work

## 🎯 Quick Start Test

1. **Start the app:** `streamlit run app.py`
2. **Enable test mode** in the sidebar
3. **Click "Analyze Test Transcript"**
4. **Verify you see sentiment, keywords, and scoring results**

If all tests pass, your installation is complete! 🎉

## 🆘 Still Having Issues?

1. **Check Python version:** `python --version`
2. **Verify virtual environment is active**
3. **Try minimal installation:** Install only core packages first
4. **Check system requirements** and install missing dependencies
5. **Create an issue** on GitHub with your error message and system info

## 📊 Performance Notes

- **First run** may be slow (downloads models)
- **Large audio files** (>10 minutes) will take longer to process
- **Enable parallel processing** in sidebar for better performance
- **Use smaller Whisper models** (base/small) for faster transcription
