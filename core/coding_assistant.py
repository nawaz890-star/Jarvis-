"""Advanced Coding Assistant for multi-language development."""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class CodingAssistant:
    """Specialized assistant for coding tasks."""

    SUPPORTED_LANGUAGES = {
        "python": {"ext": ".py", "comment": "#"},
        "javascript": {"ext": ".js", "comment": "//"},
        "typescript": {"ext": ".ts", "comment": "//"},
        "java": {"ext": ".java", "comment": "//"},
        "cpp": {"ext": ".cpp", "comment": "//"},
        "csharp": {"ext": ".cs", "comment": "//"},
        "php": {"ext": ".php", "comment": "//"},
        "go": {"ext": ".go", "comment": "//"},
        "rust": {"ext": ".rs", "comment": "//"},
        "sql": {"ext": ".sql", "comment": "--"},
        "html": {"ext": ".html", "comment": "<!--"},
        "css": {"ext": ".css", "comment": "/*"},
        "jsx": {"ext": ".jsx", "comment": "//"},
        "tsx": {"ext": ".tsx", "comment": "//"},
        "vue": {"ext": ".vue", "comment": "//"},
    }

    def __init__(self, ai_engine: Any):
        """Initialize coding assistant.
        
        Args:
            ai_engine: Reference to AIEngine instance
        """
        self.ai_engine = ai_engine
        self.ai_engine.set_system_prompt(ai_engine.get_system_prompt_for_coding())

    def generate_code(self, description: str, language: str = "python", context: Optional[str] = None) -> Dict[str, Any]:
        """Generate code based on description.
        
        Args:
            description: What code to generate
            language: Programming language
            context: Additional context or requirements
            
        Returns:
            Dictionary with code and metadata
        """
        if language.lower() not in self.SUPPORTED_LANGUAGES:
            return {"error": f"Unsupported language: {language}. Supported: {', '.join(self.SUPPORTED_LANGUAGES.keys())}"}

        prompt = f"""Generate complete, production-ready {language} code for the following:

{description}

{f'Additional context: {context}' if context else ''}

Requirements:
1. Complete, working code (no pseudocode or placeholders)
2. Proper error handling and edge cases
3. Clear variable and function names
4. Docstrings/comments for complex logic
5. Follow {language} best practices and style conventions
6. Include any necessary imports or dependencies"""

        response = self.ai_engine.ask(prompt)
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(response, language)
        
        return {
            "language": language,
            "code": code_blocks[0] if code_blocks else response,
            "explanation": response,
            "file_extension": self.SUPPORTED_LANGUAGES[language.lower()]["ext"]
        }

    def explain_code(self, code: str, language: Optional[str] = None) -> str:
        """Explain what code does.
        
        Args:
            code: Code to explain
            language: Programming language (auto-detect if not provided)
            
        Returns:
            Explanation of the code
        """
        prompt = f"""Explain the following {language or 'code'}:

```{language or ''}
{code}
```

Provide:
1. What this code does
2. How it works step by step
3. Key concepts and patterns used
4. Performance characteristics
5. Potential improvements or issues"""

        return self.ai_engine.ask(prompt)

    def debug_code(self, code: str, error: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Debug code with error message.
        
        Args:
            code: Code with bug
            error: Error message or description
            language: Programming language
            
        Returns:
            Dictionary with fixed code and explanation
        """
        prompt = f"""Debug the following {language or 'code'} that's producing this error:

Error: {error}

Code:
```{language or ''}
{code}
```

Provide:
1. Root cause of the error
2. Fixed code
3. Explanation of the fix
4. How to prevent similar issues
5. Any related best practices"""

        response = self.ai_engine.ask(prompt)
        code_blocks = self._extract_code_blocks(response, language or "python")
        
        return {
            "original_code": code,
            "error": error,
            "fixed_code": code_blocks[0] if code_blocks else None,
            "explanation": response,
            "language": language
        }

    def refactor_code(self, code: str, language: Optional[str] = None, goals: Optional[List[str]] = None) -> Dict[str, Any]:
        """Refactor code for improvements.
        
        Args:
            code: Code to refactor
            language: Programming language
            goals: Refactoring goals (e.g., ["performance", "readability"])
            
        Returns:
            Dictionary with refactored code and changes
        """
        goals_text = ", ".join(goals) if goals else "performance, readability, maintainability"
        
        prompt = f"""Refactor the following {language or 'code'} for {goals_text}:

```{language or ''}
{code}
```

Provide:
1. Refactored code
2. Specific improvements made
3. Performance impact (if applicable)
4. Code quality metrics improved
5. Any breaking changes or migration guide needed"""

        response = self.ai_engine.ask(prompt)
        code_blocks = self._extract_code_blocks(response, language or "python")
        
        return {
            "original_code": code,
            "refactored_code": code_blocks[0] if code_blocks else None,
            "improvements": response,
            "language": language,
            "goals": goals
        }

    def generate_tests(self, code: str, language: str = "python", test_framework: Optional[str] = None) -> Dict[str, Any]:
        """Generate unit tests for code.
        
        Args:
            code: Code to test
            language: Programming language
            test_framework: Test framework (pytest, unittest, jest, etc.)
            
        Returns:
            Dictionary with test code and coverage info
        """
        default_frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "junit",
            "csharp": "xunit",
            "go": "testing",
            "rust": "cargo test"
        }
        
        framework = test_framework or default_frameworks.get(language.lower(), "default")
        
        prompt = f"""Generate comprehensive unit tests using {framework} for the following {language} code:

```{language}
{code}
```

Include:
1. Happy path tests
2. Edge case tests
3. Error handling tests
4. Invalid input tests
5. Performance tests (if applicable)
6. Mocking (if needed)
7. Minimum 80% code coverage

Provide complete, runnable test code."""

        response = self.ai_engine.ask(prompt)
        code_blocks = self._extract_code_blocks(response, language)
        
        return {
            "test_code": code_blocks[0] if code_blocks else response,
            "framework": framework,
            "language": language,
            "explanation": response
        }

    def generate_documentation(self, code: str, language: Optional[str] = None, style: str = "markdown") -> str:
        """Generate documentation for code.
        
        Args:
            code: Code to document
            language: Programming language
            style: Documentation style (markdown, html, docstring)
            
        Returns:
            Generated documentation
        """
        prompt = f"""Generate comprehensive {style} documentation for the following {language or 'code'}:

```{language or ''}
{code}
```

Include:
1. Overview and purpose
2. Function/method documentation
3. Parameters and return values
4. Usage examples
5. Error conditions
6. Performance notes
7. Related functions/classes
8. Version history (if applicable)

Format as {style}."""

        return self.ai_engine.ask(prompt)

    def create_file(self, path: str, content: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Create a new code file.
        
        Args:
            path: File path to create
            content: File content
            language: Programming language
            
        Returns:
            Operation status
        """
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            logger.info(f"Created file: {path}")
            return {
                "success": True,
                "path": str(path),
                "size": len(content),
                "language": language
            }
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            return {"success": False, "error": str(e)}

    def read_file(self, path: str) -> Optional[str]:
        """Read a code file.
        
        Args:
            path: File path to read
            
        Returns:
            File content or None
        """
        try:
            file_path = Path(path)
            if file_path.exists():
                return file_path.read_text()
            else:
                logger.warning(f"File not found: {path}")
                return None
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            return None

    def edit_file(self, path: str, changes: Dict[str, str]) -> Dict[str, Any]:
        """Edit a code file with specified changes.
        
        Args:
            path: File path to edit
            changes: Dictionary of old_text -> new_text
            
        Returns:
            Operation status
        """
        try:
            file_path = Path(path)
            content = file_path.read_text()
            
            for old_text, new_text in changes.items():
                content = content.replace(old_text, new_text)
            
            file_path.write_text(content)
            logger.info(f"Edited file: {path}")
            return {
                "success": True,
                "path": str(path),
                "changes": len(changes),
                "new_size": len(content)
            }
        except Exception as e:
            logger.error(f"Failed to edit file: {e}")
            return {"success": False, "error": str(e)}

    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze entire project structure.
        
        Args:
            project_path: Path to project root
            
        Returns:
            Project analysis
        """
        try:
            project_root = Path(project_path)
            
            stats = {
                "total_files": 0,
                "total_lines": 0,
                "languages": {},
                "structure": {},
                "largest_files": []
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
            logger.error(f"Failed to analyze project: {e}")
            return {"error": str(e)}

    def _extract_code_blocks(self, text: str, language: str = "") -> List[str]:
        """Extract code blocks from markdown-formatted text.
        
        Args:
            text: Text containing code blocks
            language: Expected language (optional)
            
        Returns:
            List of extracted code blocks
        """
        # Match ```language code ``` or ``` code ```
        pattern = r"```(?:\w+)?\n(.*?)\n```"
        matches = re.findall(pattern, text, re.DOTALL)
        return matches if matches else []
