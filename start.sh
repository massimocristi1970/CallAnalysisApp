#!/bin/bash

# Startup script for Call Analysis App on Hugging Face Spaces
# Runs both Streamlit applications simultaneously

set -e

# Color codes for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Ensure required directories exist
log_info "Creating required directories..."
mkdir -p audio_samples
mkdir -p fonts
mkdir -p dejavu-sans-ttf-2.37

# Check if database exists
if [ ! -f "call_analysis.db" ]; then
    log_warning "Database file not found. Will be created on first use."
fi

# Check Python version
log_info "Python version: $(python --version)"

# Verify required packages
log_info "Verifying Streamlit installation..."
python -c "import streamlit" 2>/dev/null || {
    log_error "Streamlit not installed!"
    exit 1
}

# Download spaCy model if not already present
log_info "Checking spaCy model..."
python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null || {
    log_warning "Downloading spaCy model en_core_web_sm..."
    python -m spacy download en_core_web_sm
}

# Start the main app on port 8501 in the background
log_info "Starting main Call Analysis app on port 8501..."
streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.serverAddress=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=true \
    > /tmp/app_8501.log 2>&1 &

APP_PID=$!
log_info "Main app started with PID: $APP_PID"

# Wait a bit for the first app to initialize
sleep 5

# Check if main app is still running
if ! kill -0 $APP_PID 2>/dev/null; then
    log_error "Main app failed to start! Check logs:"
    tail -n 50 /tmp/app_8501.log
    exit 1
fi

# Start the dashboard on port 8503 in the foreground
log_info "Starting dashboard app on port 8503..."
streamlit run dashboard.py \
    --server.port=8503 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.serverAddress=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=true \
    > /tmp/dashboard_8503.log 2>&1 &

DASHBOARD_PID=$!
log_info "Dashboard started with PID: $DASHBOARD_PID"

# Function to handle shutdown
shutdown() {
    log_info "Shutting down applications..."
    kill $APP_PID 2>/dev/null || true
    kill $DASHBOARD_PID 2>/dev/null || true
    exit 0
}

# Trap termination signals
trap shutdown SIGTERM SIGINT

# Monitor both processes
log_info "Both applications are running:"
log_info "  - Main App: http://0.0.0.0:8501 (PID: $APP_PID)"
log_info "  - Dashboard: http://0.0.0.0:8503 (PID: $DASHBOARD_PID)"
log_info ""
log_info "Monitoring application health..."

# Keep the script running and monitor processes
while true; do
    # Check if main app is still running
    if ! kill -0 $APP_PID 2>/dev/null; then
        log_error "Main app (PID: $APP_PID) has stopped!"
        log_error "Last 50 lines of log:"
        tail -n 50 /tmp/app_8501.log
        kill $DASHBOARD_PID 2>/dev/null || true
        exit 1
    fi
    
    # Check if dashboard is still running
    if ! kill -0 $DASHBOARD_PID 2>/dev/null; then
        log_error "Dashboard (PID: $DASHBOARD_PID) has stopped!"
        log_error "Last 50 lines of log:"
        tail -n 50 /tmp/dashboard_8503.log
        kill $APP_PID 2>/dev/null || true
        exit 1
    fi
    
    # Wait before next check
    sleep 30
done
