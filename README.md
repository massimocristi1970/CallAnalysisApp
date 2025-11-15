# 🎧 Enhanced Call Analysis App with Performance Dashboard

A comprehensive Streamlit-based application for transcribing, analyzing, and scoring call recordings with advanced NLP capabilities, persistent data storage, and comprehensive performance tracking. Designed to support internal QA processes and compliance with FCA expectations.

## 🚀 New Features (v2.1) - Dashboard Edition

### 📊 Performance Dashboard System
- **Flexible database storage** - SQLite (local) or Supabase (cloud PostgreSQL)
- **Agent performance tracking** by month with historical trends
- **Interactive dashboard** with 5 different views (Overview, Agent Performance, Monthly Trends, Category Analysis, Individual Agent)
- **Real-time performance metrics** with color-coded indicators
- **Data export capabilities** (JSON, PDF, CSV)
- **Comparative analysis** between agents and scoring methods

### 👤 Agent Management
- **Agent information capture** (name, department, call date)
- **Historical performance tracking** with monthly summaries
- **Individual agent deep-dive analysis**
- **Department-based categorization**
- **Performance improvement tracking over time**

### 📈 Advanced Analytics
- **Monthly trend analysis** with interactive charts
- **Performance heatmaps** showing agent progress
- **Category breakdown analysis** (Customer Understanding, Fair Treatment, etc.)
- **Sentiment distribution tracking**
- **Call volume and duration analytics**

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
- 👤 **Agent Performance Tracking** with historical data storage
- 📊 **Interactive Dashboard** with comprehensive analytics
- 🔇 **Audio Quality Analysis** with metadata extraction
- 🕵️ **PII Redaction** with configurable patterns
- 📊 **Visual Dashboard** with color-coded results and confidence scores
- 🔎 **Advanced Search** and filtering capabilities
- 📄 **Comprehensive PDF Reports** with individual and combined exports
- 💾 **Persistent Data Storage** using SQLite (local) or Supabase (cloud)

## 🛠️ Installation

### Prerequisites
- **Python**: 3.8 - 3.12 (tested on 3.12)
- **Operating System**: Windows 10/11, macOS, Linux
- **Memory**: 4GB RAM minimum (8GB recommended for large files)
- **Storage**: 2GB free space for models and dependencies

### Quick Setup

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

4. **Configure database (choose one):**
   
   **Option A: Local SQLite (Default)**
   - No additional configuration needed
   - Database file created automatically as `call_analysis.db`
   
   **Option B: Supabase (Cloud PostgreSQL)**
   - **Quick Start**: See [QUICK_START_SUPABASE.md](QUICK_START_SUPABASE.md) (5 minutes)
   - **Full Guide**: See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for detailed instructions
   - **Migration**: See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) to migrate existing data

5. **Configure the application:**
   - The `config.yaml` file contains all settings
   - Adjust settings as needed for your use case

## 🚀 Running the System

### Option 1: Dual App Setup (Recommended)

**Terminal 1 - Main Analysis App:**
```bash
streamlit run app.py --server.port 8501
```

**Terminal 2 - Performance Dashboard:**
```bash
streamlit run dashboard.py --server.port 8503
```

**Access URLs:**
- **Call Analysis**: http://localhost:8501
- **Performance Dashboard**: http://localhost:8503

### Option 2: Single Session Testing
Run just the main app first to test functionality:
```bash
streamlit run app.py
```

## 📊 System Architecture

### File Structure
```
CallAnalysisApp/
├── app.py                 # Main call analysis interface
├── dashboard.py           # Performance dashboard
├── database.py            # Database management (SQLite/Supabase)
├── analyser.py           # NLP analysis and scoring
├── transcriber.py        # Audio processing and transcription
├── pdf_exporter.py       # PDF report generation
├── config.yaml           # Configuration settings
├── .env.example          # Environment variables template
├── SUPABASE_SETUP.md     # Supabase configuration guide
├── requirements.txt      # Python dependencies
├── call_analysis.db      # SQLite database (if using local)
└── audio_samples/        # Temporary audio file storage
```

