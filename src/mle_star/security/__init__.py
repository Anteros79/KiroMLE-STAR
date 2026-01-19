"""
Security Audit & Hardening module for MLE-STAR.

This module provides comprehensive security scanning capabilities including:
- Hardcoded secret detection
- Dependency vulnerability analysis
- API endpoint security analysis
- Security audit report generation
"""

from .models import (
    SecretCategory,
    OWASPCategory,
    SecretFinding,
    VulnerableDependency,
    EndpointFinding,
    ScanConfig,
    ScanResult,
    AuditReport,
)
from .secret_detector import SecretDetector
from .dependency_analyzer import DependencyAnalyzer
from .api_auditor import APIAuditor
from .report_generator import ReportGenerator
from .source_marker import SourceMarker, MarkedLocation
from .scanner import SecurityScanner
from .cli import main as run_security_audit

__all__ = [
    "SecretCategory",
    "OWASPCategory",
    "SecretFinding",
    "VulnerableDependency",
    "EndpointFinding",
    "ScanConfig",
    "ScanResult",
    "AuditReport",
    "SecretDetector",
    "DependencyAnalyzer",
    "APIAuditor",
    "ReportGenerator",
    "SourceMarker",
    "MarkedLocation",
    "SecurityScanner",
    "run_security_audit",
]
