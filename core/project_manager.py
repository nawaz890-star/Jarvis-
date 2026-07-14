"""Project management and file system utilities for coding tasks."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ProjectManager:
    """Manage projects and file structures."""

    def __init__(self):
        """Initialize project manager."""
        self.current_project: Optional[Path] = None

    def create_project(self, project_name: str, project_type: str = "generic", parent_dir: str = ".") -> Dict[str, Any]:
        """Create a new project with initial structure.
        
        Args:
            project_name: Name of the project
            project_type: Type of project (generic, python, nodejs, react, django, flask)
            parent_dir: Parent directory for project
            
        Returns:
            Project creation status
        """
        try:
            project_path = Path(parent_dir) / project_name
            
            if project_path.exists():
                return {"error": f"Project already exists at {project_path}"}
            
            project_path.mkdir(parents=True, exist_ok=True)
            self.current_project = project_path
            
            # Create base structure
            (project_path / "src").mkdir()
            (project_path / "tests").mkdir()
            (project_path / "docs").mkdir()
            (project_path / "data").mkdir()
            (project_path / ".gitignore").write_text(self._get_gitignore(project_type))
            (project_path / "README.md").write_text(f"# {project_name}\n\nTODO: Add project description\n")
            
            # Create type-specific files
            if project_type == "python":
                (project_path / "requirements.txt").write_text("# Add dependencies here\n")
                (project_path / "setup.py").write_text(self._get_setup_py(project_name))
                (project_path / "pyproject.toml").write_text(self._get_pyproject_toml(project_name))
            
            elif project_type == "nodejs":
                (project_path / "package.json").write_text(self._get_package_json(project_name))
                (project_path / ".npmrc").write_text("")
            
            elif project_type == "react":
                (project_path / "package.json").write_text(self._get_react_package_json(project_name))
                (project_path / "tsconfig.json").write_text(self._get_tsconfig())
                (project_path / "public").mkdir()
                (project_path / "public" / "index.html").write_text(self._get_react_html())
            
            logger.info(f"Created {project_type} project at {project_path}")
            return {
                "success": True,
                "project_path": str(project_path),
                "project_type": project_type,
                "next_steps": self._get_next_steps(project_type)
            }
        
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return {"error": str(e)}

    def list_project_files(self, project_path: Optional[str] = None, max_depth: int = 3) -> List[Dict[str, Any]]:
        """List all files in a project.
        
        Args:
            project_path: Project path (uses current if not specified)
            max_depth: Maximum directory depth to traverse
            
        Returns:
            List of files with metadata
        """
        path = Path(project_path or self.current_project or ".")
        files = []
        
        for file_path in path.rglob("*"):
            depth = len(file_path.relative_to(path).parts)
            if depth > max_depth:
                continue
            
            if file_path.is_file() and not file_path.name.startswith("."):
                files.append({
                    "path": str(file_path.relative_to(path)),
                    "size": file_path.stat().st_size,
                    "type": file_path.suffix,
                    "is_binary": self._is_binary(file_path)
                })
        
        return sorted(files, key=lambda x: x["path"])

    def add_file(self, filename: str, content: str, directory: str = "src") -> Dict[str, Any]:
        """Add a file to the project.
        
        Args:
            filename: Name of file to add
            content: File content
            directory: Directory within project (default: src)
            
        Returns:
            File creation status
        """
        try:
            if not self.current_project:
                return {"error": "No project loaded"}
            
            file_path = self.current_project / directory / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            
            logger.info(f"Added file: {file_path}")
            return {
                "success": True,
                "path": str(file_path.relative_to(self.current_project)),
                "size": len(content)
            }
        
        except Exception as e:
            logger.error(f"Failed to add file: {e}")
            return {"error": str(e)}

    def delete_file(self, filepath: str) -> Dict[str, Any]:
        """Delete a file from the project.
        
        Args:
            filepath: Relative path to file
            
        Returns:
            Deletion status
        """
        try:
            if not self.current_project:
                return {"error": "No project loaded"}
            
            file_path = self.current_project / filepath
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {filepath}")
                return {"success": True}
            else:
                return {"error": f"File not found: {filepath}"}
        
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return {"error": str(e)}

    def _get_gitignore(self, project_type: str) -> str:
        """Get appropriate .gitignore content.
        
        Args:
            project_type: Type of project
            
        Returns:
            .gitignore content
        """
        base = "*.pyc\n.DS_Store\n.env\n.venv\nvenv/\nnode_modules/\n.idea/\n.vscode/\n*.log\n"
        
        if project_type == "python":
            return base + "dist/\nbuild/\n*.egg-info/\n.pytest_cache/\n.coverage\n"
        elif project_type == "nodejs" or project_type == "react":
            return base + "dist/\nbuild/\n.next/\nout/\n.env.local\n"
        return base

    def _get_setup_py(self, project_name: str) -> str:
        """Get setup.py template."""
        return f"""from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Short description",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # Add dependencies here
    ],
)
"""

    def _get_pyproject_toml(self, project_name: str) -> str:
        """Get pyproject.toml template."""
        return f"""[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "Short description"
requires-python = ">=3.8"

[tool.black]
line-length = 100
"""

    def _get_package_json(self, project_name: str) -> str:
        """Get package.json template."""
        return f"""{{\n  "name": "{project_name.lower().replace('_', '-')}",
  "version": "0.1.0",
  "description": "Short description",
  "main": "src/index.js",
  "scripts": {{
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest"
  }},
  "keywords": [],
  "author": "",
  "license": "MIT",
  "dependencies": {{}},
  "devDependencies": {{}}
}}
"""

    def _get_react_package_json(self, project_name: str) -> str:
        """Get React package.json template."""
        return f"""{{\n  "name": "{project_name.lower().replace('_', '-')}",
  "version": "0.1.0",
  "private": true,
  "dependencies": {{
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  }},
  "scripts": {{
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }},
  "eslintConfig": {{
    "extends": ["react-app"]
  }},
  "browserslist": {{
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }}
}}
"""

    def _get_tsconfig(self) -> str:
        """Get tsconfig.json template."""
        return """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "strict": true,
    "jsx": "react-jsx",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "esModuleInterop": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"],
  "exclude": ["node_modules"]
}
"""

    def _get_react_html(self) -> str:
        """Get React index.html template."""
        return """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <title>React App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
"""

    def _get_next_steps(self, project_type: str) -> List[str]:
        """Get next steps after project creation.
        
        Args:
            project_type: Type of project
            
        Returns:
            List of next steps
        """
        steps = [
            "Review the project structure",
            "Update README.md with project description",
            "Configure development environment"
        ]
        
        if project_type == "python":
            steps.append("Create virtual environment: python -m venv venv")
            steps.append("Install dependencies: pip install -r requirements.txt")
        elif project_type == "nodejs" or project_type == "react":
            steps.append("Install dependencies: npm install")
            steps.append("Start development: npm run dev")
        
        return steps

    def _is_binary(self, file_path: Path) -> bool:
        """Check if file is binary.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if binary
        """
        try:
            file_path.read_text()
            return False
        except (UnicodeDecodeError, AttributeError):
            return True
