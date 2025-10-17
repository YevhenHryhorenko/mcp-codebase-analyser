"""
Code parser and indexer for extracting structure from codebases.
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CodeSection:
    """Represents a section of code (function, class, component, etc.)"""
    
    def __init__(
        self,
        name: str,
        type: str,
        file_path: str,
        start_line: int,
        end_line: int,
        code: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.type = type  # function, class, component, section, etc.
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.code = code
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.type,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "code": self.code,
            "metadata": self.metadata,
            "context": self._generate_context()
        }
    
    def _generate_context(self) -> str:
        """Generate contextual description for embedding."""
        return (
            f"File: {self.file_path}\n"
            f"Type: {self.type}\n"
            f"Name: {self.name}\n"
            f"Lines: {self.start_line}-{self.end_line}\n"
            f"Code:\n{self.code}"
        )
    
    def __repr__(self) -> str:
        return f"CodeSection(name={self.name}, type={self.type}, file={self.file_path})"


class CodeParser:
    """Parses code files and extracts sections."""
    
    # File extensions we support
    SUPPORTED_EXTENSIONS = {
        ".js", ".jsx", ".ts", ".tsx",  # JavaScript/TypeScript
        ".py",  # Python
        ".java",  # Java
        ".go",  # Go
        ".rs",  # Rust
        ".cpp", ".c", ".h", ".hpp",  # C/C++
        ".liquid",  # Shopify Liquid templates
        ".html", ".htm",  # HTML
        ".vue",  # Vue components
        ".css", ".scss", ".sass", ".less",  # Stylesheets
    }
    
    # Patterns for different code structures
    PATTERNS = {
        # CSS/SCSS Sections
        "css_class": [
            r"\.([a-zA-Z][\w-]*)\s*\{",  # CSS classes (.my-class {)
        ],
        "css_id": [
            r"#([a-zA-Z][\w-]*)\s*\{",  # CSS IDs (#my-id {)
        ],
        "css_keyframes": [
            r"@keyframes\s+([a-zA-Z][\w-]*)",  # CSS animations
        ],
        "scss_mixin": [
            r"@mixin\s+([a-zA-Z][\w-]*)",  # SCSS mixins
        ],
        "scss_function": [
            r"@function\s+([a-zA-Z][\w-]*)",  # SCSS functions
        ],
        # Liquid Sections and Snippets
        "liquid_section": [
            r"{%\s*schema\s*%}",  # Liquid schema blocks (sections)
        ],
        "liquid_block": [
            r"{%\s*block\s+['\"]?(\w+)['\"]?",  # Liquid blocks
            r"{%\s*for\s+(\w+)\s+in",  # Liquid for loops
            r"{%\s*if\s+(\w+)",  # Liquid conditionals
        ],
        # React/JS/TS Components
        "react_component": [
            r"(?:export\s+)?(?:default\s+)?(?:const|let|var|function)\s+(\w+)\s*=\s*(?:\([^)]*\))?\s*(?::\s*\w+\s*)?=>\s*\{",
            r"(?:export\s+)?(?:default\s+)?function\s+(\w+)\s*\([^)]*\)\s*(?::\s*\w+\s*)?\{",
            r"(?:export\s+)?(?:default\s+)?class\s+(\w+)\s+extends\s+(?:React\.)?Component",
        ],
        # Functions
        "function": [
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
            r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
            r"def\s+(\w+)\s*\(",  # Python
            r"func\s+(\w+)\s*\(",  # Go
            r"fn\s+(\w+)\s*\(",  # Rust
        ],
        # Classes
        "class": [
            r"(?:export\s+)?(?:default\s+)?class\s+(\w+)",
            r"class\s+(\w+)\s*(?:\([^)]*\))?:",  # Python
            r"type\s+(\w+)\s+struct",  # Go
            r"struct\s+(\w+)",  # Rust/C++
        ],
        # Interfaces/Types
        "interface": [
            r"(?:export\s+)?interface\s+(\w+)",
            r"(?:export\s+)?type\s+(\w+)\s*=",
        ],
    }
    
    def __init__(
        self,
        max_file_size_kb: int = 500,
        supported_extensions: Optional[List[str]] = None,
        skip_patterns: Optional[List[str]] = None
    ):
        """
        Initialize the code parser.
        
        Args:
            max_file_size_kb: Maximum file size to parse in KB
            supported_extensions: List of file extensions to parse
            skip_patterns: List of file name patterns to skip (e.g., ['.min.js', 'bundle-'])
        """
        self.max_file_size_kb = max_file_size_kb
        self.supported_extensions = set(supported_extensions) if supported_extensions else self.SUPPORTED_EXTENSIONS
        
        # Default skip patterns for minified/bundled files
        default_skip_patterns = [
            '.min.js', '.min.css', '.min.html',
            '.chunk.js', '.bundle.js', 
            '-min.js', '_min.js',
            '.production.js', '.prod.js',
            'bundle-main.js', 'bundle-product.js', 
            'bundle-customer.js', 'bundle-cart.js',
            'bundle-', 'chunk-',
        ]
        self.skip_patterns = skip_patterns if skip_patterns is not None else default_skip_patterns
    
    def should_parse_file(self, file_path: Path) -> bool:
        """Check if a file should be parsed."""
        # Check extension
        if file_path.suffix not in self.supported_extensions:
            return False
        
        # Skip files matching skip patterns (minified/bundled files, etc.)
        file_name = file_path.name.lower()
        if any(pattern in file_name for pattern in self.skip_patterns):
            logger.debug(f"Skipping {file_path}: matches skip pattern")
            return False
        
        # Check file size
        try:
            size_kb = file_path.stat().st_size / 1024
            if size_kb > self.max_file_size_kb:
                logger.debug(f"Skipping {file_path}: too large ({size_kb:.1f} KB)")
                return False
        except Exception:
            return False
        
        # Skip common directories
        skip_dirs = {
            "node_modules", ".git", "dist", "build", "coverage",
            "__pycache__", ".pytest_cache", "venv", ".venv",
            "vendor", "target", ".next", ".nuxt", "out"
        }
        
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            return False
        
        return True
    
    def parse_file(self, file_path: Path, repo_root: Path) -> List[CodeSection]:
        """
        Parse a single file and extract code sections.
        
        Args:
            file_path: Path to the file to parse
            repo_root: Root directory of the repository
        
        Returns:
            List of CodeSection objects
        """
        sections = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            relative_path = str(file_path.relative_to(repo_root))
            lines = content.split('\n')
            
            # Try to extract sections using patterns
            sections.extend(self._extract_with_patterns(content, lines, relative_path))
            
            # If no sections found, treat whole file as one section
            if not sections and len(content.strip()) > 0:
                # Limit code to prevent huge sections (was 3000, now 5000 for better coverage)
                max_code_length = 5000
                truncated_code = content[:max_code_length]
                if len(content) > max_code_length:
                    truncated_code += "\n... (truncated)"
                    
                sections.append(CodeSection(
                    name=file_path.stem,
                    type="file",
                    file_path=relative_path,
                    start_line=1,
                    end_line=len(lines),
                    code=truncated_code,
                    metadata={"extension": file_path.suffix}
                ))
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
        
        return sections
    
    def _extract_with_patterns(
        self, 
        content: str, 
        lines: List[str], 
        relative_path: str
    ) -> List[CodeSection]:
        """Extract code sections using regex patterns."""
        sections = []
        
        for section_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    try:
                        # Try to get name from capture group, fallback to file name
                        try:
                            name = match.group(1)
                        except IndexError:
                            # No capture group, use filename + type
                            name = f"{Path(relative_path).stem}_{section_type}"
                        
                        start_pos = match.start()
                        
                        # Find line number
                        start_line = content[:start_pos].count('\n') + 1
                        
                        # Extract the section (try to find matching braces)
                        section_code, end_line = self._extract_section_code(
                            lines, start_line, start_pos, content
                        )
                        
                        if section_code:
                            # Limit section code length to prevent token limit issues
                            # Keep more code for better semantic search (was 3000, now 5000)
                            max_section_length = 5000
                            if len(section_code) > max_section_length:
                                section_code = section_code[:max_section_length] + "\n... (truncated)"
                            
                            sections.append(CodeSection(
                                name=name,
                                type=section_type,
                                file_path=relative_path,
                                start_line=start_line,
                                end_line=end_line,
                                code=section_code,
                                metadata={
                                    "pattern_type": section_type,
                                    "file_extension": Path(relative_path).suffix
                                }
                            ))
                    except Exception as e:
                        logger.debug(f"Error extracting section: {e}")
                        continue
        
        return sections
    
    def _extract_section_code(
        self, 
        lines: List[str], 
        start_line: int, 
        start_pos: int,
        content: str
    ) -> tuple[str, int]:
        """
        Extract code section by finding matching braces.
        
        Returns:
            Tuple of (code, end_line)
        """
        # Simple brace matching
        brace_count = 0
        in_section = False
        section_lines = []
        end_line = start_line
        
        for i in range(start_line - 1, min(len(lines), start_line + 500)):  # Limit lookahead
            line = lines[i]
            section_lines.append(line)
            
            # Count braces
            for char in line:
                if char == '{':
                    brace_count += 1
                    in_section = True
                elif char == '}':
                    brace_count -= 1
                    if in_section and brace_count == 0:
                        end_line = i + 1
                        return '\n'.join(section_lines), end_line
        
        # If we didn't find matching braces, return what we have (up to 50 lines)
        max_lines = min(50, len(section_lines))
        return '\n'.join(section_lines[:max_lines]), start_line + max_lines - 1
    
    def parse_repository(self, repo_path: Path) -> List[CodeSection]:
        """
        Parse entire repository and extract all code sections.
        
        Args:
            repo_path: Path to the repository root
        
        Returns:
            List of all CodeSection objects found
        """
        all_sections = []
        
        logger.info(f"Parsing repository: {repo_path}")
        
        # Walk through all files
        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            if not self.should_parse_file(file_path):
                continue
            
            sections = self.parse_file(file_path, repo_path)
            all_sections.extend(sections)
            
            if sections:
                logger.debug(f"Found {len(sections)} sections in {file_path.name}")
        
        logger.info(f"Parsed repository: found {len(all_sections)} code sections")
        
        return all_sections

