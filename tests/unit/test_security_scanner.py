"""
Unit tests for the SecurityScanner orchestrator.
"""

import tempfile
from pathlib import Path

import pytest

from mle_star.security import (
    ScanConfig,
    SecurityScanner,
)


class TestSecurityScanner:
    """Tests for the SecurityScanner class."""
    
    def test_scanner_initialization(self):
        """Test that SecurityScanner initializes correctly."""
        scanner = SecurityScanner()
        
        assert scanner.config is None
        assert scanner.secret_detector is not None
        assert scanner.dependency_analyzer is not None
        assert scanner.api_auditor is not None
        assert scanner.report_generator is not None
        assert scanner.source_marker is not None
    
    def test_scanner_with_config(self):
        """Test SecurityScanner initialization with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScanConfig(
                project_root=Path(tmpdir),
                scan_secrets=True,
                scan_dependencies=False,
                scan_api=False,
            )
            scanner = SecurityScanner(config)
            
            assert scanner.config == config
            assert scanner.config.scan_secrets is True
            assert scanner.config.scan_dependencies is False
    
    def test_create_default_config(self):
        """Test default config creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = SecurityScanner()
            config = scanner._create_default_config(Path(tmpdir))
            
            assert config.project_root == Path(tmpdir)
            assert config.scan_secrets is True
            assert config.scan_dependencies is True
            assert config.scan_api is True
            assert config.mark_critical is True
            assert ".git" in config.exclude_dirs
            assert ".venv" in config.exclude_dirs
    
    def test_scan_empty_directory(self):
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = SecurityScanner()
            result = scanner.scan(
                project_root=Path(tmpdir),
                skip_marking=True,
            )
            
            assert result is not None
            assert result.secret_findings == []
            assert result.dependency_findings == []
            assert result.api_findings == []
            assert result.scan_duration_seconds >= 0
    
    def test_scan_with_secret(self):
        """Test scanning a directory with a hardcoded secret."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with a fake secret
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text('API_KEY = "sk-1234567890abcdef1234567890abcdef1234567890abcdef12"')
            
            scanner = SecurityScanner()
            result = scanner.scan(
                project_root=Path(tmpdir),
                skip_marking=True,
            )
            
            # Should find the OpenAI-style key
            assert len(result.secret_findings) >= 1
    
    def test_get_findings_summary(self):
        """Test getting findings summary."""
        scanner = SecurityScanner()
        
        # Before scan, should be empty
        summary = scanner.get_findings_summary()
        assert summary["total"] == 0
        assert summary["secrets"] == 0
        assert summary["dependencies"] == 0
        assert summary["api"] == 0
    
    def test_reset(self):
        """Test resetting scanner state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with a secret
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text('API_KEY = "sk-1234567890abcdef1234567890abcdef1234567890abcdef12"')
            
            scanner = SecurityScanner()
            scanner.scan(project_root=Path(tmpdir), skip_marking=True)
            
            # Should have findings
            assert scanner.get_findings_summary()["total"] >= 1
            
            # Reset
            scanner.reset()
            
            # Should be empty
            assert scanner.get_findings_summary()["total"] == 0
    
    def test_scan_requires_project_root(self):
        """Test that scan raises error without project root."""
        scanner = SecurityScanner()
        
        with pytest.raises(ValueError, match="No project_root"):
            scanner.scan()


class TestSecurityScannerCLI:
    """Tests for CLI argument parsing."""
    
    def test_parse_args_defaults(self):
        """Test default argument values."""
        from mle_star.security.cli import parse_args
        
        args = parse_args([])
        
        assert args.project_root == "."
        assert args.output_path is None
        assert args.skip_secrets is False
        assert args.skip_dependencies is False
        assert args.skip_api is False
        assert args.skip_marking is False
        assert args.dry_run is False
        assert args.verbose is False
        assert args.quiet is False
    
    def test_parse_args_with_options(self):
        """Test parsing with various options."""
        from mle_star.security.cli import parse_args
        
        args = parse_args([
            "/path/to/project",
            "--output-path", "/path/to/report.md",
            "--skip-secrets",
            "--skip-marking",
            "--dry-run",
            "--verbose",
        ])
        
        assert args.project_root == "/path/to/project"
        assert args.output_path == "/path/to/report.md"
        assert args.skip_secrets is True
        assert args.skip_marking is True
        assert args.dry_run is True
        assert args.verbose is True
    
    def test_create_config_from_args(self):
        """Test creating ScanConfig from parsed args."""
        from mle_star.security.cli import parse_args, create_config_from_args
        
        with tempfile.TemporaryDirectory() as tmpdir:
            args = parse_args([
                tmpdir,
                "--skip-secrets",
                "--exclude-dirs", "build", "dist",
            ])
            
            config = create_config_from_args(args)
            
            assert config.project_root == Path(tmpdir).resolve()
            assert config.scan_secrets is False
            assert config.scan_dependencies is True
            assert "build" in config.exclude_dirs
            assert "dist" in config.exclude_dirs
