"""
Unit tests for the DependencyAnalyzer component.

Tests the parsing of requirements.txt and package.json files,
as well as vulnerability checking functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from mle_star.security import DependencyAnalyzer, VulnerableDependency


class TestRequirementsTxtParser:
    """Tests for requirements.txt parsing functionality."""
    
    def test_parse_simple_requirements(self, tmp_path: Path):
        """Test parsing a simple requirements.txt file."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("""
fastapi>=0.109.0
uvicorn==0.27.0
pydantic~=2.5.0
requests
""")
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert "fastapi" in deps
        assert deps["fastapi"] == ">=0.109.0"
        assert "uvicorn" in deps
        assert deps["uvicorn"] == "==0.27.0"
        assert "pydantic" in deps
        assert deps["pydantic"] == "~=2.5.0"
        assert "requests" in deps
        assert deps["requests"] == ""
    
    def test_parse_requirements_with_comments(self, tmp_path: Path):
        """Test parsing requirements.txt with comments."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("""
# This is a comment
fastapi>=0.109.0  # inline comment
# Another comment
uvicorn==0.27.0
""")
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert len(deps) == 2
        assert "fastapi" in deps
        assert "uvicorn" in deps
    
    def test_parse_requirements_with_extras(self, tmp_path: Path):
        """Test parsing requirements.txt with extras."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("""
uvicorn[standard]>=0.27.0
requests[security,socks]>=2.28.0
""")
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert "uvicorn" in deps
        assert deps["uvicorn"] == ">=0.27.0"
        assert "requests" in deps
        assert deps["requests"] == ">=2.28.0"
    
    def test_parse_requirements_with_multiple_version_specs(self, tmp_path: Path):
        """Test parsing requirements.txt with multiple version specifiers."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("""
package>=1.0.0,<2.0.0
another>=1.0,!=1.5.0
""")
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert "package" in deps
        assert ">=1.0.0,<2.0.0" in deps["package"]
        assert "another" in deps
    
    def test_parse_requirements_skips_options(self, tmp_path: Path):
        """Test that pip options are skipped."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("""
-r base.txt
--index-url https://pypi.org/simple
-e git+https://github.com/user/repo.git
fastapi>=0.109.0
""")
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert len(deps) == 1
        assert "fastapi" in deps
    
    def test_parse_requirements_file_not_found(self, tmp_path: Path):
        """Test that FileNotFoundError is raised for missing file."""
        analyzer = DependencyAnalyzer()
        
        with pytest.raises(FileNotFoundError):
            analyzer.parse_requirements_txt(tmp_path / "nonexistent.txt")
    
    def test_parse_empty_requirements(self, tmp_path: Path):
        """Test parsing an empty requirements.txt file."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("")
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.parse_requirements_txt(req_file)
        
        assert deps == {}


class TestPackageJsonParser:
    """Tests for package.json parsing functionality."""
    
    def test_parse_simple_package_json(self, tmp_path: Path):
        """Test parsing a simple package.json file."""
        pkg_file = tmp_path / "package.json"
        pkg_file.write_text(json.dumps({
            "name": "test-package",
            "version": "1.0.0",
            "dependencies": {
                "react": "^18.2.0",
                "next": "14.2.0"
            }
        }))
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.parse_package_json(pkg_file)
        
        assert "react" in deps
        assert deps["react"] == "^18.2.0"
        assert "next" in deps
        assert deps["next"] == "14.2.0"
    
    def test_parse_package_json_with_dev_dependencies(self, tmp_path: Path):
        """Test parsing package.json with devDependencies."""
        pkg_file = tmp_path / "package.json"
        pkg_file.write_text(json.dumps({
            "name": "test-package",
            "dependencies": {
                "react": "^18.2.0"
            },
            "devDependencies": {
                "typescript": "^5.3.3",
                "eslint": "^8.56.0"
            }
        }))
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.parse_package_json(pkg_file)
        
        assert "react" in deps
        assert "typescript" in deps
        assert "eslint" in deps
        assert len(deps) == 3
    
    def test_parse_package_json_dependencies_take_precedence(self, tmp_path: Path):
        """Test that dependencies take precedence over devDependencies."""
        pkg_file = tmp_path / "package.json"
        pkg_file.write_text(json.dumps({
            "dependencies": {
                "shared-pkg": "^1.0.0"
            },
            "devDependencies": {
                "shared-pkg": "^2.0.0"
            }
        }))
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.parse_package_json(pkg_file)
        
        assert deps["shared-pkg"] == "^1.0.0"
    
    def test_parse_package_json_file_not_found(self, tmp_path: Path):
        """Test that FileNotFoundError is raised for missing file."""
        analyzer = DependencyAnalyzer()
        
        with pytest.raises(FileNotFoundError):
            analyzer.parse_package_json(tmp_path / "nonexistent.json")
    
    def test_parse_invalid_json(self, tmp_path: Path):
        """Test that ValueError is raised for invalid JSON."""
        pkg_file = tmp_path / "package.json"
        pkg_file.write_text("{ invalid json }")
        
        analyzer = DependencyAnalyzer()
        
        with pytest.raises(ValueError):
            analyzer.parse_package_json(pkg_file)
    
    def test_parse_empty_package_json(self, tmp_path: Path):
        """Test parsing a package.json with no dependencies."""
        pkg_file = tmp_path / "package.json"
        pkg_file.write_text(json.dumps({
            "name": "test-package",
            "version": "1.0.0"
        }))
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.parse_package_json(pkg_file)
        
        assert deps == {}


