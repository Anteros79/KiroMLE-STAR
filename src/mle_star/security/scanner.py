"""
Security Scanner orchestrator for the Security Audit & Hardening feature.

This module provides the main SecurityScanner class that coordinates all
security analysis components: SecretDetector, DependencyAnalyzer, APIAuditor,
ReportGenerator, and SourceMarker.
"""

import logging
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .api_auditor import APIAuditor
from .dependency_analyzer import DependencyAnalyzer
from .models import (
    EndpointFinding,
    ScanConfig,
    ScanResult,
    SecretFinding,
    VulnerableDependency,
)
from .report_generator import ReportGenerator
from .secret_detector import SecretDetector
from .source_marker import MarkedLocation, SourceMarker

logger = logging.getLogger(__name__)


class SecurityScanner:
    """Main orchestrator for security scanning operations.
    
    The SecurityScanner coordinates all security analysis components to perform
    a comprehensive security audit of a codebase. It manages:
    - Secret detection in source files
    - Dependency vulnerability analysis
    - API endpoint security analysis
    - Report generation
    - Source file marking with security comments
    
    Attributes:
        config: ScanConfig object with scan settings
        secret_detector: SecretDetector instance
        dependency_analyzer: DependencyAnalyzer instance
        api_auditor: APIAuditor instance
        report_generator: ReportGenerator instance
        source_marker: SourceMarker instance
    """
    
    def __init__(self, config: Optional[ScanConfig] = None):
        """Initialize the SecurityScanner with configuration.
        
        Args:
            config: Optional ScanConfig object. If not provided, a default
                   configuration will be created when scan() is called.
        """
        self.config = config
        self.secret_detector = SecretDetector()
        self.dependency_analyzer = DependencyAnalyzer()
        self.api_auditor = APIAuditor()
        self.report_generator = ReportGenerator()
        self.source_marker = SourceMarker()
        
        # Results storage
        self._secret_findings: List[SecretFinding] = []
        self._dependency_findings: List[VulnerableDependency] = []
        self._api_findings: List[EndpointFinding] = []
        self._marked_files: List[str] = []
        self._scanned_files_count: int = 0
    
    def _create_default_config(self, project_root: Path) -> ScanConfig:
        """Create a default ScanConfig for the given project root.
        
        Args:
            project_root: Root directory of the project to scan
            
        Returns:
            ScanConfig with default settings
        """
        return ScanConfig(
            project_root=project_root,
            exclude_dirs={".git", ".venv", "node_modules", "__pycache__", ".next", ".hypothesis"},
            exclude_files={"*.pyc", "*.lock"},
            scan_secrets=True,
            scan_dependencies=True,
            scan_api=True,
            mark_critical=True,
            api_directories=["src/mle_star/api", "routes", "api"],
        )
    
    def scan_secrets(self) -> List[SecretFinding]:
        """Run secret detection on the project.
        
        Returns:
            List of SecretFinding objects for detected secrets
        """
        if not self.config or not self.config.scan_secrets:
            logger.info("Secret scanning disabled or no config")
            return []
        
        logger.info(f"Scanning for secrets in {self.config.project_root}")
        
        findings = self.secret_detector.scan_directory(
            self.config.project_root,
            self.config.exclude_dirs
        )
        
        logger.info(f"Found {len(findings)} potential secrets")
        
        # Generate summary
        category_summary = self.secret_detector.generate_category_summary(findings)
        for category, count in category_summary.items():
            logger.info(f"  - {category.value}: {count}")
        
        return findings
    
    def scan_dependencies(self) -> List[VulnerableDependency]:
        """Run dependency vulnerability analysis on the project.
        
        Returns:
            List of VulnerableDependency objects for vulnerable packages
        """
        if not self.config or not self.config.scan_dependencies:
            logger.info("Dependency scanning disabled or no config")
            return []
        
        logger.info(f"Analyzing dependencies in {self.config.project_root}")
        
        findings = self.dependency_analyzer.analyze(self.config.project_root)
        
        logger.info(f"Found {len(findings)} vulnerable dependencies")
        
        # Generate summary
        summary = self.dependency_analyzer.get_summary(findings)
        logger.info(f"  - Critical: {summary['critical']}")
        logger.info(f"  - High: {summary['high']}")
        logger.info(f"  - Medium: {summary['medium']}")
        logger.info(f"  - Low: {summary['low']}")
        
        return findings
    
    def scan_api(self) -> List[EndpointFinding]:
        """Run API endpoint security analysis on the project.
        
        Returns:
            List of EndpointFinding objects for API security issues
        """
        if not self.config or not self.config.scan_api:
            logger.info("API scanning disabled or no config")
            return []
        
        logger.info(f"Analyzing API endpoints in {self.config.project_root}")
        
        findings = self.api_auditor.analyze_api_directories(
            self.config.project_root,
            self.config.api_directories
        )
        
        logger.info(f"Found {len(findings)} API security issues")
        
        # Generate summary
        summary = self.api_auditor.generate_summary(findings)
        logger.info(f"  - Unique endpoints analyzed: {summary.get('unique_endpoints', 0)}")
        for vuln_type, count in summary.get('by_vulnerability_type', {}).items():
            logger.info(f"  - {vuln_type}: {count}")
        
        return findings
    
    def mark_critical_findings(
        self, 
        secret_findings: List[SecretFinding],
        dry_run: bool = False
    ) -> List[str]:
        """Mark critical findings in source files with TODO comments.
        
        Args:
            secret_findings: List of secret findings to potentially mark
            dry_run: If True, don't actually modify files
            
        Returns:
            List of file paths that were marked
        """
        if not self.config or not self.config.mark_critical:
            logger.info("Source marking disabled or no config")
            return []
        
        logger.info("Marking critical findings in source files")
        
        # Group findings by file
        findings_by_file: Dict[str, List[SecretFinding]] = defaultdict(list)
        for finding in secret_findings:
            findings_by_file[finding.file_path].append(finding)
        
        # Mark files
        marked_locations = self.source_marker.mark_files(findings_by_file, dry_run)
        
        # Get list of marked files
        marked_files = self.source_marker.get_marked_files_list()
        
        logger.info(f"Marked {len(marked_locations)} locations in {len(marked_files)} files")
        
        return marked_files
    
    def generate_report(
        self,
        secret_findings: List[SecretFinding],
        dependency_findings: List[VulnerableDependency],
        api_findings: List[EndpointFinding],
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate the security audit report.
        
        Args:
            secret_findings: List of detected secrets
            dependency_findings: List of vulnerable dependencies
            api_findings: List of API security issues
            output_path: Optional path for the report. Defaults to
                        project_root/SECURITY_AUDIT.md
            
        Returns:
            Path to the generated report
        """
        if output_path is None:
            if self.config:
                output_path = self.config.project_root / "SECURITY_AUDIT.md"
            else:
                output_path = Path("SECURITY_AUDIT.md")
        
        logger.info(f"Generating security audit report at {output_path}")
        
        self.report_generator.generate_report(
            secret_findings,
            dependency_findings,
            api_findings,
            output_path,
        )
        
        logger.info("Report generated successfully")
        
        return output_path
    
    def _count_scanned_files(self) -> int:
        """Count the number of files that were scanned.
        
        Returns:
            Number of files scanned
        """
        if not self.config:
            return 0
        
        count = 0
        for item in self.config.project_root.rglob("*"):
            if item.is_file():
                # Check if in excluded directory
                if any(part in self.config.exclude_dirs for part in item.parts):
                    continue
                # Check file extension for secret scanning
                if item.suffix.lower() in self.secret_detector.FILE_EXTENSIONS:
                    count += 1
        
        return count
    
    def scan(
        self,
        project_root: Optional[Path] = None,
        output_path: Optional[Path] = None,
        skip_marking: bool = False,
        dry_run: bool = False,
    ) -> ScanResult:
        """Execute a complete security scan on the project.
        
        This is the main entry point for running a security audit. It:
        1. Scans for hardcoded secrets
        2. Analyzes dependencies for vulnerabilities
        3. Audits API endpoints for security issues
        4. Marks critical findings in source files (unless skip_marking=True)
        5. Generates the SECURITY_AUDIT.md report
        
        Args:
            project_root: Root directory to scan. Uses config.project_root if not provided.
            output_path: Path for the report. Defaults to project_root/SECURITY_AUDIT.md
            skip_marking: If True, skip marking source files with TODO comments
            dry_run: If True, don't modify any files (report still generated)
            
        Returns:
            ScanResult containing all findings and scan metadata
            
        Raises:
            ValueError: If no project_root is provided and no config exists
        """
        start_time = time.time()
        
        # Determine project root
        if project_root is not None:
            project_root = Path(project_root).resolve()
        elif self.config is not None:
            project_root = self.config.project_root
        else:
            raise ValueError("No project_root provided and no config set")
        
        # Create or update config
        if self.config is None:
            self.config = self._create_default_config(project_root)
        else:
            self.config.project_root = project_root
        
        # Apply skip_marking override
        if skip_marking:
            self.config.mark_critical = False
        
        logger.info(f"Starting security scan of {project_root}")
        logger.info(f"  - Scan secrets: {self.config.scan_secrets}")
        logger.info(f"  - Scan dependencies: {self.config.scan_dependencies}")
        logger.info(f"  - Scan API: {self.config.scan_api}")
        logger.info(f"  - Mark critical: {self.config.mark_critical}")
        
        # Run all scan phases
        self._secret_findings = self.scan_secrets()
        self._dependency_findings = self.scan_dependencies()
        self._api_findings = self.scan_api()
        
        # Mark critical findings
        if self.config.mark_critical and not dry_run:
            self._marked_files = self.mark_critical_findings(
                self._secret_findings, 
                dry_run=dry_run
            )
        else:
            self._marked_files = []
        
        # Generate report
        report_path = self.generate_report(
            self._secret_findings,
            self._dependency_findings,
            self._api_findings,
            output_path,
        )
        
        # Calculate scan duration
        scan_duration = time.time() - start_time
        
        # Count scanned files
        self._scanned_files_count = self._count_scanned_files()
        
        logger.info(f"Security scan completed in {scan_duration:.2f} seconds")
        logger.info(f"  - Files scanned: {self._scanned_files_count}")
        logger.info(f"  - Total findings: {len(self._secret_findings) + len(self._dependency_findings) + len(self._api_findings)}")
        logger.info(f"  - Report: {report_path}")
        
        # Create and return ScanResult
        return ScanResult(
            config=self.config,
            secret_findings=self._secret_findings,
            dependency_findings=self._dependency_findings,
            api_findings=self._api_findings,
            marked_files=self._marked_files,
            scan_duration_seconds=scan_duration,
            scanned_files_count=self._scanned_files_count,
            timestamp=datetime.now(),
        )
    
    def get_findings_summary(self) -> Dict[str, int]:
        """Get a summary of all findings from the last scan.
        
        Returns:
            Dictionary with finding counts by type and severity
        """
        summary = {
            "total": 0,
            "secrets": len(self._secret_findings),
            "dependencies": len(self._dependency_findings),
            "api": len(self._api_findings),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        
        # Count by severity
        for finding in self._secret_findings:
            severity = finding.severity.lower()
            if severity in summary:
                summary[severity] += 1
        
        for finding in self._dependency_findings:
            severity = finding.severity.lower()
            if severity in summary:
                summary[severity] += 1
        
        for finding in self._api_findings:
            severity = finding.severity.lower()
            if severity in summary:
                summary[severity] += 1
        
        summary["total"] = summary["secrets"] + summary["dependencies"] + summary["api"]
        
        return summary
    
    def reset(self) -> None:
        """Reset the scanner state, clearing all findings and marked locations."""
        self._secret_findings = []
        self._dependency_findings = []
        self._api_findings = []
        self._marked_files = []
        self._scanned_files_count = 0
        self.source_marker.clear_marked_locations()
