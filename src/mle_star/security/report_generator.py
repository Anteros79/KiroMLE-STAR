"""
Report Generator for Security Audit & Hardening.

This module generates the SECURITY_AUDIT.md report with executive summary,
critical findings table, and remediation plan.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from .models import (
    AuditReport,
    SecretFinding,
    VulnerableDependency,
    EndpointFinding,
    SecretCategory,
    OWASPCategory,
)


class ReportGenerator:
    """Generates the SECURITY_AUDIT.md report."""

    # Severity order for sorting (lower index = higher priority)
    SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    def __init__(self):
        """Initialize the report generator."""
        pass

    def _count_by_severity(
        self,
        secret_findings: List[SecretFinding],
        dependency_findings: List[VulnerableDependency],
        api_findings: List[EndpointFinding],
    ) -> Tuple[int, int, int, int]:
        """Count findings by severity level.
        
        Returns:
            Tuple of (critical_count, high_count, medium_count, low_count)
        """
        critical = 0
        high = 0
        medium = 0
        low = 0

        for finding in secret_findings:
            severity = finding.severity.lower()
            if severity == "critical":
                critical += 1
            elif severity == "high":
                high += 1
            elif severity == "medium":
                medium += 1
            else:
                low += 1

        for finding in dependency_findings:
            severity = finding.severity.lower()
            if severity == "critical":
                critical += 1
            elif severity == "high":
                high += 1
            elif severity == "medium":
                medium += 1
            else:
                low += 1

        for finding in api_findings:
            severity = finding.severity.lower()
            if severity == "critical":
                critical += 1
            elif severity == "high":
                high += 1
            elif severity == "medium":
                medium += 1
            else:
                low += 1

        return critical, high, medium, low

    def _calculate_risk_level(self, critical: int, high: int, medium: int, low: int) -> str:
        """Calculate overall risk assessment based on finding counts.
        
        Args:
            critical: Number of critical findings
            high: Number of high severity findings
            medium: Number of medium severity findings
            low: Number of low severity findings
            
        Returns:
            Risk level string: "CRITICAL", "HIGH", "MEDIUM", "LOW", or "MINIMAL"
        """
        if critical > 0:
            return "CRITICAL"
        elif high > 0:
            return "HIGH"
        elif medium > 0:
            return "MEDIUM"
        elif low > 0:
            return "LOW"
        else:
            return "MINIMAL"

    def generate_executive_summary(
        self,
        secret_findings: List[SecretFinding],
        dependency_findings: List[VulnerableDependency],
        api_findings: List[EndpointFinding],
    ) -> str:
        """Generate the executive summary section of the report.
        
        Args:
            secret_findings: List of detected secrets
            dependency_findings: List of vulnerable dependencies
            api_findings: List of API security issues
            
        Returns:
            Markdown formatted executive summary string
        """
        critical, high, medium, low = self._count_by_severity(
            secret_findings, dependency_findings, api_findings
        )
        total = critical + high + medium + low
        risk_level = self._calculate_risk_level(critical, high, medium, low)

        # Build summary text
        summary_lines = [
            "## Executive Summary",
            "",
            f"**Overall Risk Assessment: {risk_level}**",
            "",
            "### Key Statistics",
            "",
            f"- **Total Findings:** {total}",
            f"- **Critical:** {critical}",
            f"- **High:** {high}",
            f"- **Medium:** {medium}",
            f"- **Low:** {low}",
            "",
            "### Findings Breakdown",
            "",
            f"- **Hardcoded Secrets:** {len(secret_findings)}",
            f"- **Vulnerable Dependencies:** {len(dependency_findings)}",
            f"- **API Security Issues:** {len(api_findings)}",
            "",
        ]

        # Add risk assessment description
        if risk_level == "CRITICAL":
            summary_lines.extend([
                "### Risk Assessment Details",
                "",
                "⚠️ **CRITICAL RISK**: Immediate action required. Critical vulnerabilities "
                "have been identified that could lead to data breaches, unauthorized access, "
                "or system compromise. Address critical findings before deployment.",
                "",
            ])
        elif risk_level == "HIGH":
            summary_lines.extend([
                "### Risk Assessment Details",
                "",
                "🔴 **HIGH RISK**: Significant security issues detected. High severity "
                "vulnerabilities should be addressed promptly to prevent potential exploitation.",
                "",
            ])
        elif risk_level == "MEDIUM":
            summary_lines.extend([
                "### Risk Assessment Details",
                "",
                "🟡 **MEDIUM RISK**: Moderate security concerns identified. These issues "
                "should be addressed in the near term to improve security posture.",
                "",
            ])
        elif risk_level == "LOW":
            summary_lines.extend([
                "### Risk Assessment Details",
                "",
                "🟢 **LOW RISK**: Minor security issues detected. Consider addressing "
                "these findings as part of regular maintenance.",
                "",
            ])
        else:
            summary_lines.extend([
                "### Risk Assessment Details",
                "",
                "✅ **MINIMAL RISK**: No significant security issues detected. "
                "Continue monitoring and regular security reviews.",
                "",
            ])

        return "\n".join(summary_lines)

    def _get_finding_category(self, finding) -> str:
        """Get the category string for a finding."""
        if isinstance(finding, SecretFinding):
            return f"Secret: {finding.category.value}"
        elif isinstance(finding, VulnerableDependency):
            return f"Dependency: {finding.cve_id}"
        elif isinstance(finding, EndpointFinding):
            return f"API: {finding.owasp_category.value}"
        return "Unknown"

    def _get_finding_location(self, finding) -> str:
        """Get the location string for a finding."""
        if isinstance(finding, SecretFinding):
            return f"{finding.file_path}:{finding.line_number}"
        elif isinstance(finding, VulnerableDependency):
            return f"{finding.source_file} ({finding.package_name})"
        elif isinstance(finding, EndpointFinding):
            return f"{finding.file_path}:{finding.line_number}"
        return "Unknown"

    def _get_finding_description(self, finding) -> str:
        """Get the description string for a finding."""
        if isinstance(finding, SecretFinding):
            return f"Hardcoded {finding.pattern_name}: {finding.redacted_value}"
        elif isinstance(finding, VulnerableDependency):
            return finding.description[:80] + "..." if len(finding.description) > 80 else finding.description
        elif isinstance(finding, EndpointFinding):
            return finding.description[:80] + "..." if len(finding.description) > 80 else finding.description
        return "Unknown"

    def generate_findings_table(
        self,
        secret_findings: List[SecretFinding],
        dependency_findings: List[VulnerableDependency],
        api_findings: List[EndpointFinding],
    ) -> str:
        """Generate the critical findings table section of the report.
        
        Args:
            secret_findings: List of detected secrets
            dependency_findings: List of vulnerable dependencies
            api_findings: List of API security issues
            
        Returns:
            Markdown formatted findings table string
        """
        # Combine all findings with their type for sorting
        all_findings = []
        
        for finding in secret_findings:
            all_findings.append(("secret", finding))
        for finding in dependency_findings:
            all_findings.append(("dependency", finding))
        for finding in api_findings:
            all_findings.append(("api", finding))

        # Sort by severity (critical first)
        all_findings.sort(
            key=lambda x: self.SEVERITY_ORDER.get(x[1].severity.lower(), 4)
        )

        # Build table
        table_lines = [
            "## Critical Findings",
            "",
            "| ID | Category | Severity | Location | Description | Remediation Status |",
            "|:---|:---------|:---------|:---------|:------------|:-------------------|",
        ]

        for idx, (finding_type, finding) in enumerate(all_findings, 1):
            finding_id = f"F{idx:03d}"
            category = self._get_finding_category(finding)
            severity = finding.severity.upper()
            location = self._get_finding_location(finding)
            description = self._get_finding_description(finding)
            status = "Open"
            
            # Escape pipe characters in description
            description = description.replace("|", "\\|")
            location = location.replace("|", "\\|")
            
            table_lines.append(
                f"| {finding_id} | {category} | {severity} | {location} | {description} | {status} |"
            )

        if len(all_findings) == 0:
            table_lines.append("| - | No findings | - | - | - | - |")

        table_lines.append("")
        return "\n".join(table_lines)

    def _get_secret_remediation(self, category: SecretCategory) -> str:
        """Get remediation recommendation for a secret category."""
        remediation_map = {
            SecretCategory.API_KEY: "Move API key to environment variable or secrets manager",
            # TODO: SECURITY CRITICAL - Hardcoded password detected (password_assignment)
            SecretCategory.PASSWORD: "Use environment variables or a secure vault for passwords",
            SecretCategory.TOKEN: "Store tokens in environment variables or secrets manager",
            SecretCategory.PRIVATE_KEY: "Move private key to secure key management system",
            SecretCategory.CONNECTION_STRING: "Use environment variables for connection strings",
            SecretCategory.AWS_CREDENTIALS: "Use IAM roles or AWS Secrets Manager instead",
            SecretCategory.GENERIC_SECRET: "Move secret to environment variable or secrets manager",
        }
        return remediation_map.get(category, "Review and secure this credential")

    def _get_api_remediation(self, owasp_category: OWASPCategory) -> str:
        """Get remediation recommendation for an OWASP category."""
        remediation_map = {
            OWASPCategory.A01_BROKEN_ACCESS_CONTROL: "Add authentication/authorization checks",
            OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES: "Implement proper encryption and key management",
            OWASPCategory.A03_INJECTION: "Add input validation and parameterized queries",
            OWASPCategory.A04_INSECURE_DESIGN: "Review and improve security architecture",
            OWASPCategory.A05_SECURITY_MISCONFIGURATION: "Review and harden security configuration",
            OWASPCategory.A07_AUTH_FAILURES: "Implement proper authentication mechanisms",
        }
        return remediation_map.get(owasp_category, "Review security controls for this endpoint")

    def generate_remediation_plan(
        self,
        secret_findings: List[SecretFinding],
        dependency_findings: List[VulnerableDependency],
        api_findings: List[EndpointFinding],
    ) -> Tuple[str, List[str]]:
        """Generate the remediation plan section of the report.
        
        Args:
            secret_findings: List of detected secrets
            dependency_findings: List of vulnerable dependencies
            api_findings: List of API security issues
            
        Returns:
            Tuple of (markdown string, list of remediation items)
        """
        remediation_items = []
        plan_lines = [
            "## Remediation Plan",
            "",
            "### Priority 1: Critical Issues (Immediate Action Required)",
            "",
        ]

        priority_1 = []
        priority_2 = []
        priority_3 = []

        # Categorize secrets by severity
        for finding in secret_findings:
            item = f"**{finding.file_path}:{finding.line_number}** - {self._get_secret_remediation(finding.category)}"
            if finding.severity.lower() == "critical":
                priority_1.append(item)
            elif finding.severity.lower() == "high":
                priority_2.append(item)
            else:
                priority_3.append(item)
            remediation_items.append(item)

        # Categorize dependencies by severity
        for finding in dependency_findings:
            fixed_ver = f" (upgrade to {finding.fixed_version})" if finding.fixed_version else ""
            item = f"**{finding.package_name}** - Update from {finding.current_version}{fixed_ver}"
            if finding.severity.lower() == "critical":
                priority_1.append(item)
            elif finding.severity.lower() == "high":
                priority_2.append(item)
            else:
                priority_3.append(item)
            remediation_items.append(item)

        # Categorize API findings by severity
        for finding in api_findings:
            item = f"**{finding.endpoint_path}** ({finding.http_method}) - {self._get_api_remediation(finding.owasp_category)}"
            if finding.severity.lower() == "critical":
                priority_1.append(item)
            elif finding.severity.lower() == "high":
                priority_2.append(item)
            else:
                priority_3.append(item)
            remediation_items.append(item)

        # Add priority 1 items
        if priority_1:
            for item in priority_1:
                plan_lines.append(f"- [ ] {item}")
        else:
            plan_lines.append("_No critical issues found._")
        
        plan_lines.extend(["", "### Priority 2: High Severity Issues", ""])
        
        if priority_2:
            for item in priority_2:
                plan_lines.append(f"- [ ] {item}")
        else:
            plan_lines.append("_No high severity issues found._")

        plan_lines.extend(["", "### Priority 3: Medium/Low Severity Issues", ""])
        
        if priority_3:
            for item in priority_3:
                plan_lines.append(f"- [ ] {item}")
        else:
            plan_lines.append("_No medium/low severity issues found._")

        plan_lines.append("")
        return "\n".join(plan_lines), remediation_items

    def generate_report(
        self,
        secret_findings: List[SecretFinding],
        dependency_findings: List[VulnerableDependency],
        api_findings: List[EndpointFinding],
        output_path: Path,
    ) -> AuditReport:
        """Generate the complete SECURITY_AUDIT.md report.
        
        Args:
            secret_findings: List of detected secrets
            dependency_findings: List of vulnerable dependencies
            api_findings: List of API security issues
            output_path: Path where to write the report
            
        Returns:
            AuditReport dataclass with all report data
        """
        # Generate timestamp
        timestamp = datetime.now().isoformat()
        
        # Count findings by severity
        critical, high, medium, low = self._count_by_severity(
            secret_findings, dependency_findings, api_findings
        )
        total = critical + high + medium + low

        # Generate sections
        executive_summary = self.generate_executive_summary(
            secret_findings, dependency_findings, api_findings
        )
        findings_table = self.generate_findings_table(
            secret_findings, dependency_findings, api_findings
        )
        remediation_plan_md, remediation_items = self.generate_remediation_plan(
            secret_findings, dependency_findings, api_findings
        )

        # Assemble full report
        report_lines = [
            "# Security Audit Report",
            "",
            f"**Generated:** {timestamp}",
            "",
            "---",
            "",
            executive_summary,
            findings_table,
            remediation_plan_md,
            "---",
            "",
            "_This report was automatically generated by the MLE-STAR Security Scanner._",
            "",
        ]

        report_content = "\n".join(report_lines)

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content, encoding="utf-8")

        # Create and return AuditReport
        return AuditReport(
            timestamp=timestamp,
            executive_summary=executive_summary,
            total_findings=total,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            secret_findings=secret_findings,
            dependency_findings=dependency_findings,
            api_findings=api_findings,
            remediation_plan=remediation_items,
        )
