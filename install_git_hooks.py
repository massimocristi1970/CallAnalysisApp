from pathlib import Path
import subprocess
import sys

repo_root = Path(__file__).resolve().parent
hooks_path = repo_root / '.githooks'

subprocess.run(['git', 'config', 'core.hooksPath', str(hooks_path)], check=True, cwd=repo_root)
print(f'Configured git hooks path: {hooks_path}')
print('The post-push hook will now upload call_analysis.db to Hugging Face after pushes to origin/main.')
