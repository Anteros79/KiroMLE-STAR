"""
Unit tests for the Source Marker module.
"""

import tempfile
from pathlib import Path

import pytest

from src.mle_star.security.models import SecretCategory, SecretFinding
from src.mle_star.security.source_marker import SourceMarker, MarkedLocation


class TestSourceMarker:
    """Tests for the SourceMarker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.marker = SourceMarker()
    
    def test_get_comment_format_python(self):
        """Test that Python files get the correct comment format."""
        path = Path("test.py")
        comment_format = self.marker.get_comment_format(path)
        assert comment_format == "# TODO: SECURITY CRITICAL - {description}"
    
    def test_get_comment_format_typescript(self):
        """Test that TypeScript files get the correct comment format."""
        path = Path("test.ts")
        comment_format = self.marker.get_comment_format(path)
        assert comment_format == "// TODO: SECURITY CRITICAL - {description}"
    
    def test_get_comment_format_javascript(self):
        """Test that JavaScript files get the correct comment format."""
        path = Path("test.js")
        comment_format = self.marker.get_comment_format(path)
        assert comment_format == "// TODO: SECURITY CRITICAL - {description}"
    
    def test_get_comment_format_tsx(self):
        """Test that TSX files get the correct comment format."""
        path = Path("test.tsx")
        comment_format = self.marker.get_comment_format(path)
        assert comment_format == "// TODO: SECURITY CRITICAL - {description}"
    
    def test_get_comment_format_jsx(self):
        """Test that JSX files get the correct comment format."""
        path = Path("test.jsx")
        comment_format = self.marker.get_comment_format(path)
        assert comment_format == "// TODO: SECURITY CRITICAL - {description}"
    
    def test_get_comment_format_unsupported(self):
        """Test that unsupported file types return None."""
        path = Path("test.json")
        comment_format = self.marker.get_comment_format(path)
        assert comment_format is None
    
    def test_create_comment_python(self):
        """Test creating a comment for a Python file."""
        path = Path("test.py")
        comment = self.marker.create_comment(path, "Test description", "    code_line()")
        assert comment == "    # TODO: SECURITY CRITICAL - Test description"
    
    def test_create_comment_javascript(self):
        """Test creating a comment for a JavaScript file."""
        path = Path("test.js")
        comment = self.marker.create_comment(path, "Test description", "  const x = 1;")
        assert comment == "  // TODO: SECURITY CRITICAL - Test description"
    
    def test_create_comment_preserves_indentation(self):
        """Test that comments preserve the indentation of the target line."""
        path = Path("test.py")
        comment = self.marker.create_comment(path, "Test", "\t\tindented_code()")
        assert comment.startswith("\t\t")
    
    def test_insert_comment(self):
        """Test inserting a comment above a specific line."""
        lines = ["line1", "line2", "line3"]
        comment = "# comment"
        result = self.marker.insert_comment(lines, 2, comment)
        assert result == ["line1", "# comment", "line2", "line3"]
    
    def test_insert_comment_at_first_line(self):
        """Test inserting a comment at the first line."""
        lines = ["line1", "line2"]
        comment = "# comment"
        result = self.marker.insert_comment(lines, 1, comment)
        assert result == ["# comment", "line1", "line2"]
    
    def test_insert_comment_invalid_line_number(self):
        """Test that invalid line numbers don't modify the file."""
        lines = ["line1", "line2"]
        result = self.marker.insert_comment(lines, 10, "# comment")
        assert result == lines
    
    def test_should_skip_tests_directory(self):
        """Test that files in tests/ directory are skipped."""
        path = Path("tests/unit/test_file.py")
        assert self.marker._should_skip_file(path) is True
    
    def test_should_skip_test_directory(self):
        """Test that files in test/ directory are skipped."""
        path = Path("test/test_file.py")
        assert self.marker._should_skip_file(path) is True
    
    def test_should_not_skip_src_directory(self):
        """Test that files in src/ directory are not skipped."""
        path = Path("src/module/file.py")
        assert self.marker._should_skip_file(path) is False

    def test_mark_file_with_critical_finding(self):
        """Test marking a file with a critical finding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("line1\napi_key = 'AKIAIOSFODNN7EXAMPLE'\nline3\n")
            
            # Create a finding
            finding = SecretFinding(
                file_path=str(test_file),
                line_number=2,
                category=SecretCategory.AWS_CREDENTIALS,
                pattern_name="aws_access_key",
                redacted_value="AKIA...MPLE",
                context_line="api_key = 'AKIA...MPLE'",
                severity="critical"
            )
            
            # Mark the file
            marked = self.marker.mark_file(test_file, [finding])
            
            # Verify the file was marked
            assert len(marked) == 1
            assert marked[0].line_number == 2
            assert "SECURITY CRITICAL" in marked[0].comment
            
            # Verify the file content
            content = test_file.read_text()
            assert "# TODO: SECURITY CRITICAL" in content
            assert "api_key = 'AKIAIOSFODNN7EXAMPLE'" in content
    
    def test_mark_file_skips_non_critical(self):
        """Test that non-critical findings are not marked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("line1\napi_key = 'some_key_value_here'\nline3\n")
            
            finding = SecretFinding(
                file_path=str(test_file),
                line_number=2,
                category=SecretCategory.API_KEY,
                pattern_name="generic_api_key",
                redacted_value="some...here",
                context_line="api_key = 'some...here'",
                severity="high"  # Not critical
            )
            
            marked = self.marker.mark_file(test_file, [finding])
            
            # Should not mark non-critical findings
            assert len(marked) == 0
    
    def test_mark_file_skips_tests_directory(self):
        """Test that files in tests/ directory are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file in tests directory
            tests_dir = Path(tmpdir) / "tests"
            tests_dir.mkdir()
            test_file = tests_dir / "test_file.py"
            test_file.write_text("api_key = 'AKIAIOSFODNN7EXAMPLE'\n")
            
            finding = SecretFinding(
                file_path=str(test_file),
                line_number=1,
                category=SecretCategory.AWS_CREDENTIALS,
                pattern_name="aws_access_key",
                redacted_value="AKIA...MPLE",
                context_line="api_key = 'AKIA...MPLE'",
                severity="critical"
            )
            
            marked = self.marker.mark_file(test_file, [finding])
            
            # Should skip files in tests directory
            assert len(marked) == 0
    
    def test_mark_file_dry_run(self):
        """Test that dry_run mode doesn't modify files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            original_content = "api_key = 'AKIAIOSFODNN7EXAMPLE'\n"
            test_file.write_text(original_content)
            
            finding = SecretFinding(
                file_path=str(test_file),
                line_number=1,
                category=SecretCategory.AWS_CREDENTIALS,
                pattern_name="aws_access_key",
                redacted_value="AKIA...MPLE",
                context_line="api_key = 'AKIA...MPLE'",
                severity="critical"
            )
            
            marked = self.marker.mark_file(test_file, [finding], dry_run=True)
            
            # Should return marked locations
            assert len(marked) == 1
            
            # But file should not be modified
            assert test_file.read_text() == original_content
    
    def test_get_marking_log(self):
        """Test generating a marking log."""
        # Add some marked locations
        self.marker._marked_locations = [
            MarkedLocation(
                file_path="src/test.py",
                line_number=10,
                comment="# TODO: SECURITY CRITICAL - Test",
                finding_type="secret",
                severity="critical"
            )
        ]
        
        log = self.marker.get_marking_log()
        
        assert "Marked Source Files" in log
        assert "src/test.py" in log
        assert "Line 10" in log
    
    def test_get_marking_log_empty(self):
        """Test marking log when no files were marked."""
        log = self.marker.get_marking_log()
        assert "No files were marked" in log
    
    def test_get_marked_files_list(self):
        """Test getting list of marked files."""
        self.marker._marked_locations = [
            MarkedLocation("file1.py", 1, "comment", "secret", "critical"),
            MarkedLocation("file1.py", 2, "comment", "secret", "critical"),
            MarkedLocation("file2.py", 1, "comment", "secret", "critical"),
        ]
        
        files = self.marker.get_marked_files_list()
        
        assert len(files) == 2
        assert "file1.py" in files
        assert "file2.py" in files



