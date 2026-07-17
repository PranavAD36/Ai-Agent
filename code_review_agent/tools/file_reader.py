"""Python code file reader.

Implements:
  - read_python_files(repo_path: str) -> dict[str, str]
"""

from __future__ import annotations

from pathlib import Path


IGNORED_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
}


def read_python_files(repo_path: str) -> dict[str, str]:
    """Read every .py file from a repository into memory (backward-compatibility)."""
    return read_source_files(repo_path, extensions=[".py"])


def read_source_files(
    repo_path: str,
    extensions: list[str] = [".py"],
    exclude_dirs: list[str] | set[str] = IGNORED_DIRS
) -> dict[str, str]:
    """Read every source file matching the extensions, skipping excluded directories."""
    root = Path(repo_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

    files: dict[str, str] = {}
    exclude_set = set(exclude_dirs)
    
    for path in sorted(root.rglob("*")):
        if path.is_file():
            # Skip ignored directories
            if any(part in exclude_set for part in path.relative_to(root).parts):
                continue
            if path.suffix.lower() in extensions:
                relative_path = path.relative_to(root).as_posix()
                files[relative_path] = path.read_text(encoding="utf-8", errors="replace")
    return files
