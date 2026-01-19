"""
Source Marker module for adding security comments to source files.

This module provides functionality to mark critical vulnerabilities in source
files by inserting TODO comments above lines with security findings.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

from .models import SecretFinding


@dataclass
class MarkedLocation:
    """Represents a location that was marked with a security comment.
    
    Attributes:
        file_path: Path to the marked file
        line_number: Original line number where the finding was located
        comment: The comment that was inserted
        finding_type: Type of security finding (e.g., "secret", "vulnerability")
        severity: Severity level of the finding
    """
    file_path: str
    line_number: int
    comment: str
    finding_type: str
    severity: str


class SourceMarker:
    """Marks critical vulnerabilities in source files with TODO comments.
    
    The marker inserts comments above lines containing security findings,
    using the appropriate comment format based on file type:
    - Python files (.py): # TODO: SECURITY CRITICAL - [description]
    - JS/TS files (.ts, .tsx, .js, .jsx): // TODO: SECURITY CRITICAL - [description]
    
    The marker preserves original code and only adds comment lines.
    Files in the tests/ directory are skipped to preserve test integrity.
    """
    
    # Comment format templates
    PYTHON_COMMENT = "# TODO: SECURITY CRITICAL - {description}"
    JS_TS_COMMENT = "// TODO: SECURITY CRITICAL - {description}"
    
    # File extensions and their comment formats
    PYTHON_EXTENSIONS = {".py"}
    JS_TS_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}
    
    # Directories to skip
    SKIP_DIRECTORIES = {"tests", "test", "__tests__"}
    
    def __init__(self):
        """Initialize the SourceMarker."""
        self._marked_locations: List[MarkedLocation] = []
    
    def get_comment_format(self, file_path: Path) -> Optional[str]:
        """Get the appropriate comment format for a file based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Comment format string with {description} placeholder, or None if
            the file type is not supported for marking
        """
        suffix = file_path.suffix.lower()
        
        if suffix in self.PYTHON_EXTENSIONS:
            return self.PYTHON_COMMENT
        elif suffix in self.JS_TS_EXTENSIONS:
            return self.JS_TS_COMMENT
        
        return None

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if a file should be skipped based on its path.
        
        Files in tests/ directories are skipped to preserve test integrity.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file should be skipped, False otherwise
        """
        # Check if any part of the path is a test directory
        parts = file_path.parts
        for part in parts:
            if part.lower() in self.SKIP_DIRECTORIES:
                return True
        return False
    
    def _get_indentation(self, line: str) -> str:
        """Extract the leading whitespace from a line.
        
        Args:
            line: The line of code
            
        Returns:
            The leading whitespace characters
        """
        stripped = line.lstrip()
        if not stripped:
            return ""
        return line[:len(line) - len(stripped)]
    
    def create_comment(self, file_path: Path, description: str, line: str = "") -> Optional[str]:
        """Create a security comment for a file.
        
        Args:
            file_path: Path to the file (used to determine comment format)
            description: Description of the security issue
            line: The line of code (used to match indentation)
            
        Returns:
            Formatted comment string, or None if file type not supported
        """
        comment_format = self.get_comment_format(file_path)
        if comment_format is None:
            return None
        
        indentation = self._get_indentation(line)
        comment = comment_format.format(description=description)
        return f"{indentation}{comment}"
    
    def insert_comment(
        self, 
        lines: List[str], 
        line_number: int, 
        comment: str
    ) -> List[str]:
        """Insert a comment above a specific line.
        
        Args:
            lines: List of lines in the file
            line_number: 1-indexed line number to insert comment above
            comment: The comment to insert
            
        Returns:
            New list of lines with the comment inserted
        """
        # Convert to 0-indexed
        index = line_number - 1
        
        # Validate line number
        if index < 0 or index >= len(lines):
            return lines
        
        # Create new list with comment inserted
        new_lines = lines[:index]
        new_lines.append(comment)
        new_lines.extend(lines[index:])
        
        return new_lines

    def mark_file(
        self, 
        file_path: Path, 
        findings: List[SecretFinding],
        dry_run: bool = False
    ) -> List[MarkedLocation]:
        """Mark a file with security comments for critical findings.
        
        Inserts TODO comments above lines with critical security findings.
        Only critical severity findings are marked.
        
        Args:
            file_path: Path to the file to mark
            findings: List of SecretFinding objects for this file
            dry_run: If True, don't actually modify the file
            
        Returns:
            List of MarkedLocation objects for all marked locations
        """
        marked_locations: List[MarkedLocation] = []
        
        # Skip files in test directories
        if self._should_skip_file(file_path):
            return marked_locations
        
        # Check if file type is supported
        comment_format = self.get_comment_format(file_path)
        if comment_format is None:
            return marked_locations
        
        # Filter to only critical findings
        critical_findings = [f for f in findings if f.severity == "critical"]
        if not critical_findings:
            return marked_locations
        
        # Sort findings by line number in descending order
        # This ensures we insert from bottom to top, preserving line numbers
        critical_findings.sort(key=lambda f: f.line_number, reverse=True)
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError, OSError):
            return marked_locations
        
        lines = content.splitlines()
        original_lines = lines.copy()
        
        # Track which lines already have security comments
        marked_line_numbers: Set[int] = set()
        
        for finding in critical_findings:
            # Skip if we've already marked this line
            if finding.line_number in marked_line_numbers:
                continue
            
            # Get the line to match indentation
            line_index = finding.line_number - 1
            if line_index < 0 or line_index >= len(original_lines):
                continue
            
            original_line = original_lines[line_index]
            
            # Create description based on finding
            description = f"Hardcoded {finding.category.value} detected ({finding.pattern_name})"
            
            # Create the comment
            comment = self.create_comment(file_path, description, original_line)
            if comment is None:
                continue
            
            # Insert the comment
            lines = self.insert_comment(lines, finding.line_number, comment)
            
            # Record the marked location
            marked_location = MarkedLocation(
                file_path=str(file_path),
                line_number=finding.line_number,
                comment=comment.strip(),
                finding_type="secret",
                severity=finding.severity
            )
            marked_locations.append(marked_location)
            marked_line_numbers.add(finding.line_number)
        
        # Write the modified content back to the file
        if not dry_run and marked_locations:
            try:
                new_content = '\n'.join(lines)
                # Preserve trailing newline if original had one
                if content.endswith('\n'):
                    new_content += '\n'
                file_path.write_text(new_content, encoding='utf-8')
            except (PermissionError, OSError):
                # If we can't write, return empty list
                return []
        
        # Add to internal tracking
        self._marked_locations.extend(marked_locations)
        
        return marked_locations

    def mark_files(
        self,
        findings_by_file: dict,
        dry_run: bool = False
    ) -> List[MarkedLocation]:
        """Mark multiple files with security comments.
        
        Args:
            findings_by_file: Dictionary mapping file paths to lists of findings
            dry_run: If True, don't actually modify files
            
        Returns:
            List of all MarkedLocation objects
        """
        all_marked: List[MarkedLocation] = []
        
        for file_path_str, findings in findings_by_file.items():
            file_path = Path(file_path_str)
            marked = self.mark_file(file_path, findings, dry_run)
            all_marked.extend(marked)
        
        return all_marked
    
    def get_marked_locations(self) -> List[MarkedLocation]:
        """Get all locations that have been marked.
        
        Returns:
            List of MarkedLocation objects for all marked locations
        """
        return self._marked_locations.copy()
    
    def clear_marked_locations(self) -> None:
        """Clear the internal list of marked locations."""
        self._marked_locations.clear()
    
    def get_marking_log(self) -> str:
        """Generate a log of all marked locations for inclusion in reports.
        
        Returns:
            Formatted string containing all marked locations
        """
        if not self._marked_locations:
            return "No files were marked with security comments."
        
        log_lines = [
            "## Marked Source Files",
            "",
            "The following locations were marked with security TODO comments:",
            "",
        ]
        
        # Group by file
        files_dict: dict = {}
        for loc in self._marked_locations:
            if loc.file_path not in files_dict:
                files_dict[loc.file_path] = []
            files_dict[loc.file_path].append(loc)
        
        for file_path, locations in sorted(files_dict.items()):
            log_lines.append(f"### `{file_path}`")
            log_lines.append("")
            for loc in sorted(locations, key=lambda x: x.line_number):
                log_lines.append(f"- Line {loc.line_number}: {loc.comment}")
            log_lines.append("")
        
        return '\n'.join(log_lines)
    
    def get_marked_files_list(self) -> List[str]:
        """Get a list of unique file paths that were marked.
        
        Returns:
            List of file paths that were marked
        """
        return list(set(loc.file_path for loc in self._marked_locations))
    
    @staticmethod
    def verify_code_preservation(original_content: str, modified_content: str) -> bool:
        """Verify that original code is preserved in modified content.
        
        This method checks that all non-comment lines from the original
        content are present in the modified content in the same order.
        
        Args:
            original_content: The original file content
            modified_content: The modified file content
            
        Returns:
            True if original code is preserved, False otherwise
        """
        original_lines = original_content.splitlines()
        modified_lines = modified_content.splitlines()
        
        # Filter out comment lines from modified content
        # (lines that start with # or // after stripping whitespace)
        non_comment_modified = []
        for line in modified_lines:
            stripped = line.strip()
            if stripped.startswith("# TODO: SECURITY CRITICAL"):
                continue
            if stripped.startswith("// TODO: SECURITY CRITICAL"):
                continue
            non_comment_modified.append(line)
        
        # All original lines should be present in the same order
        return original_lines == non_comment_modified
    
    @staticmethod
    def is_comment_line(line: str) -> bool:
        """Check if a line is a security comment added by the marker.
        
        Args:
            line: The line to check
            
        Returns:
            True if the line is a security comment, False otherwise
        """
        stripped = line.strip()
        return (
            stripped.startswith("# TODO: SECURITY CRITICAL") or
            stripped.startswith("// TODO: SECURITY CRITICAL")
        )
