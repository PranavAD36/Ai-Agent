"""Code chunking by Python function and class.

Implements:
  - chunk_python_file(file_path: str, content: str) -> list[CodeChunk]
  - chunk_python_files(files: dict[str, str]) -> list[CodeChunk]
"""

from __future__ import annotations

import ast
import re
from typing import TypedDict


class CodeChunk(TypedDict):
    """A review-sized slice of a source file."""

    file_path: str
    name: str
    kind: str
    start_line: int
    end_line: int
    content: str


def chunk_python_files(files: dict[str, str]) -> list[CodeChunk]:
    """Chunk all Python files (backward-compatibility)."""
    return chunk_source_files(files, language="python")


def chunk_source_files(files: dict[str, str], language: str = "python") -> list[CodeChunk]:
    """Chunk all source files of the specified language."""
    chunks: list[CodeChunk] = []
    for file_path, content in files.items():
        if language.lower() == "javascript":
            chunks.extend(chunk_javascript_file(file_path, content))
        else:
            chunks.extend(chunk_python_file(file_path, content))
    return chunks


def chunk_python_file(file_path: str, content: str) -> list[CodeChunk]:
    """Chunk one Python file by module preamble, functions, and classes."""

    lines = content.splitlines()
    if not lines:
        return [_build_chunk(file_path, "<module>", "module", 1, 1, lines)]

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return [_build_chunk(file_path, "<module>", "module", 1, len(lines), lines)]

    definitions = [
        node
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if not definitions:
        return [_build_chunk(file_path, "<module>", "module", 1, len(lines), lines)]

    definitions.sort(key=lambda node: node.lineno)
    chunks = _module_preamble_chunks(file_path, lines, definitions)

    for node in definitions:
        kind = "class" if isinstance(node, ast.ClassDef) else "function"
        end_line = getattr(node, "end_lineno", node.lineno)
        chunks.append(_build_chunk(file_path, node.name, kind, node.lineno, end_line, lines))

    return chunks


def _module_preamble_chunks(
    file_path: str, lines: list[str], definitions: list[ast.AST]
) -> list[CodeChunk]:
    first_definition_line = definitions[0].lineno
    if first_definition_line <= 1:
        return []

    preamble = lines[: first_definition_line - 1]
    if not any(line.strip() for line in preamble):
        return []

    return [_build_chunk(file_path, "<module>", "module", 1, first_definition_line - 1, lines)]


def _build_chunk(
    file_path: str,
    name: str,
    kind: str,
    start_line: int,
    end_line: int,
    lines: list[str],
) -> CodeChunk:
    return {
        "file_path": file_path,
        "name": name,
        "kind": kind,
        "start_line": start_line,
        "end_line": end_line,
        "content": "\n".join(lines[start_line - 1 : end_line]),
    }


def chunk_javascript_file(file_path: str, content: str) -> list[CodeChunk]:
    """Chunk one JavaScript/TypeScript file by module preamble, functions, and classes using regex and brace matching."""
    lines = content.splitlines()
    if not lines:
        return [_build_chunk(file_path, "<module>", "module", 1, 1, lines)]

    # Regexes to detect function or class starts
    patterns = [
        r"\bfunction\s+(\w+)\s*\(",
        r"\bclass\s+(\w+)\b",
        r"\b(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=]+)\s*=>",
        r"\b(?:const|let|var)\s+(\w+)\s*=\s*function\b"
    ]
    
    combined_pattern = "|".join(f"(?:{p})" for p in patterns)
    regex = re.compile(combined_pattern)
    
    definitions = []
    
    for line_idx, line in enumerate(lines):
        # Skip comments
        trimmed = line.strip()
        if trimmed.startswith("//") or trimmed.startswith("/*") or trimmed.startswith("*"):
            continue
            
        match = regex.search(line)
        if match:
            name = "unknown"
            kind = "function"
            
            for idx, pattern in enumerate(patterns):
                m = re.search(pattern, line)
                if m:
                    name = m.group(1)
                    if idx == 1:
                        kind = "class"
                    break
            
            # Brace matching
            brace_count = 0
            found_first_brace = False
            end_line = line_idx + 1
            
            for check_idx in range(line_idx, len(lines)):
                check_line = lines[check_idx]
                
                for char in check_line:
                    if char == "{":
                        brace_count += 1
                        found_first_brace = True
                    elif char == "}":
                        brace_count -= 1
                        
                if found_first_brace and brace_count <= 0:
                    end_line = check_idx + 1
                    break
            else:
                end_line = len(lines)
                
            definitions.append({
                "name": name,
                "kind": kind,
                "start_line": line_idx + 1,
                "end_line": end_line
            })

    if not definitions:
        return [_build_chunk(file_path, "<module>", "module", 1, len(lines), lines)]

    definitions.sort(key=lambda d: d["start_line"])
    
    chunks = []
    first_start = definitions[0]["start_line"]
    if first_start > 1:
        preamble_lines = lines[:first_start - 1]
        if any(l.strip() for l in preamble_lines):
            chunks.append(_build_chunk(file_path, "<module>", "module", 1, first_start - 1, lines))
            
    for d in definitions:
        chunks.append(_build_chunk(file_path, d["name"], d["kind"], d["start_line"], d["end_line"], lines))
        
    return chunks
