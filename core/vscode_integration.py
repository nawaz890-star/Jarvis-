"""VS Code Integration - Open projects, create/edit files, run commands."""

import logging
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class VSCodeIntegration:
    """Integrate with VS Code editor."""

    def __init__(self):
        """Initialize VS Code Integration."""
        self.vscode_available = self._check_vscode()

    def _check_vscode(self) -> bool:
        """Check if VS Code is installed."""
        try:
            result = subprocess.run(["code", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def open_project(self, project_path: str) -> Dict[str, Any]:
        """Open project in VS Code.
        
        Args:
            project_path: Path to project
            
        Returns:
            Operation status
        """
        if not self.vscode_available:
            return {"success": False, "error": "VS Code not installed"}

        try:
            path = Path(project_path).resolve()
            if not path.exists():
                return {"success": False, "error": "Project not found"}

            subprocess.Popen(["code", str(path)])
            logger.info(f"Opened project in VS Code: {project_path}")
            return {"success": True, "project": str(path)}
        except Exception as e:
            logger.error(f"Error opening project: {e}")
            return {"success": False, "error": str(e)}

    def run_python(self, file_path: str) -> Dict[str, Any]:
        """Run Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Execution result
        """
        try:
            path = Path(file_path).resolve()
            if not path.exists():
                return {"success": False, "error": "File not found"}

            result = subprocess.run(
                ["python", str(path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Execution timeout"}
        except Exception as e:
            logger.error(f"Python execution error: {e}")
            return {"success": False, "error": str(e)}

    def run_terminal_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run terminal command safely.
        
        Args:
            command: Command to run
            cwd: Working directory
            
        Returns:
            Command result
        """
        # Blacklist dangerous commands
        dangerous = ["rm -rf", "sudo", "reboot", "shutdown", "format", "dd", "mkfs"]
        for danger in dangerous:
            if danger in command.lower():
                logger.warning(f"Blocked dangerous command: {command}")
                return {"success": False, "error": "Command not allowed"}

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cwd
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout"}
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {"success": False, "error": str(e)}