### Database Options

The application supports two database backends:

**1. SQLite (Local)**
- Default option, no configuration required
- Data stored locally in `call_analysis.db` file
- Perfect for single-user or development use
- No internet connection required

**2. Supabase (Cloud PostgreSQL)**
- Cloud-based PostgreSQL database
- Multi-user support with proper authentication
- Accessible from anywhere
- Automatic backups (paid plans)
- See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for setup instructions

### Database Schema
- **agents**: Agent information and department tracking
- **calls**: Individual call records with transcripts and metadata
- **keywords**: Detected keywords with confidence scores
- **qa_scores**: Rule-based and NLP scoring results
- **monthly_summaries**: Pre-calculated performance statistics

## 💼 Usage Workflow

### 1. Agent Setup & Call Analysis

1. **Enter Agent Information** (sidebar):
   - Agent name (required for database saving)
   - Call date
   - Department selection

2. **Upload Audio Files**:
   - Drag and drop or browse for files
   - Supports: MP3, WAV, M4A, FLAC, AAC, OGG
   - Maximum file size: 100MB (configurable)

3. **Configure Analysis Settings**:
   - Select Whisper model size (base/small/medium/large)
   - Choose call type (Customer Service/Collections/Sales/Support)
   - Enable/disable PII redaction
   - Adjust processing settings

4. **Process Calls**:
   - Click "🚀 Start Processing"
   - Monitor real-time progress
   - View results with highlighted keywords
   - Automatic database saving

### 2. Performance Monitoring (Dashboard)

1. **Overview Dashboard**: 
   - Total agents and calls
   - Average performance scores
   - Monthly call volume trends
   - Overall performance indicators

2. **Agent Performance View**:
   - Side-by-side agent comparison
   - Performance cards with color coding
   - Detailed statistics table
   - Sentiment distribution analysis

3. **Monthly Trends Analysis**:
   - Score progression over time
   - Performance heatmaps
   - Call volume trends
   - Month-over-month improvement tracking

4. **Category Analysis**:
   - QA category breakdown
   - Rule-based vs NLP scoring comparison
   - Best/worst performing categories
   - Improvement opportunities identification

5. **Individual Agent Deep Dive**:
   - Personal performance metrics
   - Historical trend analysis
   - Monthly performance detail
   - Progress tracking over time

### 3. Data Export & Reporting

1. **PDF Reports**:
   - Individual call analysis reports
   - Combined summary reports
   - Comprehensive formatting with charts

2. **Dashboard Data Export**:
   - JSON format for external analysis
   - Raw data for spreadsheet import
   - Performance metrics for reporting

## ⚙️ Configuration Options

### Scoring Thresholds (config.yaml)
```yaml
scoring:
  fuzzy_threshold: 80          # 0-100, keyword matching sensitivity
  semantic_threshold: 0.7      # 0-1, NLP similarity threshold
  keyword_confidence_threshold: 0.6  # 0-1, minimum confidence level
```

### Audio Processing Settings
```yaml
audio:
  supported_formats: [mp3, wav, m4a, flac, aac, ogg]
  max_file_size_mb: 100
  chunk_duration_minutes: 10   # For large file processing
  normalize_audio: true        # Audio preprocessing
  noise_reduction: true
```

### Security Configuration
```yaml
security:
  redact_pii: true            # Enable PII redaction
  secure_temp_files: true     # Encrypt temporary files
  auto_cleanup: true          # Secure file deletion
```

### Agent Behavior Phrases (Customizable)
```yaml
agent_behaviour_phrases:
  Customer Understanding:
    - "do you understand"
    - "let me explain"
    - "does that make sense"
  Fair Treatment:
    - "we're here to help"
    - "take your time"
    - "you have options"
```

## 📊 Scoring Framework