class TestVersionParsing:
    """Tests for version specifier parsing."""
    
    def test_parse_version_specifier(self):
        """Test parsing version specifiers."""
        analyzer = DependencyAnalyzer()
        
        specs = analyzer.parse_version_specifier(">=1.0.0")
        assert specs == [(">=", "1.0.0")]
        
        specs = analyzer.parse_version_specifier(">=1.0.0,<2.0.0")
        assert (">=", "1.0.0") in specs
        assert ("<", "2.0.0") in specs
        
        specs = analyzer.parse_version_specifier("==1.5.0")
        assert specs == [("==", "1.5.0")]
    
    def test_parse_empty_version_specifier(self):
        """Test parsing empty version specifier."""
        analyzer = DependencyAnalyzer()
        
        specs = analyzer.parse_version_specifier("")
        assert specs == []
    
    def test_get_pinned_version(self):
        """Test extracting pinned versions."""
        analyzer = DependencyAnalyzer()
        
        assert analyzer.get_pinned_version("==1.0.0") == "1.0.0"
        assert analyzer.get_pinned_version(">=1.0.0") is None
        assert analyzer.get_pinned_version(">=1.0.0,==1.5.0") == "1.5.0"
        assert analyzer.get_pinned_version("") is None


class TestSeverityMapping:
    """Tests for severity level mapping."""
    
    def test_map_severity(self):
        """Test severity string mapping."""
        analyzer = DependencyAnalyzer()
        
        assert analyzer._map_severity("critical") == "critical"
        assert analyzer._map_severity("CRITICAL") == "critical"
        assert analyzer._map_severity("high") == "high"
        assert analyzer._map_severity("HIGH") == "high"
        assert analyzer._map_severity("important") == "high"
        assert analyzer._map_severity("medium") == "medium"
        assert analyzer._map_severity("moderate") == "medium"
        assert analyzer._map_severity("low") == "low"
        assert analyzer._map_severity("info") == "low"
        assert analyzer._map_severity("unknown") == "medium"


class TestAnalyze:
    """Tests for the main analyze function."""
    
    def test_analyze_project_with_requirements(self, tmp_path: Path):
        """Test analyzing a project with requirements.txt."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("""
fastapi>=0.109.0
uvicorn==0.27.0
""")
        
        analyzer = DependencyAnalyzer()
        # Note: This won't find actual vulnerabilities without pip-audit
        # but it should run without errors
        findings = analyzer.analyze(tmp_path)
        
        # Should return a list (possibly empty if pip-audit not available)
        assert isinstance(findings, list)
    
    def test_analyze_project_with_package_json(self, tmp_path: Path):
        """Test analyzing a project with package.json."""
        pkg_file = tmp_path / "package.json"
        pkg_file.write_text(json.dumps({
            "name": "test",
            "dependencies": {"react": "^18.0.0"}
        }))
        
        analyzer = DependencyAnalyzer()
        findings = analyzer.analyze(tmp_path)
        
        assert isinstance(findings, list)
    
    def test_get_summary(self):
        """Test generating a summary of findings."""
        analyzer = DependencyAnalyzer()
        
        findings = [
            VulnerableDependency(
                package_name="pkg1",
                current_version="1.0.0",
                cve_id="CVE-2024-0001",
                severity="critical",
                description="Test",
                fixed_version="1.0.1",
                source_file="requirements.txt"
            ),
            VulnerableDependency(
                package_name="pkg2",
                current_version="2.0.0",
                cve_id="CVE-2024-0002",
                severity="high",
                description="Test",
                fixed_version="2.0.1",
                source_file="requirements.txt"
            ),
            VulnerableDependency(
                package_name="pkg3",
                current_version="3.0.0",
                cve_id="CVE-2024-0003",
                severity="low",
                description="Test",
                fixed_version=None,
                source_file="requirements.txt"
            ),
        ]
        
        summary = analyzer.get_summary(findings)
        
        assert summary["total"] == 3
        assert summary["critical"] == 1
        assert summary["high"] == 1
        assert summary["medium"] == 0
        assert summary["low"] == 1
