"""File Manager - Safe file operations with project analysis."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil

logger = logging.getLogger(__name__)


class FileManager:
    """Manage file operations safely."""

    def __init__(self, safe_dirs: Optional[List[str]] = None):
        """Initialize File Manager.
        
        Args:
            safe_dirs: List of allowed directories
        """
        self.safe_dirs = safe_dirs or [str(Path.home() / "projects"), str(Path.cwd())]

    def _is_safe_path(self, path: str) -> bool:
        """Check if path is safe to operate on."""
        try:
            full_path = Path(path).resolve()
            for safe_dir in self.safe_dirs:
                if str(full_path).startswith(str(Path(safe_dir).resolve())):
                    return True
            logger.warning(f"Unsafe path access attempted: {path}")
            return False
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return False

    def create_file(self, path: str, content: str) -> Dict[str, Any]:
        """Create new file.
        
        Args:
            path: File path
            content: File content
            
        Returns:
            Creation status
        """
        if not self._is_safe_path(path):
            return {"success": False, "error": "Unsafe path"}

        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            logger.info(f"Created file: {path}")
            return {"success": True, "path": str(path)}
        except Exception as e:
            logger.error(f"File creation error: {e}")
            return {"success": False, "error": str(e)}

    def read_file(self, path: str) -> Optional[str]:
        """Read file content.
        
        Args:
            path: File path
            
        Returns:
            File content
        """
        if not self._is_safe_path(path):
            return None

        try:
            file_path = Path(path)
            if file_path.exists():
                return file_path.read_text()
            return None
        except Exception as e:
            logger.error(f"File read error: {e}")
            return None

    def edit_file(self, path: str, changes: Dict[str, str]) -> Dict[str, Any]:
        """Edit file with replacements.
        
        Args:
            path: File path
            changes: Text replacements
            
        Returns:
            Edit status
        """
        if not self._is_safe_path(path):
            return {"success": False, "error": "Unsafe path"}

        try:
            file_path = Path(path)
            content = file_path.read_text()

            for old_text, new_text in changes.items():
                content = content.replace(old_text, new_text)

            file_path.write_text(content)
            logger.info(f"Edited file: {path}")
            return {"success": True, "path": str(path)}
        except Exception as e:
            logger.error(f"File edit error: {e}")
            return {"success": False, "error": str(e)}

    def delete_file(self, path: str, confirm: bool = True) -> Dict[str, Any]:
        """Delete file safely.
        
        Args:
            path: File path
            confirm: Require confirmation
            
        Returns:
            Deletion status
        """
        if not self._is_safe_path(path):
            return {"success": False, "error": "Unsafe path"}

        try:
            file_path = Path(path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {path}")
                return {"success": True}
            return {"success": False, "error": "File not found"}
        except Exception as e:
            logger.error(f"File deletion error: {e}")
            return {"success": False, "error": str(e)}

    def list_files(self, path: str, recursive: bool = False) -> List[Dict[str, Any]]:
        """List files in directory.
        
        Args:
            path: Directory path
            recursive: Include subdirectories
            
        Returns:
            List of files
        """
        if not self._is_safe_path(path):
            return []

        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return []

            files = []
            pattern = "**/*" if recursive else "*"

            for file_path in dir_path.glob(pattern):
                if file_path.is_file() and not file_path.name.startswith("."):
                    files.append({
                        "path": str(file_path.relative_to(dir_path)),
                        "size": file_path.stat().st_size,
                        "type": file_path.suffix,
                        "modified": file_path.stat().st_mtime
                    })

            return sorted(files, key=lambda x: x["path"])
        except Exception as e:
            logger.error(f"File listing error: {e}")
            return []
