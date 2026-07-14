"""Coding Assistant - Generate, analyze, debug, and refactor code across multiple languages."""

import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class CodingAssistant:
    """Advanced coding assistant with multi-language support."""

    SUPPORTED_LANGUAGES = {
        "python": {"ext": ".py", "comment": "#", "run": "python"},
        "javascript": {"ext": ".js", "comment": "//", "run": "node"},
        "typescript": {"ext": ".ts", "comment": "//", "run": "ts-node"},
        "react": {"ext": ".jsx", "comment": "//", "framework": "react"},
        "java": {"ext": ".java", "comment": "//", "run": "java"},
        "cpp": {"ext": ".cpp", "comment": "//", "run": "g++"},
        "csharp": {"ext": ".cs", "comment": "//", "run": "dotnet"},
        "php": {"ext": ".php", "comment": "//", "run": "php"},
        "go": {"ext": ".go", "comment": "//", "run": "go"},
        "rust": {"ext": ".rs", "comment": "//", "run": "cargo"},
        "sql": {"ext": ".sql", "comment": "--"},
        "html": {"ext": ".html", "comment": "<!--"},
        "css": {"ext": ".css", "comment": "/*"},
        "nextjs": {"ext": ".js", "comment": "//", "framework": "next"},
    }

    def __init__(self, ai_manager: Any):
        """Initialize Coding Assistant.
        
        Args:
            ai_manager: AI provider manager instance
        """
        self.ai_manager = ai_manager

    async def generate_code(self, description: str, language: str = "python", context: Optional[str] = None) -> Dict[str, Any]:
        """Generate code from description.
        
        Args:
            description: What code to generate
            language: Programming language
            context: Additional requirements
            
        Returns:
            Generated code with metadata
        """
        if language.lower() not in self.SUPPORTED_LANGUAGES:
            return {"error": f"Unsupported language: {language}"}

        prompt = f"""Generate production-ready {language} code:

{description}

{f'Context: {context}' if context else ''}

Requirements:
1. Complete, working code (no pseudocode)
2. Error handling
3. Type hints (if applicable)
4. Clear documentation
5. Follow best practices
6. Include imports and dependencies"""

        response = await self.ai_manager.ask(prompt)
        code_blocks = self._extract_code_blocks(response.content)

        return {
            "language": language,
            "code": code_blocks[0] if code_blocks else response.content,
            "explanation": response.content,
            "file_extension": self.SUPPORTED_LANGUAGES[language.lower()]["ext"]
        }

    async def debug_code(self, code: str, error: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Debug code with error message.
        
        Args:
            code: Code with bug
            error: Error message
            language: Programming language
            
        Returns:
            Fixed code and explanation
        """
        prompt = f"""Debug this {language or 'code'} that's producing this error:

Error: {error}

Code:
```{language or ''}
{code}
```

Provide:
1. Root cause
2. Fixed code
3. Explanation
4. Prevention tips"""

        response = await self.ai_manager.ask(prompt)
        code_blocks = self._extract_code_blocks(response.content)

        return {
            "original_code": code,
            "error": error,
            "fixed_code": code_blocks[0] if code_blocks else None,
            "explanation": response.content,
            "language": language
        }

    async def refactor_code(self, code: str, language: Optional[str] = None, goals: Optional[List[str]] = None) -> Dict[str, Any]:
        """Refactor code for improvements.
        
        Args:
            code: Code to refactor
            language: Programming language
            goals: Refactoring goals
            
        Returns:
            Refactored code
        """
        goals_text = ", ".join(goals) if goals else "readability, performance, maintainability"

        prompt = f"""Refactor this {language or 'code'} for {goals_text}:

```{language or ''}
{code}
```

Provide refactored code with improvements explained."""

        response = await self.ai_manager.ask(prompt)
        code_blocks = self._extract_code_blocks(response.content)

        return {
            "original_code": code,
            "refactored_code": code_blocks[0] if code_blocks else None,
            "improvements": response.content,
            "language": language,
            "goals": goals
        }

    async def generate_tests(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Generate unit tests.
        
        Args:
            code: Code to test
            language: Programming language
            
        Returns:
            Test code
        """
        default_frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "junit",
            "go": "testing",
            "rust": "cargo test"
        }

        framework = default_frameworks.get(language.lower(), "default")

        prompt = f"""Generate comprehensive unit tests using {framework} for:

```{language}
{code}
```

Include:
- Happy path tests
- Edge cases
- Error handling
- 80%+ coverage

Provide complete test code."""

        response = await self.ai_manager.ask(prompt)
        code_blocks = self._extract_code_blocks(response.content)

        return {
            "test_code": code_blocks[0] if code_blocks else response.content,
            "framework": framework,
            "language": language,
            "explanation": response.content
        }

    async def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze project structure.
        
        Args:
            project_path: Path to project
            
        Returns:
            Project analysis
        """
        try:
            project_root = Path(project_path)
            if not project_root.exists():
                return {"error": f"Project not found: {project_path}"}

            stats = {
                "total_files": 0,
                "total_lines": 0,
                "languages": {},
                "largest_files": [],
                "issues": []
            }

            for file_path in project_root.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    stats["total_files"] += 1
                    ext = file_path.suffix

                    if ext in [v["ext"] for v in self.SUPPORTED_LANGUAGES.values()]:
                        try:
                            lines = len(file_path.read_text().split("\n"))
                            stats["total_lines"] += lines
                            stats["languages"][ext] = stats["languages"].get(ext, 0) + 1
                            stats["largest_files"].append((str(file_path), lines))
                        except:
                            pass

            stats["largest_files"] = sorted(stats["largest_files"], key=lambda x: x[1], reverse=True)[:5]
            return stats
        except Exception as e:
            logger.error(f"Project analysis error: {e}")
            return {"error": str(e)}

    def create_file(self, path: str, content: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Create code file.
        
        Args:
            path: File path
            content: File content
            language: Programming language
            
        Returns:
            Creation status
        """
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            logger.info(f"Created file: {path}")
            return {"success": True, "path": str(path), "size": len(content)}
        except Exception as e:
            logger.error(f"File creation error: {e}")
            return {"success": False, "error": str(e)}

    def read_file(self, path: str) -> Optional[str]:
        """Read code file.
        
        Args:
            path: File path
            
        Returns:
            File content
        """
        try:
            file_path = Path(path)
            if file_path.exists():
                return file_path.read_text()
            return None
        except Exception as e:
            logger.error(f"File read error: {e}")
            return None

    def edit_file(self, path: str, changes: Dict[str, str]) -> Dict[str, Any]:
        """Edit code file.
        
        Args:
            path: File path
            changes: Text replacements
            
        Returns:
            Edit status
        """
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

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks from markdown.
        
        Args:
            text: Markdown text
            
        Returns:
            List of code blocks
        """
        pattern = r"```(?:\w+)?\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        return matches if matches else []
