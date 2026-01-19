"""
Core data models for the Security Audit & Hardening feature.

This module defines all enums, dataclasses, and type definitions used
throughout the security scanning system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional


class SecretCategory(Enum):
    """Categories of hardcoded secrets that can be detected."""
    
    API_KEY = "api_key"
    # TODO: SECURITY CRITICAL - Hardcoded password detected (password_assignment)
    PASSWORD = "password"
    TOKEN = "token"
    PRIVATE_KEY = "private_key"
    CONNECTION_STRING = "connection_string"
    AWS_CREDENTIALS = "aws_credentials"
    GENERIC_SECRET = "generic_secret"


class OWASPCategory(Enum):
    """OWASP Top 10 2021 vulnerability categories."""
    
    A01_BROKEN_ACCESS_CONTROL = "A01:2021-Broken Access Control"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021-Cryptographic Failures"
    A03_INJECTION = "A03:2021-Injection"
    A04_INSECURE_DESIGN = "A04:2021-Insecure Design"
    A05_SECURITY_MISCONFIGURATION = "A05:2021-Security Misconfiguration"
    A07_AUTH_FAILURES = "A07:2021-Identification and Authentication Failures"


@dataclass
class SecretFinding:
    """Represents a detected hardcoded secret in source code.
    
    Attributes:
        file_path: Path to the file containing the secret
        line_number: Line number where the secret was found
        category: Type of secret detected
        pattern_name: Name of the regex pattern that matched
        redacted_value: Redacted version showing only first 4 + "..." + last 4 chars
        context_line: The line of code with the secret redacted
        severity: Severity level ("critical", "high", "medium")
    """
    
    file_path: str
    line_number: int
    category: SecretCategory
    pattern_name: str
    redacted_value: str
    context_line: str
    severity: str


@dataclass
class VulnerableDependency:
    """Represents a dependency with known vulnerabilities.
    
    Attributes:
        package_name: Name of the vulnerable package
        current_version: Currently installed version
        cve_id: CVE identifier for the vulnerability
        severity: Severity level ("critical", "high", "medium", "low")
        description: Description of the vulnerability
        fixed_version: Version that fixes the vulnerability (if known)
        source_file: Source file where dependency was found
    """
    
    package_name: str
    current_version: str
    cve_id: str
    severity: str
    description: str
    fixed_version: Optional[str]
    source_file: str


@dataclass
class EndpointFinding:
    """Represents a security finding for an API endpoint.
    
    Attributes:
        file_path: Path to the file containing the endpoint
        line_number: Line number of the endpoint definition
        endpoint_path: URL path of the endpoint
        http_method: HTTP method (GET, POST, etc.)
        vulnerability: Description of the vulnerability
        owasp_category: Relevant OWASP Top 10 category
        severity: Severity level
        description: Detailed description of the issue
        recommendation: Recommended fix
    """
    
    file_path: str
    line_number: int
    endpoint_path: str
    http_method: str
    vulnerability: str
    owasp_category: OWASPCategory
    severity: str
    description: str
    recommendation: str


@dataclass
class ScanConfig:
    """Configuration for the security scanner.
    
    Attributes:
        project_root: Root directory of the project to scan
        exclude_dirs: Set of directory names to exclude from scanning
        exclude_files: Set of file patterns to exclude
        scan_secrets: Whether to scan for hardcoded secrets
        scan_dependencies: Whether to scan for vulnerable dependencies
        scan_api: Whether to scan API endpoints
        mark_critical: Whether to add TODO comments for critical findings
        api_directories: List of directories to scan for API endpoints
    """
    
    project_root: Path
    exclude_dirs: set = field(default_factory=lambda: {
        ".git", ".venv", "node_modules", "__pycache__", ".next", ".hypothesis"
    })
    exclude_files: set = field(default_factory=lambda: {"*.pyc", "*.lock"})
    scan_secrets: bool = True
    scan_dependencies: bool = True
    scan_api: bool = True
    mark_critical: bool = True
    api_directories: List[str] = field(default_factory=lambda: ["src/mle_star/api", "routes"])


@dataclass
class ScanResult:
    """Complete result of a security scan.
    
    Attributes:
        config: Configuration used for the scan
        secret_findings: List of detected hardcoded secrets
        dependency_findings: List of vulnerable dependencies
        api_findings: List of API endpoint security issues
        marked_files: List of files that were marked with TODO comments
        scan_duration_seconds: Time taken to complete the scan
        scanned_files_count: Number of files scanned
        timestamp: When the scan was performed
    """
    
    config: ScanConfig
    secret_findings: List[SecretFinding]
    dependency_findings: List[VulnerableDependency]
    api_findings: List[EndpointFinding]
    marked_files: List[str]
    scan_duration_seconds: float
    scanned_files_count: int
    timestamp: datetime


@dataclass
class AuditReport:
    """Complete security audit report data.
    
    Attributes:
        timestamp: When the audit was performed
        executive_summary: High-level summary of findings
        total_findings: Total number of security findings
        critical_count: Number of critical severity findings
        high_count: Number of high severity findings
        medium_count: Number of medium severity findings
        low_count: Number of low severity findings
        secret_findings: List of detected secrets
        dependency_findings: List of vulnerable dependencies
        api_findings: List of API security issues
        remediation_plan: List of prioritized remediation actions
    """
    
    timestamp: str
    executive_summary: str
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    secret_findings: List[SecretFinding]
    dependency_findings: List[VulnerableDependency]
    api_findings: List[EndpointFinding]
    remediation_plan: List[str]