class TestCodePreservation:
    """Tests for code preservation safeguards."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.marker = SourceMarker()
    
    def test_verify_code_preservation_unchanged(self):
        """Test that identical content passes verification."""
        content = "line1\nline2\nline3"
        assert SourceMarker.verify_code_preservation(content, content) is True
    
    def test_verify_code_preservation_with_comments(self):
        """Test that content with added comments passes verification."""
        original = "line1\nline2\nline3"
        modified = "# TODO: SECURITY CRITICAL - Test\nline1\nline2\nline3"
        assert SourceMarker.verify_code_preservation(original, modified) is True
    
    def test_verify_code_preservation_with_js_comments(self):
        """Test that content with JS comments passes verification."""
        original = "const x = 1;\nconst y = 2;"
        modified = "// TODO: SECURITY CRITICAL - Test\nconst x = 1;\nconst y = 2;"
        assert SourceMarker.verify_code_preservation(original, modified) is True
    
    def test_verify_code_preservation_fails_on_modification(self):
        """Test that modified code fails verification."""
        original = "line1\nline2\nline3"
        modified = "line1\nmodified_line2\nline3"
        assert SourceMarker.verify_code_preservation(original, modified) is False
    
    def test_verify_code_preservation_fails_on_deletion(self):
        """Test that deleted code fails verification."""
        original = "line1\nline2\nline3"
        modified = "line1\nline3"
        assert SourceMarker.verify_code_preservation(original, modified) is False
    
    def test_is_comment_line_python(self):
        """Test detecting Python security comments."""
        assert SourceMarker.is_comment_line("# TODO: SECURITY CRITICAL - Test") is True
        assert SourceMarker.is_comment_line("    # TODO: SECURITY CRITICAL - Test") is True
        assert SourceMarker.is_comment_line("# Regular comment") is False
    
    def test_is_comment_line_javascript(self):
        """Test detecting JavaScript security comments."""
        assert SourceMarker.is_comment_line("// TODO: SECURITY CRITICAL - Test") is True
        assert SourceMarker.is_comment_line("  // TODO: SECURITY CRITICAL - Test") is True
        assert SourceMarker.is_comment_line("// Regular comment") is False
    
    def test_mark_file_preserves_code(self):
        """Test that marking a file preserves all original code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            original_content = '''def my_function():
    api_key = "AKIAIOSFODNN7EXAMPLE"
    return api_key

def another_function():
    return "hello"
'''
            test_file.write_text(original_content)
            
            finding = SecretFinding(
                file_path=str(test_file),
                line_number=2,
                category=SecretCategory.AWS_CREDENTIALS,
                pattern_name="aws_access_key",
                redacted_value="AKIA...MPLE",
                context_line='    api_key = "AKIA...MPLE"',
                severity="critical"
            )
            
            self.marker.mark_file(test_file, [finding])
            
            modified_content = test_file.read_text()
            
            # Verify code preservation
            assert SourceMarker.verify_code_preservation(original_content, modified_content)
            
            # Verify the comment was added
            assert "# TODO: SECURITY CRITICAL" in modified_content
    
    def test_mark_file_multiple_findings_preserves_code(self):
        """Test that marking multiple findings preserves all original code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            original_content = '''key1 = "AKIAIOSFODNN7EXAMPLE1"
key2 = "AKIAIOSFODNN7EXAMPLE2"
key3 = "AKIAIOSFODNN7EXAMPLE3"
'''
            test_file.write_text(original_content)
            
            findings = [
                SecretFinding(
                    file_path=str(test_file),
                    line_number=1,
                    category=SecretCategory.AWS_CREDENTIALS,
                    pattern_name="aws_access_key",
                    redacted_value="AKIA...LE1",
                    context_line='key1 = "AKIA...LE1"',
                    severity="critical"
                ),
                SecretFinding(
                    file_path=str(test_file),
                    line_number=2,
                    category=SecretCategory.AWS_CREDENTIALS,
                    pattern_name="aws_access_key",
                    redacted_value="AKIA...LE2",
                    context_line='key2 = "AKIA...LE2"',
                    severity="critical"
                ),
                SecretFinding(
                    file_path=str(test_file),
                    line_number=3,
                    category=SecretCategory.AWS_CREDENTIALS,
                    pattern_name="aws_access_key",
                    redacted_value="AKIA...LE3",
                    context_line='key3 = "AKIA...LE3"',
                    severity="critical"
                ),
            ]
            
            self.marker.mark_file(test_file, findings)
            
            modified_content = test_file.read_text()
            
            # Verify code preservation
            assert SourceMarker.verify_code_preservation(original_content, modified_content)
            
            # Verify all comments were added
            assert modified_content.count("# TODO: SECURITY CRITICAL") == 3



class TestMarkingLog:
    """Tests for the marking log functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.marker = SourceMarker()
    
    def test_marking_log_format(self):
        """Test that the marking log has the correct format."""
        self.marker._marked_locations = [
            MarkedLocation(
                file_path="src/module/file.py",
                line_number=10,
                comment="# TODO: SECURITY CRITICAL - Hardcoded api_key detected",
                finding_type="secret",
                severity="critical"
            ),
            MarkedLocation(
                file_path="src/module/file.py",
                line_number=25,
                comment="# TODO: SECURITY CRITICAL - Hardcoded password detected",
                finding_type="secret",
                severity="critical"
            ),
        ]
        
        log = self.marker.get_marking_log()
        
        # Check structure
        assert "## Marked Source Files" in log
        assert "src/module/file.py" in log
        assert "Line 10" in log
        assert "Line 25" in log
    
    def test_marking_log_multiple_files(self):
        """Test marking log with multiple files."""
        self.marker._marked_locations = [
            MarkedLocation("file1.py", 1, "comment1", "secret", "critical"),
            MarkedLocation("file2.py", 5, "comment2", "secret", "critical"),
            MarkedLocation("file1.py", 10, "comment3", "secret", "critical"),
        ]
        
        log = self.marker.get_marking_log()
        
        assert "file1.py" in log
        assert "file2.py" in log
        assert "Line 1" in log
        assert "Line 5" in log
        assert "Line 10" in log
    
    def test_marking_log_sorted_by_line_number(self):
        """Test that locations within a file are sorted by line number."""
        self.marker._marked_locations = [
            MarkedLocation("file.py", 30, "comment3", "secret", "critical"),
            MarkedLocation("file.py", 10, "comment1", "secret", "critical"),
            MarkedLocation("file.py", 20, "comment2", "secret", "critical"),
        ]
        
        log = self.marker.get_marking_log()
        
        # Find positions of line numbers in the log
        pos_10 = log.find("Line 10")
        pos_20 = log.find("Line 20")
        pos_30 = log.find("Line 30")
        
        # Verify they appear in order
        assert pos_10 < pos_20 < pos_30
    
    def test_clear_marked_locations(self):
        """Test clearing marked locations."""
        self.marker._marked_locations = [
            MarkedLocation("file.py", 1, "comment", "secret", "critical"),
        ]
        
        self.marker.clear_marked_locations()
        
        assert len(self.marker.get_marked_locations()) == 0
        assert "No files were marked" in self.marker.get_marking_log()
    
    def test_marking_log_integration(self):
        """Test marking log after actually marking a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text('api_key = "AKIAIOSFODNN7EXAMPLE"\n')
            
            finding = SecretFinding(
                file_path=str(test_file),
                line_number=1,
                category=SecretCategory.AWS_CREDENTIALS,
                pattern_name="aws_access_key",
                redacted_value="AKIA...MPLE",
                context_line='api_key = "AKIA...MPLE"',
                severity="critical"
            )
            
            self.marker.mark_file(test_file, [finding])
            
            log = self.marker.get_marking_log()
            
            # Verify the log contains the marked file
            assert str(test_file) in log or "test.py" in log
            assert "Line 1" in log
            assert "SECURITY CRITICAL" in log
