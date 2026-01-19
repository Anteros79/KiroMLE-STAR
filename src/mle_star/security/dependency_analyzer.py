"""
Dependency Analyzer for the Security Audit & Hardening feature.

This module analyzes project dependencies for known vulnerabilities by:
- Parsing requirements.txt and package.json files
- Cross-referencing dependencies against CVE databases
- Categorizing findings by severity
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import VulnerableDependency

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes dependencies for known vulnerabilities.
    
    This class parses dependency files (requirements.txt, package.json) and
    checks them against vulnerability databases using pip-audit for Python
    packages.
    """
    
    # Regex pattern for parsing requirements.txt lines
    # Handles: package==1.0.0, package>=1.0.0, package~=1.0.0, package[extra]>=1.0.0, etc.
    REQUIREMENTS_PATTERN = re.compile(
        r'^(?P<package>[a-zA-Z0-9][-a-zA-Z0-9._]*)'  # Package name
        r'(?:\[(?P<extras>[^\]]+)\])?'               # Optional extras [extra1,extra2]
        r'(?P<version_spec>(?:[<>=!~]+[^,\s#]+(?:,\s*[<>=!~]+[^,\s#]+)*)?)'  # Version specifier(s)
        r'(?:\s*#.*)?$'                              # Optional inline comment
    )
    
    # Version specifier pattern to extract operator and version
    VERSION_SPEC_PATTERN = re.compile(
        r'(?P<operator>[<>=!~]+)(?P<version>[^,\s]+)'
    )
    
    def __init__(self):
        """Initialize the DependencyAnalyzer."""
        self._pip_audit_available: Optional[bool] = None
    
    def parse_requirements_txt(self, file_path: Path) -> Dict[str, str]:
        """Parse a requirements.txt file to extract dependencies.
        
        Args:
            file_path: Path to the requirements.txt file
            
        Returns:
            Dictionary mapping package names to version specifiers.
            If no version is specified, the value will be an empty string.
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file cannot be parsed
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Requirements file not found: {file_path}")
        
        dependencies: Dict[str, str] = {}
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            logger.warning(f"Could not decode {file_path} as UTF-8, trying latin-1")
            content = file_path.read_text(encoding='latin-1')
        
        for line_num, line in enumerate(content.splitlines(), start=1):
            # Strip whitespace
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Skip -r, -e, --index-url, and other pip options
            if line.startswith('-') or line.startswith('--'):
                continue
            
            # Skip URLs (git+, http://, etc.)
            if '://' in line or line.startswith('git+'):
                continue
            
            # Try to parse the line
            match = self.REQUIREMENTS_PATTERN.match(line)
            if match:
                package = match.group('package').lower()
                version_spec = match.group('version_spec') or ''
                dependencies[package] = version_spec.strip()
            else:
                logger.warning(f"Could not parse line {line_num} in {file_path}: {line}")
        
        return dependencies
    
    def parse_version_specifier(self, version_spec: str) -> List[Tuple[str, str]]:
        """Parse a version specifier string into operator-version pairs.
        
        Args:
            version_spec: Version specifier string (e.g., ">=1.0.0,<2.0.0")
            
        Returns:
            List of (operator, version) tuples
        """
        if not version_spec:
            return []
        
        matches = self.VERSION_SPEC_PATTERN.findall(version_spec)
        return [(op, ver) for op, ver in matches]
    
    def get_pinned_version(self, version_spec: str) -> Optional[str]:
        """Extract a pinned version from a version specifier.
        
        Args:
            version_spec: Version specifier string
            
        Returns:
            The pinned version if using == operator, otherwise None
        """
        specs = self.parse_version_specifier(version_spec)
        for operator, version in specs:
            if operator == '==':
                return version
        return None

    def parse_package_json(self, file_path: Path) -> Dict[str, str]:
        """Parse a package.json file to extract dependencies.
        
        Extracts both dependencies and devDependencies from the package.json file.
        
        Args:
            file_path: Path to the package.json file
            
        Returns:
            Dictionary mapping package names to version specifiers.
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is not valid JSON
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Package.json file not found: {file_path}")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
        except UnicodeDecodeError:
            logger.warning(f"Could not decode {file_path} as UTF-8")
            raise ValueError(f"Could not decode {file_path}")
        
        dependencies: Dict[str, str] = {}
        
        # Extract dependencies
        if 'dependencies' in data and isinstance(data['dependencies'], dict):
            for package, version in data['dependencies'].items():
                if isinstance(version, str):
                    dependencies[package] = version
        
        # Extract devDependencies
        if 'devDependencies' in data and isinstance(data['devDependencies'], dict):
            for package, version in data['devDependencies'].items():
                if isinstance(version, str):
                    # Don't overwrite if already in dependencies
                    if package not in dependencies:
                        dependencies[package] = version
        
        return dependencies
    
    def normalize_npm_version(self, version: str) -> str:
        """Normalize an npm version specifier.
        
        Handles various npm version formats:
        - ^1.0.0 (caret ranges)
        - ~1.0.0 (tilde ranges)
        - 1.0.0 (exact)
        - >=1.0.0 (ranges)
        - * or latest (any version)
        
        Args:
            version: npm version specifier
            
        Returns:
            Normalized version string
        """
        if not version:
            return ''
        
        # Remove leading/trailing whitespace
        version = version.strip()
        
        # Handle special cases
        if version in ('*', 'latest', 'x'):
            return '*'
        
        return version

    def _check_pip_audit_available(self) -> bool:
        """Check if pip-audit is available on the system.
        
        Returns:
            True if pip-audit is available, False otherwise
        """
        if self._pip_audit_available is not None:
            return self._pip_audit_available
        
        try:
            result = subprocess.run(
                ['pip-audit', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self._pip_audit_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._pip_audit_available = False
        
        return self._pip_audit_available
    
    def _map_severity(self, severity_str: str) -> str:
        """Map vulnerability severity strings to standard levels.
        
        Args:
            severity_str: Severity string from vulnerability database
            
        Returns:
            Normalized severity level: "critical", "high", "medium", or "low"
        """
        severity_lower = severity_str.lower().strip()
        
        if severity_lower in ('critical', 'crit'):
            return 'critical'
        elif severity_lower in ('high', 'important'):
            return 'high'
        elif severity_lower in ('medium', 'moderate', 'med'):
            return 'medium'
        elif severity_lower in ('low', 'minor', 'info', 'informational'):
            return 'low'
        else:
            # Default to medium for unknown severities
            return 'medium'
    
    def check_python_vulnerabilities(
        self, 
        dependencies: Dict[str, str],
        requirements_file: Optional[Path] = None
    ) -> List[VulnerableDependency]:
        """Check Python dependencies for known vulnerabilities using pip-audit.
        
        Args:
            dependencies: Dictionary of package names to version specifiers
            requirements_file: Optional path to requirements.txt for pip-audit
            
        Returns:
            List of VulnerableDependency objects for vulnerable packages
        """
        findings: List[VulnerableDependency] = []
        source_file = str(requirements_file) if requirements_file else "requirements.txt"
        
        if not self._check_pip_audit_available():
            logger.warning(
                "pip-audit is not available. Install with: pip install pip-audit. "
                "Skipping Python vulnerability check."
            )
            return findings
        
        try:
            # Run pip-audit with JSON output
            cmd = ['pip-audit', '--format', 'json']
            
            if requirements_file and requirements_file.exists():
                cmd.extend(['--requirement', str(requirements_file)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            # pip-audit returns non-zero if vulnerabilities found
            if result.stdout:
                try:
                    audit_data = json.loads(result.stdout)
                    findings = self._parse_pip_audit_output(audit_data, source_file)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse pip-audit output: {result.stdout[:200]}")
            
            if result.stderr and 'error' in result.stderr.lower():
                logger.warning(f"pip-audit stderr: {result.stderr[:200]}")
                
        except subprocess.TimeoutExpired:
            logger.warning("pip-audit timed out after 120 seconds")
        except Exception as e:
            logger.warning(f"Error running pip-audit: {e}")
        
        return findings
    
    def _parse_pip_audit_output(
        self, 
        audit_data: dict, 
        source_file: str
    ) -> List[VulnerableDependency]:
        """Parse pip-audit JSON output into VulnerableDependency objects.
        
        Args:
            audit_data: Parsed JSON output from pip-audit
            source_file: Source file name for the findings
            
        Returns:
            List of VulnerableDependency objects
        """
        findings: List[VulnerableDependency] = []
        
        # pip-audit output format: {"dependencies": [...], "vulnerabilities": [...]}
        # or list of vulnerability objects directly
        vulnerabilities = []
        
        if isinstance(audit_data, list):
            vulnerabilities = audit_data
        elif isinstance(audit_data, dict):
            vulnerabilities = audit_data.get('dependencies', [])
        
        for item in vulnerabilities:
            if not isinstance(item, dict):
                continue
            
            package_name = item.get('name', '')
            version = item.get('version', '')
            vulns = item.get('vulns', [])
            
            if not vulns:
                continue
            
            for vuln in vulns:
                if not isinstance(vuln, dict):
                    continue
                
                cve_id = vuln.get('id', vuln.get('aliases', ['UNKNOWN'])[0] if vuln.get('aliases') else 'UNKNOWN')
                description = vuln.get('description', 'No description available')
                fix_versions = vuln.get('fix_versions', [])
                fixed_version = fix_versions[0] if fix_versions else None
                
                # Determine severity - pip-audit may not always provide it
                severity = self._map_severity(vuln.get('severity', 'medium'))
                
                findings.append(VulnerableDependency(
                    package_name=package_name,
                    current_version=version,
                    cve_id=cve_id,
                    severity=severity,
                    description=description[:500] if description else 'No description',
                    fixed_version=fixed_version,
                    source_file=source_file
                ))
        
        return findings
    
    def check_npm_vulnerabilities(
        self, 
        dependencies: Dict[str, str],
        package_json_path: Optional[Path] = None
    ) -> List[VulnerableDependency]:
        """Check npm dependencies for known vulnerabilities.
        
        Note: This is a placeholder that logs a warning. Full npm audit
        integration would require npm to be installed and configured.
        
        Args:
            dependencies: Dictionary of package names to version specifiers
            package_json_path: Optional path to package.json
            
        Returns:
            List of VulnerableDependency objects (currently empty)
        """
        source_file = str(package_json_path) if package_json_path else "package.json"
        
        # Log that npm audit is not fully implemented
        logger.info(
            f"npm vulnerability checking for {source_file} is not fully implemented. "
            "Consider running 'npm audit' manually in the frontend directory."
        )
        
        # Return empty list - npm audit integration would go here
        return []
    
    def analyze(self, project_root: Path) -> List[VulnerableDependency]:
        """Analyze all dependencies in a project for vulnerabilities.
        
        Scans for requirements.txt and package.json files and checks
        all found dependencies against vulnerability databases.
        
        Args:
            project_root: Root directory of the project to analyze
            
        Returns:
            List of all VulnerableDependency findings
        """
        all_findings: List[VulnerableDependency] = []
        
        # Find and analyze requirements.txt files
        requirements_files = list(project_root.rglob('requirements*.txt'))
        
        # Also check for requirements.txt in root
        root_requirements = project_root / 'requirements.txt'
        if root_requirements.exists() and root_requirements not in requirements_files:
            requirements_files.insert(0, root_requirements)
        
        python_deps_found = False
        for req_file in requirements_files:
            # Skip files in excluded directories
            if any(part in {'.venv', 'node_modules', '.git', '__pycache__'} 
                   for part in req_file.parts):
                continue
            
            try:
                dependencies = self.parse_requirements_txt(req_file)
                if dependencies:
                    python_deps_found = True
                    logger.info(f"Found {len(dependencies)} Python dependencies in {req_file}")
                    findings = self.check_python_vulnerabilities(dependencies, req_file)
                    all_findings.extend(findings)
            except FileNotFoundError:
                logger.warning(f"Requirements file not found: {req_file}")
            except Exception as e:
                logger.warning(f"Error parsing {req_file}: {e}")
        
        if not python_deps_found:
            logger.warning("No Python dependency files (requirements.txt) found")
        
        # Find and analyze package.json files
        package_json_files = list(project_root.rglob('package.json'))
        
        npm_deps_found = False
        for pkg_file in package_json_files:
            # Skip files in node_modules
            if 'node_modules' in pkg_file.parts:
                continue
            
            try:
                dependencies = self.parse_package_json(pkg_file)
                if dependencies:
                    npm_deps_found = True
                    logger.info(f"Found {len(dependencies)} npm dependencies in {pkg_file}")
                    findings = self.check_npm_vulnerabilities(dependencies, pkg_file)
                    all_findings.extend(findings)
            except FileNotFoundError:
                logger.warning(f"Package.json file not found: {pkg_file}")
            except ValueError as e:
                logger.warning(f"Error parsing {pkg_file}: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error parsing {pkg_file}: {e}")
        
        if not npm_deps_found:
            logger.info("No npm dependency files (package.json) found outside node_modules")
        
        # Sort findings by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_findings.sort(key=lambda f: severity_order.get(f.severity, 4))
        
        return all_findings
    
    def get_summary(self, findings: List[VulnerableDependency]) -> Dict[str, int]:
        """Generate a summary of vulnerability findings by severity.
        
        Args:
            findings: List of VulnerableDependency objects
            
        Returns:
            Dictionary with counts by severity level
        """
        summary = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'total': len(findings)
        }
        
        for finding in findings:
            severity = finding.severity.lower()
            if severity in summary:
                summary[severity] += 1
        
        return summary
