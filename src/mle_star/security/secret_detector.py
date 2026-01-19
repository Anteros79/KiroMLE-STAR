"""
Secret Detector module for identifying hardcoded secrets in source code.

This module provides functionality to scan source files for hardcoded secrets
such as API keys, passwords, tokens, private keys, and connection strings.
"""

import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import SecretCategory, SecretFinding


class SecretDetector:
    """Detects hardcoded secrets in source files using regex patterns.
    
    The detector scans files for patterns matching various types of secrets
    including AWS credentials, API keys, passwords, tokens, private keys,
    and connection strings.
    
    Attributes:
        PATTERNS: Dictionary mapping pattern names to (regex, category, severity) tuples
        FILE_EXTENSIONS: Set of file extensions to scan
    """
    
    # Regex patterns for secret detection
    # Each pattern is a tuple of (regex_pattern, category, severity)
    PATTERNS: Dict[str, Tuple[str, SecretCategory, str]] = {
        "aws_access_key": (
            r'(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}',
            SecretCategory.AWS_CREDENTIALS,
            "critical"
        ),
        "aws_secret_key": (
            r'(?i)aws[_\-]?secret[_\-]?(?:access[_\-]?)?key["\']?\s*[:=]\s*["\']?([A-Za-z0-9/+=]{40})',
            SecretCategory.AWS_CREDENTIALS,
            "critical"
        ),
        "generic_api_key": (
            r'(?i)(?:api[_\-]?key|apikey)["\']?\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})',
            SecretCategory.API_KEY,
            "high"
        ),
        "password_assignment": (
            r'(?i)(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']([^"\']{8,})["\']',
            SecretCategory.PASSWORD,
            "critical"
        ),
        "bearer_token": (
            r'(?i)bearer\s+([A-Za-z0-9_\-\.]{20,})',
            SecretCategory.TOKEN,
            "high"
        ),
        "jwt_token": (
            r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
            SecretCategory.TOKEN,
            "high"
        ),
        "private_key": (
            r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
            SecretCategory.PRIVATE_KEY,
            "critical"
        ),
        "connection_string": (
            r'(?i)(?:mongodb|postgres|mysql|redis)://[^\s"\']+',
            SecretCategory.CONNECTION_STRING,
            "high"
        ),
        "openai_key": (
            r'sk-[A-Za-z0-9]{48}',
            SecretCategory.API_KEY,
            "critical"
        ),
        "github_token": (
            r'(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}',
            SecretCategory.TOKEN,
            "critical"
        ),
        "slack_token": (
            r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}',
            SecretCategory.TOKEN,
            "high"
        ),
        "stripe_key": (
            r'(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{24,}',
            SecretCategory.API_KEY,
            "critical"
        ),
        "google_api_key": (
            r'AIza[0-9A-Za-z\-_]{35}',
            SecretCategory.API_KEY,
            "high"
        ),
    }
    
    # File extensions to scan for secrets
    FILE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml", ".env"}
    
    def __init__(self):
        """Initialize the SecretDetector with compiled regex patterns."""
        self._compiled_patterns: Dict[str, Tuple[re.Pattern, SecretCategory, str]] = {}
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile all regex patterns for efficient matching."""
        for name, (pattern, category, severity) in self.PATTERNS.items():
            try:
                compiled = re.compile(pattern)
                self._compiled_patterns[name] = (compiled, category, severity)
            except re.error as e:
                # Log warning but continue with other patterns
                print(f"Warning: Failed to compile pattern '{name}': {e}")
    
    def redact_value(self, value: str) -> str:
        """Redact a secret value, showing only first 4 and last 4 characters.
        
        Args:
            value: The secret value to redact
            
        Returns:
            Redacted string in format "xxxx...xxxx" for values >= 8 chars,
            or "****" for shorter values
        """
        if len(value) < 8:
            return "*" * len(value)
        return f"{value[:4]}...{value[-4:]}"
    
    def _redact_line(self, line: str, secret: str) -> str:
        """Redact a secret within a line of code.
        
        Args:
            line: The original line of code
            secret: The secret value to redact
            
        Returns:
            The line with the secret replaced by its redacted form
        """
        redacted = self.redact_value(secret)
        return line.replace(secret, redacted)
    
    def scan_line(self, line: str, line_number: int, file_path: str) -> List[SecretFinding]:
        """Scan a single line for secrets.
        
        Args:
            line: The line of code to scan
            line_number: The line number (1-indexed)
            file_path: Path to the file being scanned
            
        Returns:
            List of SecretFinding objects for any secrets found
        """
        findings = []
        
        for pattern_name, (compiled_pattern, category, severity) in self._compiled_patterns.items():
            matches = compiled_pattern.finditer(line)
            for match in matches:
                # Get the matched secret value
                # If there's a capture group, use it; otherwise use the full match
                if match.groups():
                    secret_value = match.group(1)
                else:
                    secret_value = match.group(0)
                
                # Skip if the secret is too short (likely a false positive)
                if len(secret_value) < 8:
                    continue
                
                finding = SecretFinding(
                    file_path=file_path,
                    line_number=line_number,
                    category=category,
                    pattern_name=pattern_name,
                    redacted_value=self.redact_value(secret_value),
                    context_line=self._redact_line(line.rstrip(), secret_value),
                    severity=severity
                )
                findings.append(finding)
        
        return findings
    
    def scan_file(self, file_path: Path) -> List[SecretFinding]:
        """Scan a single file for hardcoded secrets.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            List of SecretFinding objects for any secrets found
        """
        findings = []
        
        # Check file extension
        if file_path.suffix.lower() not in self.FILE_EXTENSIONS:
            return findings
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError, OSError):
            # Skip files that can't be read
            return findings
        
        lines = content.splitlines()
        for line_number, line in enumerate(lines, start=1):
            line_findings = self.scan_line(line, line_number, str(file_path))
            findings.extend(line_findings)
        
        return findings
    
    def scan_directory(
        self, 
        directory: Path, 
        exclude_dirs: Optional[set] = None
    ) -> List[SecretFinding]:
        """Scan a directory recursively for hardcoded secrets.
        
        Args:
            directory: Root directory to scan
            exclude_dirs: Set of directory names to exclude from scanning
            
        Returns:
            List of SecretFinding objects for all secrets found
        """
        if exclude_dirs is None:
            exclude_dirs = {".git", ".venv", "node_modules", "__pycache__", ".next", ".hypothesis"}
        
        findings = []
        
        if not directory.exists() or not directory.is_dir():
            return findings
        
        for item in directory.iterdir():
            if item.is_dir():
                # Skip excluded directories
                if item.name in exclude_dirs:
                    continue
                # Recursively scan subdirectories
                findings.extend(self.scan_directory(item, exclude_dirs))
            elif item.is_file():
                # Scan files with matching extensions
                findings.extend(self.scan_file(item))
        
        return findings
    
    def generate_category_summary(self, findings: List[SecretFinding]) -> Dict[SecretCategory, int]:
        """Generate a summary count of findings by category.
        
        Args:
            findings: List of SecretFinding objects
            
        Returns:
            Dictionary mapping SecretCategory to count of findings
        """
        counter = Counter(finding.category for finding in findings)
        return dict(counter)
    
    def generate_severity_summary(self, findings: List[SecretFinding]) -> Dict[str, int]:
        """Generate a summary count of findings by severity.
        
        Args:
            findings: List of SecretFinding objects
            
        Returns:
            Dictionary mapping severity level to count of findings
        """
        counter = Counter(finding.severity for finding in findings)
        return dict(counter)
