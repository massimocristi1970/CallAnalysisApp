"""
Automated Database Upload to HuggingFace Spaces
Safe to commit - uses .env file for token
"""

from huggingface_hub import HfApi
import os
from datetime import datetime

# ========== LOAD TOKEN FROM .ENV FILE ==========
# Try to load from .env file first
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")

HF_TOKEN = None

# Read token from .env file
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('HF_TOKEN='):
                HF_TOKEN = line.split('=', 1)[1].strip().strip('"').strip("'")
                break

# Fall back to environment variable if not in .env
if not HF_TOKEN:
    HF_TOKEN = os.environ.get('HF_TOKEN')

if not HF_TOKEN:
    print("=" * 60)
    print("ERROR: HF_TOKEN not found!")
    print("=" * 60)
    print("\nAdd this line to your .env file:")
    print("HF_TOKEN=hf_your_token_here")
    print(f"\n.env file location: {env_path}")
    input("\nPress Enter to exit...")
    exit(1)

# Show token is loaded (masked)
print(f"Token loaded: {HF_TOKEN[:10]}...{HF_TOKEN[-4:]}")

# ========== CONFIGURATION ==========
USERNAME = "massimocristi1970"
DB_PATH = os.path.join(script_dir, "call_analysis.db")

SPACES = [
    "call-analysis-app",
    "call-analysis-dashboard"
]

# ====================================

def upload_database():
    """Upload database to all HuggingFace Spaces"""

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return False

    file_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"Database size: {file_size_mb:.2f} MB")
    print(f"Source: {DB_PATH}")
    print(f"Upload time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    api = HfApi()

    success_count = 0
    for space_name in SPACES:
        repo_id = f"{USERNAME}/{space_name}"  # FIXED: now uses actual space_name
        try:
            print(f"\nUploading to {repo_id}...")

            api.upload_file(
                path_or_fileobj=DB_PATH,
                path_in_repo="call_analysis.db",
                repo_id=repo_id,  # FIXED: uses variable, not hardcoded
                repo_type="space",
                token=HF_TOKEN,
                commit_message=f"Update database - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            print(f"SUCCESS: {space_name} updated!")
            success_count += 1

        except Exception as e:
            print(f"ERROR uploading to {space_name}: {e}")

    print("\n" + "=" * 60)
    print(f"Upload complete! {success_count}/{len(SPACES)} spaces updated")
    if success_count > 0:
        print("Spaces will restart automatically (30-60 seconds)")

    return success_count == len(SPACES)


if __name__ == "__main__":
    print("=" * 60)
    print("  HuggingFace Database Upload Tool")
    print("=" * 60)

    upload_database()
    input("\nPress Enter to exit...")
