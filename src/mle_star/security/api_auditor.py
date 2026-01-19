"""
API Auditor module for analyzing API endpoints for security vulnerabilities.

This module provides functionality to scan Python files for API endpoint definitions
and analyze them for OWASP Top 10 vulnerabilities, including missing authorization
checks and input validation issues.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import EndpointFinding, OWASPCategory


class APIAuditor:
    """Audits API endpoints for security vulnerabilities.
    
    The auditor scans Python files for FastAPI/Flask route decorators and
    analyzes each endpoint for:
    - Missing authorization checks (A01: Broken Access Control)
    - Missing input validation (A03: Injection)
    
    Attributes:
        ROUTE_PATTERNS: Regex patterns for detecting route decorators
        AUTH_PATTERNS: Patterns indicating authorization is present
        VALIDATION_PATTERNS: Patterns indicating input validation is present
    """
    
    # Patterns for detecting FastAPI/Flask endpoints
    ROUTE_PATTERNS: Dict[str, str] = {
        "fastapi_app_decorator": r'@app\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']',
        "fastapi_router_decorator": r'@router\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']',
        "flask_route": r'@(?:app|blueprint|bp)\s*\.route\s*\(\s*["\']([^"\']+)["\'](?:.*?methods\s*=\s*\[([^\]]+)\])?',
    }
    
    # Auth-related patterns that indicate authorization is present
    AUTH_PATTERNS: List[str] = [
        r'Depends\s*\(\s*(?:get_current_user|verify_token|auth|authenticate|get_user|require_auth|check_auth)',
        r'@requires_auth',
        r'@login_required',
        r'@authenticated',
        r'@jwt_required',
        r'@token_required',
        r'Authorization\s*:',
        r'current_user\s*:',
        r'user\s*:\s*User\s*=\s*Depends',
        r'Security\s*\(',
        r'HTTPBearer',
        r'OAuth2PasswordBearer',
        r'APIKeyHeader',
    ]
    
    # Input validation patterns
    VALIDATION_PATTERNS: List[str] = [
        r'Annotated\s*\[.*?,\s*(?:Query|Path|Body|Header|Cookie|Form)\s*\(',
        r'=\s*(?:Query|Path|Body|Header|Cookie|Form)\s*\(',  # Query(...), Path(...), etc.
        r'pydantic',
        r'BaseModel',
        r'validator\s*\(',
        r'@validator',
        r'@field_validator',
        r'Field\s*\(',
        r'constr\s*\(',
        r'conint\s*\(',
        r'confloat\s*\(',
        r'EmailStr',
        r'HttpUrl',
        r':\s*\w+Model\b',  # Type hints ending in Model (e.g., UserModel)
    ]
    
    def __init__(self):
        """Initialize the APIAuditor with compiled regex patterns."""
        self._compiled_route_patterns: Dict[str, re.Pattern] = {}
        self._compiled_auth_patterns: List[re.Pattern] = []
        self._compiled_validation_patterns: List[re.Pattern] = []
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile all regex patterns for efficient matching."""
        # Compile route patterns
        for name, pattern in self.ROUTE_PATTERNS.items():
            try:
                self._compiled_route_patterns[name] = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                print(f"Warning: Failed to compile route pattern '{name}': {e}")
        
        # Compile auth patterns
        for pattern in self.AUTH_PATTERNS:
            try:
                self._compiled_auth_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                print(f"Warning: Failed to compile auth pattern: {e}")
        
        # Compile validation patterns
        for pattern in self.VALIDATION_PATTERNS:
            try:
                self._compiled_validation_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                print(f"Warning: Failed to compile validation pattern: {e}")

    def detect_endpoints(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Detect API endpoints in a Python file.
        
        Args:
            file_path: Path to the Python file to scan
            
        Returns:
            List of tuples containing (line_number, http_method, endpoint_path)
        """
        endpoints = []
        
        if not file_path.suffix == '.py':
            return endpoints
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError, OSError):
            return endpoints
        
        lines = content.splitlines()
        
        for line_number, line in enumerate(lines, start=1):
            # Check FastAPI app/router decorators
            for pattern_name in ['fastapi_app_decorator', 'fastapi_router_decorator']:
                pattern = self._compiled_route_patterns.get(pattern_name)
                if pattern:
                    match = pattern.search(line)
                    if match:
                        http_method = match.group(1).upper()
                        endpoint_path = match.group(2)
                        endpoints.append((line_number, http_method, endpoint_path))
            
            # Check Flask route decorator
            flask_pattern = self._compiled_route_patterns.get('flask_route')
            if flask_pattern:
                match = flask_pattern.search(line)
                if match:
                    endpoint_path = match.group(1)
                    methods_str = match.group(2) if match.lastindex >= 2 and match.group(2) else None
                    
                    if methods_str:
                        # Parse methods from the list
                        methods = re.findall(r'["\'](\w+)["\']', methods_str)
                        for method in methods:
                            endpoints.append((line_number, method.upper(), endpoint_path))
                    else:
                        # Default to GET for Flask routes without explicit methods
                        endpoints.append((line_number, 'GET', endpoint_path))
        
        return endpoints
    
    def _get_function_context(self, lines: List[str], decorator_line: int, context_lines: int = 30) -> str:
        """Get the function context around a decorator line.
        
        This extracts the decorator and the function body to analyze for
        auth and validation patterns.
        
        Args:
            lines: All lines of the file
            decorator_line: Line number of the decorator (1-indexed)
            context_lines: Number of lines to include after the decorator
            
        Returns:
            String containing the function context
        """
        start_idx = max(0, decorator_line - 1)  # Convert to 0-indexed
        end_idx = min(len(lines), decorator_line + context_lines)
        
        context = []
        in_function = False
        indent_level = None
        
        for i in range(start_idx, end_idx):
            line = lines[i]
            context.append(line)
            
            # Detect function definition
            if not in_function and re.match(r'\s*(async\s+)?def\s+\w+', line):
                in_function = True
                # Get the indentation level of the function
                indent_match = re.match(r'^(\s*)', line)
                if indent_match:
                    indent_level = len(indent_match.group(1))
            
            # If we're in a function and hit a line with less or equal indentation
            # (that's not empty or a comment), we've exited the function
            elif in_function and indent_level is not None:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= indent_level and not line.strip().startswith('@'):
                        break
        
        return '\n'.join(context)

    def check_auth(self, context: str) -> bool:
        """Check if authorization patterns are present in the function context.
        
        Args:
            context: The function context string to analyze
            
        Returns:
            True if authorization patterns are found, False otherwise
        """
        for pattern in self._compiled_auth_patterns:
            if pattern.search(context):
                return True
        return False
    
    def _create_auth_finding(
        self, 
        file_path: str, 
        line_number: int, 
        endpoint_path: str, 
        http_method: str
    ) -> EndpointFinding:
        """Create an EndpointFinding for missing authorization.
        
        Args:
            file_path: Path to the file
            line_number: Line number of the endpoint
            endpoint_path: URL path of the endpoint
            http_method: HTTP method
            
        Returns:
            EndpointFinding for the missing authorization issue
        """
        # Determine severity based on HTTP method
        # Mutating methods (POST, PUT, DELETE, PATCH) are more critical
        if http_method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            severity = 'high'
        else:
            severity = 'medium'
        
        return EndpointFinding(
            file_path=file_path,
            line_number=line_number,
            endpoint_path=endpoint_path,
            http_method=http_method,
            vulnerability="Missing Authorization Check",
            owasp_category=OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
            severity=severity,
            description=f"Endpoint {http_method} {endpoint_path} does not appear to have "
                       f"authorization checks. This could allow unauthorized access to "
                       f"protected resources.",
            recommendation="Add authorization using Depends(get_current_user), "
                          "@requires_auth decorator, or similar authentication mechanism."
        )

    def check_input_validation(self, context: str) -> bool:
        """Check if input validation patterns are present in the function context.
        
        Args:
            context: The function context string to analyze
            
        Returns:
            True if input validation patterns are found, False otherwise
        """
        for pattern in self._compiled_validation_patterns:
            if pattern.search(context):
                return True
        return False
    
    def _has_parameters(self, context: str) -> bool:
        """Check if the endpoint function has parameters that need validation.
        
        Args:
            context: The function context string to analyze
            
        Returns:
            True if the function has parameters beyond self/request
        """
        # Look for function definition with parameters
        func_match = re.search(r'def\s+\w+\s*\(([^)]*)\)', context)
        if not func_match:
            return False
        
        params = func_match.group(1)
        
        # Remove common non-user-input parameters
        params = re.sub(r'\bself\b', '', params)
        params = re.sub(r'\brequest\s*:', '', params)
        params = re.sub(r'\bbackground_tasks\s*:', '', params, flags=re.IGNORECASE)
        params = re.sub(r'\bdb\s*:', '', params)
        params = re.sub(r'\bsession\s*:', '', params)
        
        # Check if there are remaining parameters
        params = params.strip().strip(',')
        return bool(params)
    
    def _create_validation_finding(
        self, 
        file_path: str, 
        line_number: int, 
        endpoint_path: str, 
        http_method: str
    ) -> EndpointFinding:
        """Create an EndpointFinding for missing input validation.
        
        Args:
            file_path: Path to the file
            line_number: Line number of the endpoint
            endpoint_path: URL path of the endpoint
            http_method: HTTP method
            
        Returns:
            EndpointFinding for the missing input validation issue
        """
        # POST/PUT/PATCH typically handle more user input
        if http_method in ['POST', 'PUT', 'PATCH']:
            severity = 'medium'
        else:
            severity = 'low'
        
        return EndpointFinding(
            file_path=file_path,
            line_number=line_number,
            endpoint_path=endpoint_path,
            http_method=http_method,
            vulnerability="Missing Input Validation",
            owasp_category=OWASPCategory.A03_INJECTION,
            severity=severity,
            description=f"Endpoint {http_method} {endpoint_path} may have unvalidated "
                       f"input parameters. This could lead to injection vulnerabilities.",
            recommendation="Use Pydantic models, Field() validators, or Query/Path/Body "
                          "with validation constraints to validate all user inputs."
        )

    def scan_file(self, file_path: Path) -> List[EndpointFinding]:
        """Scan a single Python file for API endpoint security issues.
        
        Args:
            file_path: Path to the Python file to scan
            
        Returns:
            List of EndpointFinding objects for any security issues found
        """
        findings = []
        
        if not file_path.suffix == '.py':
            return findings
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError, OSError):
            return findings
        
        lines = content.splitlines()
        endpoints = self.detect_endpoints(file_path)
        
        for line_number, http_method, endpoint_path in endpoints:
            # Get the function context for analysis
            context = self._get_function_context(lines, line_number)
            
            # Check for authorization
            has_auth = self.check_auth(context)
            if not has_auth:
                finding = self._create_auth_finding(
                    str(file_path), line_number, endpoint_path, http_method
                )
                findings.append(finding)
            
            # Check for input validation (only if endpoint has parameters)
            has_validation = self.check_input_validation(context)
            has_params = self._has_parameters(context)
            
            if has_params and not has_validation:
                finding = self._create_validation_finding(
                    str(file_path), line_number, endpoint_path, http_method
                )
                findings.append(finding)
        
        return findings
    
    def analyze_directory(
        self, 
        directory: Path, 
        exclude_dirs: Optional[set] = None
    ) -> List[EndpointFinding]:
        """Analyze a directory recursively for API endpoint security issues.
        
        Args:
            directory: Root directory to scan
            exclude_dirs: Set of directory names to exclude from scanning
            
        Returns:
            List of EndpointFinding objects for all security issues found
        """
        if exclude_dirs is None:
            exclude_dirs = {".git", ".venv", "node_modules", "__pycache__", ".next", ".hypothesis", "tests"}
        
        findings = []
        
        if not directory.exists() or not directory.is_dir():
            return findings
        
        for item in directory.iterdir():
            if item.is_dir():
                # Skip excluded directories
                if item.name in exclude_dirs:
                    continue
                # Recursively scan subdirectories
                findings.extend(self.analyze_directory(item, exclude_dirs))
            elif item.is_file() and item.suffix == '.py':
                # Scan Python files
                findings.extend(self.scan_file(item))
        
        return findings
    
    def analyze_api_directories(
        self, 
        project_root: Path, 
        api_directories: Optional[List[str]] = None
    ) -> List[EndpointFinding]:
        """Analyze specific API directories for security issues.
        
        Args:
            project_root: Root directory of the project
            api_directories: List of relative paths to API directories
            
        Returns:
            List of EndpointFinding objects for all security issues found
        """
        if api_directories is None:
            api_directories = ["src/mle_star/api", "routes", "api"]
        
        findings = []
        
        for api_dir in api_directories:
            dir_path = project_root / api_dir
            if dir_path.exists() and dir_path.is_dir():
                findings.extend(self.analyze_directory(dir_path))
        
        return findings
    
    def generate_summary(self, findings: List[EndpointFinding]) -> Dict[str, any]:
        """Generate a summary of API security findings.
        
        Args:
            findings: List of EndpointFinding objects
            
        Returns:
            Dictionary containing summary statistics
        """
        summary = {
            "total_findings": len(findings),
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_owasp_category": {},
            "by_vulnerability_type": {},
            "endpoints_analyzed": set(),
        }
        
        for finding in findings:
            # Count by severity
            severity = finding.severity.lower()
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1
            
            # Count by OWASP category
            category = finding.owasp_category.value
            summary["by_owasp_category"][category] = \
                summary["by_owasp_category"].get(category, 0) + 1
            
            # Count by vulnerability type
            vuln_type = finding.vulnerability
            summary["by_vulnerability_type"][vuln_type] = \
                summary["by_vulnerability_type"].get(vuln_type, 0) + 1
            
            # Track unique endpoints
            endpoint_key = f"{finding.http_method} {finding.endpoint_path}"
            summary["endpoints_analyzed"].add(endpoint_key)
        
        # Convert set to count
        summary["unique_endpoints"] = len(summary["endpoints_analyzed"])
        del summary["endpoints_analyzed"]
        
        return summary