### Rule-Based Scoring
Evaluates calls based on exact phrase matching and pattern recognition:
- **Customer Understanding**: Clear explanations and confirmation of understanding
- **Fair Treatment**: Respectful and supportive language
- **Vulnerability Handling**: Appropriate response to vulnerable customer indicators
- **Financial Difficulty**: Suitable options and flexibility offered
- **Resolution & Support**: Proper escalation and follow-up procedures

### NLP-Enhanced Scoring
Uses advanced semantic analysis for contextual understanding:
- **Semantic Analysis**: Understanding context and meaning beyond exact phrases
- **Entity Recognition**: Identifying relevant entities and concepts
- **Confidence Scoring**: Quantifying the certainty of matches
- **Concept Mapping**: Linking related ideas and themes

### Performance Indicators
- 🟢 **Excellent**: ≥80% score (Green indicators)
- 🔵 **Good**: 60-79% score (Blue indicators)
- 🟡 **Average**: 40-59% score (Yellow indicators)
- 🔴 **Needs Improvement**: <40% score (Red indicators)

## 🔒 Security Features

### PII Redaction Patterns
- **Phone Numbers**: UK format detection and redaction
- **Email Addresses**: Comprehensive email pattern matching
- **Postcodes**: UK postcode format recognition
- **Account Numbers**: Financial account number patterns
- **Sort Codes**: UK banking sort code format

### Data Protection
- **Secure File Handling**: Optional encryption for sensitive data
- **Automatic Cleanup**: Secure deletion with data overwriting
- **Audit Logging**: Track all file access and processing
- **Access Control**: Configurable security levels

## 📈 Performance Optimization

### Processing Features
- **Parallel Processing**: Automatic chunking for large files
- **Multi-threading**: Concurrent audio processing
- **Resource Management**: Efficient memory and CPU usage
- **Progress Tracking**: Real-time status and ETA

### Caching System
- **Model Caching**: Whisper and spaCy models cached for reuse
- **Configuration Caching**: Settings loaded once per session
- **Dashboard Caching**: 5-minute cache for dashboard queries

## 🧪 Testing & Development

### Built-in Test Mode
- Enable "Test Mode" in sidebar
- Analyze sample transcripts
- Compare scoring methods
- Debug with detailed insights

### Sample Data Generation
- Generate realistic test data for multiple agents
- Create 6 months of performance history
- Populate dashboard for demonstration

### Validation Features
- **Audio File Validation**: Format, size, and quality checks
- **Transcript Validation**: Content analysis and error detection
- **Scoring Validation**: Confidence thresholds and quality metrics

## 📄 Output Formats

### Individual Call Reports
- **Detailed Analysis**: Complete transcript with highlighted keywords
- **Scoring Breakdown**: Category-by-category analysis with explanations
- **Metadata**: File information, processing time, quality metrics
- **Visual Elements**: Color-coded results and confidence indicators

### Dashboard Analytics
- **Performance Metrics**: Real-time agent and overall statistics
- **Trend Analysis**: Historical performance tracking
- **Comparative Reports**: Agent-to-agent comparisons
- **Export Options**: JSON, PDF, and raw data formats

### Combined Reports
- **Summary Dashboard**: Overview of all processed calls
- **Trend Analysis**: Patterns across multiple calls and time periods
- **Executive Summary**: High-level insights and recommendations

