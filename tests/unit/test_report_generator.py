"""
Unit tests for the Report Generator module.
"""

import pytest
from pathlib import Path
from datetime import datetime

from src.mle_star.security import (
    ReportGenerator,
    SecretFinding,
    VulnerableDependency,
    EndpointFinding,
    SecretCategory,
    OWASPCategory,
    AuditReport,
)


@pytest.fixture
def generator():
    """Create a ReportGenerator instance."""
    return ReportGenerator()


@pytest.fixture
def sample_secret_finding():
    """Create a sample secret finding."""
    return SecretFinding(
        file_path="src/config.py",
        line_number=10,
        category=SecretCategory.API_KEY,
        pattern_name="generic_api_key",
        redacted_value="sk-t...xyz1",
        context_line="API_KEY = sk-test-xyz1",
        severity="critical",
    )


@pytest.fixture
def sample_dependency_finding():
    """Create a sample dependency finding."""
    return VulnerableDependency(
        package_name="requests",
        current_version="2.25.0",
        cve_id="CVE-2023-1234",
        severity="high",
        description="Security vulnerability in requests library",
        fixed_version="2.28.0",
        source_file="requirements.txt",
    )


@pytest.fixture
def sample_api_finding():
    """Create a sample API finding."""
    return EndpointFinding(
        file_path="src/api/routes.py",
        line_number=25,
        endpoint_path="/api/users",
        http_method="GET",
        vulnerability="Missing authorization",
        owasp_category=OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
        severity="high",
        description="Endpoint lacks authentication checks",
        recommendation="Add authentication middleware",
    )


class TestCountBySeverity:
    """Tests for _count_by_severity method."""

    def test_empty_findings(self, generator):
        """Test counting with no findings."""
        critical, high, medium, low = generator._count_by_severity([], [], [])
        assert critical == 0
        assert high == 0
        assert medium == 0
        assert low == 0

    def test_single_critical_secret(self, generator, sample_secret_finding):
        """Test counting a single critical secret."""
        critical, high, medium, low = generator._count_by_severity(
            [sample_secret_finding], [], []
        )
        assert critical == 1
        assert high == 0

    def test_mixed_severities(self, generator, sample_secret_finding, sample_dependency_finding, sample_api_finding):
        """Test counting mixed severity findings."""
        critical, high, medium, low = generator._count_by_severity(
            [sample_secret_finding],
            [sample_dependency_finding],
            [sample_api_finding],
        )
        assert critical == 1
        assert high == 2
        assert medium == 0
        assert low == 0


class TestCalculateRiskLevel:
    """Tests for _calculate_risk_level method."""

    def test_critical_risk(self, generator):
        """Test critical risk level."""
        assert generator._calculate_risk_level(1, 0, 0, 0) == "CRITICAL"

    def test_high_risk(self, generator):
        """Test high risk level."""
        assert generator._calculate_risk_level(0, 1, 0, 0) == "HIGH"

    def test_medium_risk(self, generator):
        """Test medium risk level."""
        assert generator._calculate_risk_level(0, 0, 1, 0) == "MEDIUM"

    def test_low_risk(self, generator):
        """Test low risk level."""
        assert generator._calculate_risk_level(0, 0, 0, 1) == "LOW"

    def test_minimal_risk(self, generator):
        """Test minimal risk level."""
        assert generator._calculate_risk_level(0, 0, 0, 0) == "MINIMAL"


class TestExecutiveSummary:
    """Tests for generate_executive_summary method."""

    def test_summary_contains_required_sections(self, generator, sample_secret_finding):
        """Test that summary contains all required sections."""
        summary = generator.generate_executive_summary([sample_secret_finding], [], [])
        
        assert "## Executive Summary" in summary
        assert "**Overall Risk Assessment:" in summary
        assert "### Key Statistics" in summary
        assert "**Total Findings:**" in summary
        assert "**Critical:**" in summary
        assert "**High:**" in summary
        assert "**Medium:**" in summary
        assert "**Low:**" in summary
        assert "### Findings Breakdown" in summary

    def test_summary_shows_correct_counts(self, generator, sample_secret_finding, sample_dependency_finding):
        """Test that summary shows correct finding counts."""
        summary = generator.generate_executive_summary(
            [sample_secret_finding], [sample_dependency_finding], []
        )
        
        assert "**Total Findings:** 2" in summary
        assert "**Critical:** 1" in summary
        assert "**High:** 1" in summary
        assert "**Hardcoded Secrets:** 1" in summary
        assert "**Vulnerable Dependencies:** 1" in summary


