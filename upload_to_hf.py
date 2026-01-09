"""
Automated Database Upload to HuggingFace Spaces
Uploads call_analysis.db to both HF Spaces after local merge
"""

from huggingface_hub import HfApi
import os
from datetime import datetime

# ========== CONFIGURATION ==========
HF_TOKEN = "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"
USERNAME = "massimocristi1970"

# Database path
DB_PATH = r"C:\Dev\GitHub\CallAnalysisApp\call_analysis.db"

# Your HuggingFace Space names
SPACES = [
    "call-analysis-app",
    "call-analysis-dashboard"
]


# ====================================

def upload_database():
    """Upload database to all HuggingFace Spaces"""

    # Validate database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ ERROR: Database not found at {DB_PATH}")
        return False

    # Get file size
    file_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"📊 Database size: {file_size_mb:.2f} MB")
    print(f"📁 Source: {DB_PATH}")
    print(f"⏰ Upload time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Initialize HF API
    api = HfApi()

    # Upload to each Space
    success_count = 0
    for space_name in SPACES:
        try:
            print(f"\n📤 Uploading to {USERNAME}/{space_name}...")

            api.upload_file(
                path_or_fileobj=DB_PATH,
                path_in_repo="call_analysis.db",
                repo_id=f"{USERNAME}/{space_name}",
                repo_type="space",
                token=HF_TOKEN,
                commit_message=f"Update database - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            print(f"✅ {space_name} updated successfully!")
            success_count += 1

        except Exception as e:
            print(f"❌ ERROR uploading to {space_name}:  {e}")

    print("\n" + "=" * 60)
    print(f"🎉 Upload complete! {success_count}/{len(SPACES)} spaces updated")
    print("⏳ Spaces will restart automatically (30-60 seconds)")
    print("🔄 Refresh your dashboard to see new data")

    return success_count == len(SPACES)


if __name__ == "__main__":
    print("=" * 60)
    print("  HuggingFace Database Upload Tool")
    print("=" * 60)

    if HF_TOKEN == "YOUR_TOKEN_HERE":
        print("\n❌ ERROR: Please set your HuggingFace token first!")
        print("   1. Go to: https://huggingface.co/settings/tokens")
        print("   2. Create new token (Write access)")
        print("   3. Edit upload_to_hf.py and paste token")
        input("\nPress Enter to exit...")
        exit(1)

    upload_database()
    input("\nPress Enter to exit...")