## 🔧 Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Reset database connections
pkill -f streamlit
rm call_analysis.db-wal call_analysis.db-shm
```

**2. Dashboard Not Loading Data**
- Check agent name is entered correctly
- Verify database file exists
- Clear Streamlit cache: Settings > Clear Cache

**3. Audio Processing Failures**
- Check file format is supported
- Verify file size under limit
- Ensure sufficient disk space

**4. spaCy Model Issues**
```bash
python -m spacy download en_core_web_sm
```

### Debug Mode
Enable in sidebar Advanced Settings:
- Detailed confidence scores
- NLP entity recognition results
- Audio file metadata
- Processing performance metrics

### Performance Issues
- Reduce chunk duration for large files
- Use smaller Whisper models for speed
- Enable parallel processing
- Check available memory

## 🔄 Data Management

### Database Operations
- **Automatic Backup**: Regular database snapshots
- **Data Export**: Full data export capabilities
- **Agent Management**: Add, update, deactivate agents
- **Performance History**: Complete historical tracking

### File Management
- **Temporary File Cleanup**: Automatic secure deletion
- **Storage Optimization**: Efficient file handling
- **Archive Management**: Long-term data storage options

## 🌟 Best Practices

### For Optimal Performance
1. **Use high-quality audio files** (clear recording, minimal background noise)
2. **Enable audio preprocessing** for better transcription accuracy
3. **Choose appropriate Whisper model** (balance speed vs accuracy)
4. **Enter complete agent information** for proper tracking
5. **Regular database maintenance** and backups

### For Security Compliance
1. **Enable PII redaction** for all sensitive calls
2. **Use secure file handling** in production environments
3. **Regular audit log reviews** for compliance tracking
4. **Implement access controls** for multi-user deployments

### For Dashboard Insights
1. **Consistent agent naming** for accurate tracking
2. **Regular data entry** for meaningful trends
3. **Use date ranges** for focused analysis
4. **Export data regularly** for external reporting

## 📚 Dependencies

### Core Libraries
- **Streamlit**: Web application framework
- **OpenAI Whisper**: Speech-to-text transcription
- **spaCy**: Advanced NLP processing
- **VADER Sentiment**: Sentiment analysis
- **PyDub**: Audio file processing
- **FPDF2**: PDF generation

### Database & Analytics
- **SQLite3**: Database management
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive dashboard visualizations
- **NumPy**: Numerical computations

### Security Libraries
- **Cryptography**: File encryption
- **PyYAML**: Configuration management
- **Pathlib**: Secure file handling

### Performance Libraries
- **scikit-learn**: Machine learning utilities
- **concurrent.futures**: Parallel processing
- **asyncio**: Asynchronous operations

## 🆘 Support & Maintenance

### Getting Help
- Check troubleshooting section for common issues
- Enable debug mode for detailed diagnostics
- Review log files for error details
- Test with sample data to isolate problems

### System Requirements
- **Minimum**: 4GB RAM, Python 3.8+, 2GB storage
- **Recommended**: 8GB RAM, Python 3.11+, SSD storage
- **Network**: Internet connection for model downloads

### Updates & Versioning
- **Current Version**: 2.1 Enhanced with Dashboard
- **Update Process**: Pull latest code, install dependencies
- **Database Migration**: Automatic schema updates
- **Configuration**: Backward compatible settings

## 🤝 Contributing

We welcome contributions to improve the call analysis system:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Make changes** with appropriate tests
4. **Submit pull request** with detailed description

### Development Guidelines
- Follow Python PEP 8 style guidelines
- Add tests for new functionality
- Update documentation for changes
- Ensure backward compatibility

## 🔄 Version History

### v2.1 (Current) - Dashboard Edition
- Added comprehensive performance dashboard
- Implemented SQLite database for persistent storage
- Agent performance tracking and historical analysis
- Interactive charts and analytics
- Enhanced data export capabilities

### v2.0 - Enhanced NLP Edition
- Enhanced NLP analysis with semantic similarity
- Improved audio processing with multiple format support
- Advanced security features and PII redaction
- Configuration management system
- Performance optimizations

### v1.0 - Initial Release
- Basic transcription and keyword detection
- Simple QA scoring system
- PDF export functionality
- Basic audio file support

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI Whisper** for speech-to-text capabilities
- **spaCy** for advanced NLP processing
- **Streamlit** for the interactive web interface
- **VADER Sentiment** for sentiment analysis
- **Plotly** for interactive dashboard visualizations

---

**Version**: 2.1 Enhanced Dashboard Edition  
**Status**: Production Ready  
**Last Updated**: June 2025  

**Made for call center quality assurance and compliance**