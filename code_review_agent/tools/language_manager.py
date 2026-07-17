"""Language manager for automatic project type detection and configuration.

Supports:
  - Language detection from workspace files.
  - Pluggable configurations for different languages (Python, JavaScript).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Configurations for supported languages
LANGUAGES = {
    "python": {
        "name": "Python",
        "extensions": [".py"],
        "exclude_dirs": ["venv", ".venv", "__pycache__", "build", "dist", ".git", ".github", "egg-info"],
        "linters": ["pylint", "bandit"],
        "test_command": "PYTHONPATH=.:src pytest --cov=. --cov-report=json:coverage.json",
        "coverage_file": "coverage.json"
    },
    "javascript": {
        "name": "JavaScript",
        "extensions": [".js", ".jsx", ".ts", ".tsx"],
        "exclude_dirs": ["node_modules", "dist", "build", "coverage", ".git", ".github", "out"],
        "linters": ["eslint"],
        "test_command": "npm install && npm test -- --coverage --coverageReporters=json --watchAll=false",
        "coverage_file": "coverage/coverage-final.json"
    }
}

def detect_language(repo_path: str) -> str:
    """Scan the repository files and manifests to detect the primary language."""
    root = Path(repo_path).expanduser().resolve()
    if not root.exists():
        return "python"

    # 1. Check manifests first
    if (root / "package.json").exists():
        return "javascript"
    if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        return "python"

    # 2. Count extensions
    py_count = 0
    js_count = 0

    for path in root.rglob("*"):
        if path.is_file():
            # Skip common folders to avoid false counts inside excluded subdirectories
            parts = path.parts
            if any(exclude in parts for exclude in ["node_modules", "venv", ".venv", "dist", "build", ".git"]):
                continue
                
            ext = path.suffix.lower()
            if ext in LANGUAGES["python"]["extensions"]:
                py_count += 1
            elif ext in LANGUAGES["javascript"]["extensions"]:
                js_count += 1

    print(f"[*] Language detection count -> Python: {py_count} files, JavaScript: {js_count} files")
    
    if js_count > py_count:
        return "javascript"
    
    return "python"

def get_language_config(lang: str) -> dict[str, Any]:
    """Retrieve language configuration dictionary, falling back to Python."""
    return LANGUAGES.get(lang.lower(), LANGUAGES["python"])
