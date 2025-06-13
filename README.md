# 🎧 Enhanced Call Analysis App

A comprehensive Streamlit-based application for transcribing, analyzing, and scoring call recordings with advanced NLP capabilities and security features. Designed to support internal QA processes and compliance with FCA expectations.

## 🚀 New Features (v2.0)

### 🧠 Enhanced NLP Analysis
- **Semantic similarity matching** using spaCy embeddings
- **Advanced keyword detection** with confidence scoring and fuzzy matching
- **Entity recognition** and concept extraction
- **Sentiment analysis** with sentence-level breakdown
- **Text complexity scoring** and emotional indicator detection

### 🔧 Improved Audio Processing
- **Multi-format support**: MP3, WAV, M4A, FLAC, AAC, OGG
- **Parallel processing** for large files with automatic chunking
- **Audio preprocessing**: normalization, noise reduction, format optimization
- **Robust error handling** with detailed validation and metadata extraction

### 🔒 Security & Privacy
- **PII redaction** with configurable patterns (phone numbers, emails, postcodes, account numbers)
- **Secure file handling** with optional encryption
- **Automatic cleanup** of temporary files with secure deletion
- **Audit logging** for compliance tracking

### ⚙️ Configuration Management
- **YAML-based configuration** for easy customization
- **Adjustable scoring thresholds** for different use cases
- **Configurable keyword priorities** and detection rules
- **Flexible audio processing settings**

## 📋 Core Features

- 🎙️ **Advanced Transcription** using OpenAI Whisper with multiple model sizes
- 😊 **Sentiment Analysis** using VADER with sentence-level breakdown
- 🧠 **Intelligent Keyword Detection** with priority-based scoring and fuzzy matching
- ✅ **Dual QA Scoring System**:
  - Rule-based scoring for compliance checking
  - NLP-enhanced scoring using semantic analysis
- 🔇 **Audio Quality Analysis** with metadata extraction
- 🕵️ **PII Redaction** with configurable patterns
- 📊 **Visual Dashboard** with color-coded results and confidence scores
- 🔎 **Advanced Search** and filtering capabilities
- 📄 **Comprehensive PDF Reports** with individual and combined exports

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/CallAnalysisApp.git
cd CallAnalysisApp
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Download spaCy model:**
```bash
python -m spacy download en_core_web_sm
```

4. **Configure the application:**
   - Copy `config.yaml` to your project directory
   - Adjust settings as needed for your use case

## 🚀 Usage

### Basic Usage
```bash
streamlit run app.py
```

### Advanced Configuration

Edit `config.yaml` to customize:

```yaml
scoring:
  fuzzy_threshold: 80          # Fuzzy matching sensitivity
  semantic_threshold: 0.7      # Semantic similarity threshold
  keyword_confidence_threshold: 0.6

security:
  redact_pii: true            # Enable PII redaction
  secure_temp_files: true     # Encrypt temporary files
  auto_cleanup: true          # Secure deletion of temp files

audio:
  max_file_size_mb: 100       # Maximum file size
  chunk_duration_minutes: 10  # Chunk size for large files
  normalize_audio: true       # Audio preprocessing
```

## 📊 Scoring Framework

### Rule-Based Scoring
- **Customer Understanding**: Clear explanations and confirmation of understanding
- **Fair Treatment**: Respectful and supportive language
- **Vulnerability Handling**: Appropriate response to vulnerable customer indicators
- **Financial Difficulty**: Suitable options and flexibility offered
- **Resolution & Support**: Proper escalation and follow-up procedures

### NLP-Enhanced Scoring
- **Semantic Analysis**: Understanding context and meaning beyond exact phrases
- **Entity Recognition**: Identifying relevant entities and concepts
- **Confidence Scoring**: Quantifying the certainty of matches
- **Concept Mapping**: Linking related ideas and themes

## 🔒 Security Features

### PII Redaction Patterns
- **Phone Numbers**: UK format detection and redaction
- **Email Addresses**: Comprehensive email pattern matching
- **Postcodes**: UK postcode format recognition
- **Account Numbers**: Financial account number patterns
- **Sort Codes**: UK banking sort code format

