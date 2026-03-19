"""
Automated Database Upload to Hugging Face Spaces.
Safe to commit - uses .env file or environment variables for the token.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

from huggingface_hub import HfApi

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ".env"
DB_PATH = SCRIPT_DIR / "call_analysis.db"
USERNAME = "massimocristi1970"
SPACES = [
    "call-analysis-app",
    "call-analysis-dashboard",
]


def load_hf_token() -> str | None:
    token = None

    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("HF_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

    if not token:
        token = os.environ.get("HF_TOKEN")

    return token


def mask_token(token: str) -> str:
    if len(token) <= 14:
        return "[masked]"
    return f"{token[:10]}...{token[-4:]}"


def upload_database(spaces: Iterable[str] | None = None, quiet: bool = False) -> bool:
    """Upload the local SQLite database to the configured Hugging Face Spaces."""
    token = load_hf_token()
    if not token:
        if not quiet:
            print("=" * 60)
            print("ERROR: HF_TOKEN not found!")
            print("=" * 60)
            print("\nAdd this line to your .env file:")
            print("HF_TOKEN=hf_your_token_here")
            print(f"\n.env file location: {ENV_PATH}")
        return False

    if not DB_PATH.exists():
        if not quiet:
            print(f"ERROR: Database not found at {DB_PATH}")
        return False

    selected_spaces = list(spaces or SPACES)
    file_size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not quiet:
        print("=" * 60)
        print("  Hugging Face Database Upload Tool")
        print("=" * 60)
        print(f"Token loaded: {mask_token(token)}")
        print(f"Database size: {file_size_mb:.2f} MB")
        print(f"Source: {DB_PATH}")
        print(f"Upload time: {timestamp}")
        print("=" * 60)

    api = HfApi()
    success_count = 0

    for space_name in selected_spaces:
        repo_id = f"{USERNAME}/{space_name}"
        try:
            if not quiet:
                print(f"\nUploading to {repo_id}...")

            api.upload_file(
                path_or_fileobj=str(DB_PATH),
                path_in_repo="call_analysis.db",
                repo_id=repo_id,
                repo_type="space",
                token=token,
                commit_message=f"Update database - {timestamp}",
            )

            success_count += 1
            if not quiet:
                print(f"SUCCESS: {space_name} updated!")
        except Exception as exc:
            if not quiet:
                print(f"ERROR uploading to {space_name}: {exc}")
            else:
                print(f"[upload_to_hf] ERROR uploading to {space_name}: {exc}", file=sys.stderr)

    if not quiet:
        print("\n" + "=" * 60)
        print(f"Upload complete! {success_count}/{len(selected_spaces)} spaces updated")
        if success_count > 0:
            print("Spaces will restart automatically (30-60 seconds)")

    return success_count == len(selected_spaces)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload call_analysis.db to Hugging Face Spaces.")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output and avoid interactive prompts; useful for git hooks.",
    )
    parser.add_argument(
        "--space",
        dest="spaces",
        action="append",
        help="Upload only to the named Hugging Face Space. Can be passed multiple times.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    success = upload_database(spaces=args.spaces, quiet=args.quiet)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
