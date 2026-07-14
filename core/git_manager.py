"""Git Manager - Initialize repos, commit, push, and branch management."""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class GitManager:
    """Manage Git repositories."""

    def __init__(self):
        """Initialize Git Manager."""
        self.git_available = self._check_git()

    def _check_git(self) -> bool:
        """Check if Git is installed."""
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def _run_git(self, args: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run git command."""
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            logger.error(f"Git error: {e}")
            return {"success": False, "error": str(e)}

    def init_repo(self, repo_path: str) -> Dict[str, Any]:
        """Initialize new Git repository.
        
        Args:
            repo_path: Repository path
            
        Returns:
            Initialization status
        """
        if not self.git_available:
            return {"success": False, "error": "Git not installed"}

        try:
            path = Path(repo_path)
            path.mkdir(parents=True, exist_ok=True)
            return self._run_git(["init"], cwd=str(path))
        except Exception as e:
            logger.error(f"Repo init error: {e}")
            return {"success": False, "error": str(e)}

    def clone_repo(self, repo_url: str, target_path: str) -> Dict[str, Any]:
        """Clone repository.
        
        Args:
            repo_url: Repository URL
            target_path: Target directory
            
        Returns:
            Clone status
        """
        if not self.git_available:
            return {"success": False, "error": "Git not installed"}

        return self._run_git(["clone", repo_url, target_path])

    def commit(self, repo_path: str, message: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Commit changes.
        
        Args:
            repo_path: Repository path
            message: Commit message
            files: Files to stage (None = all)
            
        Returns:
            Commit status
        """
        if not self.git_available:
            return {"success": False, "error": "Git not installed"}

        try:
            # Add files
            if files:
                for file in files:
                    self._run_git(["add", file], cwd=repo_path)
            else:
                self._run_git(["add", "."], cwd=repo_path)

            # Commit
            return self._run_git(["commit", "-m", message], cwd=repo_path)
        except Exception as e:
            logger.error(f"Commit error: {e}")
            return {"success": False, "error": str(e)}

    def push(self, repo_path: str, branch: str = "main") -> Dict[str, Any]:
        """Push changes.
        
        Args:
            repo_path: Repository path
            branch: Branch to push
            
        Returns:
            Push status
        """
        if not self.git_available:
            return {"success": False, "error": "Git not installed"}

        return self._run_git(["push", "origin", branch], cwd=repo_path)

    def create_branch(self, repo_path: str, branch_name: str) -> Dict[str, Any]:
        """Create new branch.
        
        Args:
            repo_path: Repository path
            branch_name: New branch name
            
        Returns:
            Branch creation status
        """
        if not self.git_available:
            return {"success": False, "error": "Git not installed"}

        return self._run_git(["checkout", "-b", branch_name], cwd=repo_path)

    def merge_branch(self, repo_path: str, branch_name: str) -> Dict[str, Any]:
        """Merge branch.
        
        Args:
            repo_path: Repository path
            branch_name: Branch to merge
            
        Returns:
            Merge status
        """
        if not self.git_available:
            return {"success": False, "error": "Git not installed"}

        return self._run_git(["merge", branch_name], cwd=repo_path)
