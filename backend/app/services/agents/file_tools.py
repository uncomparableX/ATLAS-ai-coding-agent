"""
File System Tools for Agent Use
Safe file reading, writing, diff generation, and AST-aware patching.
All paths are validated against the repository root to prevent traversal.
"""
import difflib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import structlog

logger = structlog.get_logger(__name__)

# File size limit: skip files larger than this
MAX_FILE_SIZE = 1_000_000  # 1 MB


class FileTools:
    """
    Provides async-safe file operations bound to a repository root.
    All path arguments are relative to repo_path.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    # ── Path safety ───────────────────────────────────────────────────────────

    def safe_path(self, file_path: str) -> Path:
        """
        Resolve a relative file path within the repository root.
        Raises ValueError if the resolved path escapes the root.
        """
        resolved = (self.repo_path / file_path).resolve()
        if not str(resolved).startswith(str(self.repo_path)):
            raise ValueError(
                f"Path traversal blocked: '{file_path}' resolves outside repo root."
            )
        return resolved

    # ── Read ─────────────────────────────────────────────────────────────────

    async def read_file(self, file_path: str) -> Optional[str]:
        """
        Read and return the contents of a file.
        Returns None if the file does not exist, is too large, or is binary.
        """
        try:
            path = self.safe_path(file_path)
        except ValueError as e:
            logger.warning("read_file path rejected", path=file_path, error=str(e))
            return None

        if not path.exists() or not path.is_file():
            return None

        try:
            size = path.stat().st_size
            if size > MAX_FILE_SIZE:
                logger.warning("File too large to read", path=file_path, size=size)
                return None
            if size == 0:
                return ""
        except OSError:
            return None

        try:
            async with aiofiles.open(path, "r", encoding="utf-8", errors="replace") as fh:
                return await fh.read()
        except Exception as e:
            logger.error("read_file failed", path=file_path, error=str(e))
            return None

    async def read_multiple(self, file_paths: List[str]) -> Dict[str, str]:
        """Read multiple files and return a dict of path → content."""
        results: Dict[str, str] = {}
        for fp in file_paths:
            content = await self.read_file(fp)
            if content is not None:
                results[fp] = content
        return results

    # ── Write ─────────────────────────────────────────────────────────────────

    async def write_file(self, file_path: str, content: str) -> bool:
        """
        Write content to a file, creating parent directories as needed.
        Returns True on success.
        """
        try:
            path = self.safe_path(file_path)
        except ValueError as e:
            logger.warning("write_file path rejected", path=file_path, error=str(e))
            return False

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(path, "w", encoding="utf-8") as fh:
                await fh.write(content)
            logger.info("File written", path=file_path, chars=len(content))
            return True
        except Exception as e:
            logger.error("write_file failed", path=file_path, error=str(e))
            return False

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file. Returns True if deleted, False if not found or error."""
        try:
            path = self.safe_path(file_path)
        except ValueError:
            return False

        if not path.exists():
            return False

        try:
            path.unlink()
            logger.info("File deleted", path=file_path)
            return True
        except Exception as e:
            logger.error("delete_file failed", path=file_path, error=str(e))
            return False

    # ── Diff ─────────────────────────────────────────────────────────────────

    def generate_diff(
        self,
        original: str,
        modified: str,
        file_path: str,
    ) -> str:
        """Generate a unified diff string between original and modified content."""
        original_lines = original.splitlines(keepends=True) if original else []
        modified_lines = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
        )
        return "".join(diff)

    def count_diff_lines(self, diff: str) -> Dict[str, int]:
        """Count added and removed lines in a unified diff string."""
        added   = 0
        removed = 0
        for line in diff.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                removed += 1
        return {"lines_added": added, "lines_removed": removed}

    # ── Apply change ──────────────────────────────────────────────────────────

    async def apply_change(
        self,
        file_path: str,
        content: str,
        action: str = "modify",
        original_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Apply a code change and return a CodeChange-compatible dict.

        Args:
            file_path:        Relative path within repository.
            content:          New file content (ignored for delete).
            action:           "modify" | "create" | "delete".
            original_content: Pre-read original content (avoids double read).

        Returns:
            Dict matching the CodeChange TypedDict schema.
        """
        if action == "delete":
            success = await self.delete_file(file_path)
            return {
                "file_path":     file_path,
                "action":        "delete",
                "original":      original_content or "",
                "modified":      "",
                "diff":          f"--- a/{file_path}\n+++ /dev/null\n",
                "explanation":   "File deleted",
                "lines_added":   0,
                "lines_removed": (original_content or "").count("\n"),
                "success":       success,
            }

        # Read original if not provided
        if original_content is None:
            original_content = await self.read_file(file_path) or ""

        success = await self.write_file(file_path, content)
        diff    = self.generate_diff(original_content, content, file_path)
        counts  = self.count_diff_lines(diff)

        return {
            "file_path":     file_path,
            "action":        action,
            "original":      original_content,
            "modified":      content,
            "diff":          diff,
            "explanation":   "",
            **counts,
            "success":       success,
        }

    # ── Directory listing ─────────────────────────────────────────────────────

    async def list_directory(self, dir_path: str = "") -> Dict[str, Any]:
        """List the contents of a directory relative to repo root."""
        try:
            base = self.safe_path(dir_path) if dir_path else self.repo_path
        except ValueError:
            return {"path": dir_path, "items": []}

        SKIP = {
            "node_modules", ".git", "__pycache__",
            "venv", ".venv", "dist", "build", ".next",
        }

        items = []
        try:
            for item in sorted(base.iterdir()):
                if item.name.startswith(".") or item.name in SKIP:
                    continue
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                })
        except PermissionError:
            pass

        return {
            "path":  dir_path or ".",
            "items": items,
        }

    async def get_file_tree(self, max_depth: int = 5) -> Dict[str, Any]:
        """Build a nested file tree for the repository."""
        SKIP = {
            "node_modules", ".git", "__pycache__",
            "venv", ".venv", "dist", "build", ".next",
            "coverage", "target", "vendor",
        }

        def _walk(path: Path, depth: int) -> Dict[str, Any]:
            node: Dict[str, Any] = {
                "name":     path.name,
                "path":     str(path.relative_to(self.repo_path)),
                "type":     "directory",
                "children": [],
            }
            if depth == 0:
                return node
            try:
                for child in sorted(path.iterdir()):
                    if child.name.startswith(".") or child.name in SKIP:
                        continue
                    if child.is_dir():
                        node["children"].append(_walk(child, depth - 1))
                    else:
                        node["children"].append({
                            "name": child.name,
                            "path": str(child.relative_to(self.repo_path)),
                            "type": "file",
                            "size": child.stat().st_size,
                        })
            except PermissionError:
                pass
            return node

        return _walk(self.repo_path, max_depth)

    # ── Search ────────────────────────────────────────────────────────────────

    async def search_in_files(
        self,
        pattern: str,
        file_extensions: Optional[List[str]] = None,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Simple text search across repository files.
        Returns a list of {file_path, line_number, line} dicts.
        """
        import re
        results: List[Dict[str, Any]] = []
        compiled = re.compile(pattern, re.IGNORECASE)
        SKIP_DIRS = {
            "node_modules", ".git", "__pycache__",
            "venv", ".venv", "dist", "build",
        }

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                if file_extensions:
                    if not any(fname.endswith(ext) for ext in file_extensions):
                        continue
                full = Path(root) / fname
                rel  = str(full.relative_to(self.repo_path))
                try:
                    content = await self.read_file(rel)
                    if content is None:
                        continue
                    for i, line in enumerate(content.split("\n"), start=1):
                        if compiled.search(line):
                            results.append({
                                "file_path":   rel,
                                "line_number": i,
                                "line":        line.strip(),
                            })
                            if len(results) >= max_results:
                                return results
                except Exception:
                    continue
        return results