class TestFindingsTable:
    """Tests for generate_findings_table method."""

    def test_table_has_required_columns(self, generator, sample_secret_finding):
        """Test that table has all required columns."""
        table = generator.generate_findings_table([sample_secret_finding], [], [])
        
        assert "## Critical Findings" in table
        assert "| ID |" in table
        assert "| Category |" in table
        assert "| Severity |" in table
        assert "| Location |" in table
        assert "| Description |" in table
        assert "| Remediation Status |" in table

    def test_table_sorted_by_severity(self, generator, sample_secret_finding, sample_dependency_finding):
        """Test that findings are sorted by severity (critical first)."""
        table = generator.generate_findings_table(
            [sample_secret_finding], [sample_dependency_finding], []
        )
        
        # Critical should appear before high
        critical_pos = table.find("CRITICAL")
        high_pos = table.find("HIGH")
        assert critical_pos < high_pos

    def test_empty_findings_shows_placeholder(self, generator):
        """Test that empty findings shows placeholder row."""
        table = generator.generate_findings_table([], [], [])
        assert "No findings" in table


class TestRemediationPlan:
    """Tests for generate_remediation_plan method."""

    def test_plan_has_priority_sections(self, generator, sample_secret_finding):
        """Test that plan has all priority sections."""
        plan, items = generator.generate_remediation_plan([sample_secret_finding], [], [])
        
        assert "## Remediation Plan" in plan
        assert "### Priority 1:" in plan
        assert "### Priority 2:" in plan
        assert "### Priority 3:" in plan

    def test_critical_in_priority_1(self, generator, sample_secret_finding):
        """Test that critical findings are in priority 1."""
        plan, items = generator.generate_remediation_plan([sample_secret_finding], [], [])
        
        # Critical finding should be in Priority 1 section
        priority_1_start = plan.find("### Priority 1:")
        priority_2_start = plan.find("### Priority 2:")
        priority_1_section = plan[priority_1_start:priority_2_start]
        
        assert "src/config.py:10" in priority_1_section

    def test_returns_remediation_items(self, generator, sample_secret_finding, sample_dependency_finding):
        """Test that remediation items list is returned."""
        plan, items = generator.generate_remediation_plan(
            [sample_secret_finding], [sample_dependency_finding], []
        )
        
        assert len(items) == 2


class TestGenerateReport:
    """Tests for generate_report method."""

    def test_report_creates_file(self, generator, sample_secret_finding, tmp_path):
        """Test that report creates the output file."""
        output_path = tmp_path / "SECURITY_AUDIT.md"
        
        generator.generate_report([sample_secret_finding], [], [], output_path)
        
        assert output_path.exists()

    def test_report_contains_all_sections(self, generator, sample_secret_finding, tmp_path):
        """Test that report contains all required sections."""
        output_path = tmp_path / "SECURITY_AUDIT.md"
        
        generator.generate_report([sample_secret_finding], [], [], output_path)
        
        content = output_path.read_text(encoding="utf-8")
        assert "# Security Audit Report" in content
        assert "**Generated:**" in content
        assert "## Executive Summary" in content
        assert "## Critical Findings" in content
        assert "## Remediation Plan" in content

    def test_report_returns_audit_report(self, generator, sample_secret_finding, tmp_path):
        """Test that generate_report returns AuditReport dataclass."""
        output_path = tmp_path / "SECURITY_AUDIT.md"
        
        result = generator.generate_report([sample_secret_finding], [], [], output_path)
        
        assert isinstance(result, AuditReport)
        assert result.total_findings == 1
        assert result.critical_count == 1
        assert len(result.secret_findings) == 1

    def test_report_has_valid_timestamp(self, generator, tmp_path):
        """Test that report has a valid ISO timestamp."""
        output_path = tmp_path / "SECURITY_AUDIT.md"
        
        result = generator.generate_report([], [], [], output_path)
        
        # Should be able to parse the timestamp
        datetime.fromisoformat(result.timestamp)