### Secure File Handling
- **Encryption**: Optional file encryption for sensitive data
- **Secure Deletion**: Overwrite files with random data before deletion
- **Audit Logging**: Track file access and processing activities
- **Access Control**: Configurable security levels

## 📈 Performance Optimization

### Parallel Processing
- **Automatic Chunking**: Large files split into manageable segments
- **Multi-threading**: Concurrent processing of audio chunks
- **Resource Management**: Efficient memory and CPU usage
- **Progress Tracking**: Real-time status updates and ETA calculation

### Caching
- **Model Caching**: Whisper and spaCy models cached for reuse
- **Configuration Caching**: Settings loaded once and cached
- **Result Caching**: Intermediate results stored for efficiency

## 🧪 Testing

### Test Mode
The application includes a built-in test mode with sample transcripts:
- Enable "Test Mode" in the sidebar
- Analyze sample calls with different scenarios
- Compare rule-based vs. NLP-enhanced scoring
- Debug with detailed confidence scores and insights

### Validation
- **Audio File Validation**: Format, size, and quality checks
- **Transcript Validation**: Content analysis and error detection
- **Scoring Validation**: Confidence thresholds and quality metrics

## 📄 Output Formats

### Individual Reports
- **Detailed Analysis**: Complete transcript with highlighted keywords
- **Scoring Breakdown**: Section-by-section analysis with explanations
- **Metadata**: File information, processing time, and quality metrics
- **Visual Elements**: Color-coded results and confidence indicators

### Combined Reports
- **Summary Dashboard**: Overview of all processed calls
- **Comparative Analysis**: Side-by-side scoring comparisons
- **Trend Analysis**: Patterns across multiple calls
- **Executive Summary**: High-level insights and recommendations

## 🔧 Configuration Options

### Scoring Thresholds
```yaml
scoring:
  fuzzy_threshold: 80          # 0-100, higher = more strict
  semantic_threshold: 0.7      # 0-1, higher = more strict
  keyword_confidence_threshold: 0.6  # 0-1, minimum confidence
```

### Audio Processing
```yaml
audio:
  supported_formats: [mp3, wav, m4a, flac, aac, ogg]
  max_file_size_mb: 100
  chunk_duration_minutes: 10
  normalize_audio: true
  noise_reduction: true
```

### Security Settings
```yaml
security:
  redact_pii: true
  secure_temp_files: true
  auto_cleanup: true
  encryption_key_file: "encryption.key"
```

## 🐛 Troubleshooting

### Common Issues

1. **spaCy Model Not Found**
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **Audio Format Not Supported**
   - Check `config.yaml` for supported formats
   - Install additional codecs if needed

3. **Memory Issues with Large Files**
   - Reduce `chunk_duration_minutes` in config
   - Lower `max_workers` for parallel processing

4. **Transcription Quality Issues**
   - Use higher quality audio files
   - Enable audio preprocessing in config
   - Try a larger Whisper model

### Debug Mode
Enable debug mode in the sidebar to see:
- Detailed confidence scores
- NLP entity recognition results
- Audio file metadata
- Processing performance metrics

## 📚 Dependencies

### Core Libraries
- **Streamlit**: Web application framework
- **OpenAI Whisper**: Speech-to-text transcription
- **spaCy**: Advanced NLP processing
- **VADER Sentiment**: Sentiment analysis
- **PyDub**: Audio file processing
- **FPDF2**: PDF generation

### Security Libraries
- **Cryptography**: File encryption
- **PyYAML**: Configuration management
- **Pathlib**: Secure file handling

### Performance Libraries
- **scikit-learn**: Machine learning utilities
- **concurrent.futures**: Parallel processing
- **asyncio**: Asynchronous operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and support:
- Check the troubleshooting section
- Review configuration options
- Enable debug mode for detailed logs
- Create an issue on GitHub with detailed information

## 🔄 Version History

### v2.0 (Current)
- Enhanced NLP analysis with semantic similarity
- Improved audio processing with multiple format support
- Advanced security features and PII redaction
- Configuration management system
- Performance optimizations

### v1.0
- Basic transcription and keyword detection
- Simple QA scoring system
- PDF export functionality
- Basic audio file support

---

**Made with ❤️ for call center quality assurance and compliance**
