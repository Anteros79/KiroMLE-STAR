# Implementation Plan: Security Audit & Hardening

## Overview

This implementation plan breaks down the security audit and hardening feature into discrete coding tasks. The implementation follows a bottom-up approach: first building the core detection components, then the analysis modules, and finally the report generation and source marking capabilities. Property-based tests are included to validate correctness properties.

## Tasks

- [x] 1. Set up project structure and core data models
  - Create `src/mle_star/security/` directory structure
  - Define core data models (SecretFinding, VulnerableDependency, EndpointFinding)
  - Define enums (SecretCategory, OWASPCategory)
  - Define ScanConfig and ScanResult dataclasses
  - _Requirements: 1.1, 2.1, 3.1, 4.1_

- [x] 2. Implement Secret Detector
  - [x] 2.1 Implement regex patterns for secret detection
    - Define patterns for AWS keys, API keys, passwords, tokens, private keys, connection strings
    - Implement pattern compilation and matching logic
    - _Requirements: 1.2_
  - [x] 2.2 Implement file scanning logic
    - Implement file extension filtering (.py, .ts, .tsx, .js, .jsx, .json, .yaml, .yml, .env)
    - Implement directory traversal with exclusion support
    - _Requirements: 1.1_
  - [x] 2.3 Implement secret redaction
    - Implement redact_value() function (first 4 + "..." + last 4 chars)
    - Ensure full secret never appears in output
    - _Requirements: 1.3, 1.4_
  - [x] 2.4 Implement category summary generation
    - Aggregate findings by SecretCategory
    - Generate summary counts
    - _Requirements: 1.5_
  - [ ]* 2.5 Write property test for secret detection
    - **Property 2: Secret Pattern Detection**
    - **Validates: Requirements 1.2**
  - [ ]* 2.6 Write property test for secret redaction
    - **Property 3: Secret Redaction Correctness**
    - **Validates: Requirements 1.3, 1.4**

- [x] 3. Implement Dependency Analyzer
  - [x] 3.1 Implement requirements.txt parser
    - Parse package names and version specifiers
    - Handle various version formats (==, >=, ~=, etc.)
    - _Requirements: 2.1_
  - [x] 3.2 Implement package.json parser
    - Parse dependencies and devDependencies
    - Extract package names and versions
    - _Requirements: 2.1_
  - [x] 3.3 Implement vulnerability checking
    - Integrate with pip-audit for Python packages
    - Implement severity categorization (Critical, High, Medium, Low)
    - Handle missing dependency files gracefully
    - _Requirements: 2.2, 2.3, 2.4, 2.5_
  - [ ]* 3.4 Write property test for dependency parsing
    - **Property 5: Dependency Parsing Round-Trip**
    - **Validates: Requirements 2.1, 2.3, 2.4**

- [x] 4. Checkpoint - Core detection components
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement API Auditor
  - [x] 5.1 Implement endpoint detection
    - Detect FastAPI route decorators (@app.get, @app.post, etc.)
    - Extract HTTP method and path from decorators
    - _Requirements: 3.1, 3.2_
  - [x] 5.2 Implement authorization check detection
    - Detect Depends() with auth functions
    - Detect @requires_auth, @login_required decorators
    - Flag endpoints without auth as A01:Broken Access Control
    - _Requirements: 3.3, 3.5_
  - [x] 5.3 Implement input validation check
    - Detect Pydantic models, Field(), Query(), Path(), Body()
    - Flag unvalidated inputs as potential injection risks
    - _Requirements: 3.4, 3.5_
  - [x] 5.4 Implement endpoint analysis aggregation
    - Produce list of endpoints with security status
    - Map findings to OWASP categories
    - _Requirements: 3.6_
  - [ ]* 5.5 Write property test for endpoint detection
    - **Property 6: Endpoint Detection Completeness**
    - **Validates: Requirements 3.2, 3.6**
  - [ ]* 5.6 Write property test for authorization check
    - **Property 7: Authorization Check Detection**
    - **Validates: Requirements 3.3, 3.5**

- [x] 6. Implement Report Generator
  - [x] 6.1 Implement executive summary generation
    - Calculate overall risk assessment
    - Generate key statistics (total findings, by severity)
    - _Requirements: 4.2_
  - [x] 6.2 Implement critical findings table
    - Generate Markdown table with columns: ID, Category, Severity, Location, Description, Remediation Status
    - Sort by severity (Critical first)
    - _Requirements: 4.3_
  - [x] 6.3 Implement remediation plan generation
    - Generate prioritized action items
    - Include recommended fixes for each finding type
    - _Requirements: 4.4_
  - [x] 6.4 Implement report assembly
    - Combine all sections into SECURITY_AUDIT.md
    - Add timestamp
    - Ensure proper Markdown formatting
    - _Requirements: 4.1, 4.5, 4.6_
  - [ ]* 6.5 Write property test for report structure
    - **Property 8: Report Structure Completeness**
    - **Validates: Requirements 4.2, 4.3, 4.4, 4.5, 4.6**

- [x] 7. Checkpoint - Analysis and reporting
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Source Marker
  - [x] 8.1 Implement comment insertion logic
    - Insert comments above lines with critical findings
    - Use correct format based on file type (# for Python, // for JS/TS)
    - _Requirements: 5.1, 5.2, 5.3_
  - [x] 8.2 Implement code preservation safeguards
    - Ensure only comment lines are added
    - Preserve original code exactly
    - Skip files in tests/ directory
    - _Requirements: 5.4, 5.5, 6.1, 6.2, 6.3_
  - [x] 8.3 Implement marking log
    - Log all marked locations for inclusion in report
    - _Requirements: 5.6_
  - [ ]* 8.4 Write property test for code preservation
    - **Property 9: Code Preservation Invariant**
    - **Validates: Requirements 5.4, 5.5, 6.1, 6.2, 6.3**
  - [ ]* 8.5 Write property test for comment format
    - **Property 10: Comment Format Correctness**
    - **Validates: Requirements 5.2, 5.3**

- [x] 9. Implement Security Scanner orchestrator
  - [x] 9.1 Implement main scanner class
    - Coordinate Secret Detector, Dependency Analyzer, API Auditor
    - Manage scan configuration
    - _Requirements: 1.1, 2.1, 3.1_
  - [x] 9.2 Implement scan execution flow
    - Run all analysis phases
    - Collect and aggregate findings
    - Trigger report generation and source marking
    - _Requirements: 4.1, 5.1_
  - [x] 9.3 Implement CLI interface
    - Add command-line entry point for running audit
    - Support configuration options (--skip-marking, --output-path, etc.)
    - _Requirements: 1.1, 4.1_

- [x] 10. Run security audit on MLE-STAR codebase
  - [x] 10.1 Execute full security scan
    - Run scanner on project root
    - Generate SECURITY_AUDIT.md
    - _Requirements: 4.1_
  - [x] 10.2 Mark critical vulnerabilities
    - Add TODO comments to files with critical findings
    - Verify no business logic altered
    - _Requirements: 5.1, 5.4, 5.5_
  - [x] 10.3 Verify test preservation
    - Run existing test suite
    - Confirm all tests still pass
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 11. Final checkpoint - Complete audit
  - Ensure all tests pass, ask the user if questions arise.
  - Verify SECURITY_AUDIT.md is complete and accurate

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- The implementation must not alter business logic or break existing tests
