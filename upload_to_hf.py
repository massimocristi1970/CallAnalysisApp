"""
Upload Database to Hugging Face Spaces
Uploads the local call_analysis.db to your Hugging Face Space

SETUP:
1. Install huggingface_hub: pip install huggingface_hub
2. Set your HF token as an environment variable:
   - Windows: set HF_TOKEN=your_token_here
   - Linux/Mac: export HF_TOKEN=your_token_here
   Or create a .env file with: HF_TOKEN=your_token_here

3. Update the REPO_ID below to match your Hugging Face Space
"""

import os
import sys
from datetime import datetime

# Configuration - UPDATE THESE VALUES
REPO_ID = "your-username/your-space-name"  # e.g., "massimocristi1970/CallAnalysisApp"
DB_FILENAME = "call_analysis.db"
REPO_TYPE = "space"  # Use "space" for Spaces, "dataset" for Datasets


def get_hf_token():
    """Get HuggingFace token from environment or .env file"""
    
    # Try environment variable first
    token = os.environ.get("HF_TOKEN")
    if token:
        return token
    
    # Try .env file
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("HF_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    
    return None


def check_for_new_calls(db_path):
    """Check if there are new calls to upload by comparing with last upload"""
    import sqlite3
    
    if not os.path.exists(db_path):
        print(f"   Database not found: {db_path}")
        return False, 0
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get total call count
    cursor.execute("SELECT COUNT(*) FROM calls")
    total_calls = cursor.fetchone()[0]
    
    # Get latest call date
    cursor.execute("SELECT MAX(created_at) FROM calls")
    latest_call = cursor.fetchone()[0]
    
    conn.close()
    
    if total_calls == 0:
        print("   No calls found in database")
        return False, 0
    
    print(f"   Total calls in database: {total_calls}")
    print(f"   Latest call timestamp: {latest_call}")
    
    return True, total_calls


def upload_to_huggingface(db_path, token):
    """Upload database to Hugging Face"""
    try:
        from huggingface_hub import HfApi, upload_file
    except ImportError:
        print("\n   Error: huggingface_hub not installed")
        print("   Run: pip install huggingface_hub")
        return False
    
    if not os.path.exists(db_path):
        print(f"   Error: Database not found: {db_path}")
        return False
    
    try:
        api = HfApi()
        
        print(f"\n   Uploading to: {REPO_ID}")
        print(f"   File: {db_path}")
        print(f"   This may take a moment...")
        
        # Upload the file
        upload_file(
            path_or_fileobj=db_path,
            path_in_repo=DB_FILENAME,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            token=token,
            commit_message=f"Database update - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        print(f"\n   Upload successful!")
        print(f"   View at: https://huggingface.co/spaces/{REPO_ID}")
        return True
        
    except Exception as e:
        print(f"\n   Upload failed: {e}")
        return False


def main():
    print("=" * 50)
    print("  Upload Database to Hugging Face")
    print("=" * 50)
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_FILENAME)
    
    # Check configuration
    if REPO_ID == "your-username/your-space-name":
        print("\n   ERROR: Please update REPO_ID in this script")
        print("   Edit upload_to_hf.py and set your Hugging Face repo ID")
        return False
    
    # Get token
    token = get_hf_token()
    if not token:
        print("\n   ERROR: HuggingFace token not found")
        print("\n   Set your token using one of these methods:")
        print("   1. Environment variable: set HF_TOKEN=your_token")
        print("   2. Create .env file with: HF_TOKEN=your_token")
        print("\n   Get your token at: https://huggingface.co/settings/tokens")
        return False
    
    print(f"\n   HF Token found: {token[:8]}...{token[-4:]}")
    
    # Check for calls
    has_calls, total_calls = check_for_new_calls(db_path)
    if not has_calls:
        print("\n   No calls to upload")
        return False
    
    # Confirm upload
    print(f"\n   Ready to upload {total_calls} calls to {REPO_ID}")
    response = input("\n   Continue? (y/n): ").strip().lower()
    
    if response != 'y':
        print("   Upload cancelled")
        return False
    
    # Upload
    return upload_to_huggingface(db_path, token)


if __name__ == "__main__":
    success = main()
    print()
    input("Press Enter to exit...")
    sys.exit(0 if success else 1)
