# Security Audit Report

**Generated:** 2026-01-05T23:53:36.682794

---

## Executive Summary

**Overall Risk Assessment: CRITICAL**

### Key Statistics

- **Total Findings:** 41
- **Critical:** 13
- **High:** 14
- **Medium:** 9
- **Low:** 5

### Findings Breakdown

- **Hardcoded Secrets:** 21
- **Vulnerable Dependencies:** 0
- **API Security Issues:** 20

### Risk Assessment Details

⚠️ **CRITICAL RISK**: Immediate action required. Critical vulnerabilities have been identified that could lead to data breaches, unauthorized access, or system compromise. Address critical findings before deployment.

## Critical Findings

| ID | Category | Severity | Location | Description | Remediation Status |
|:---|:---------|:---------|:---------|:------------|:-------------------|
| F001 | Secret: password | CRITICAL | C:\DevProjects\KiroMLE-STAR\src\mle_star\security\models.py:19 | Hardcoded password_assignment: pass...word | Open |
| F002 | Secret: password | CRITICAL | C:\DevProjects\KiroMLE-STAR\src\mle_star\security\report_generator.py:290 | Hardcoded password_assignment: Use ...ords | Open |
| F003 | Secret: api_key | CRITICAL | C:\DevProjects\KiroMLE-STAR\tests\unit\test_security_scanner.py:79 | Hardcoded openai_key: sk-1...cdef | Open |
| F004 | Secret: api_key | CRITICAL | C:\DevProjects\KiroMLE-STAR\tests\unit\test_security_scanner.py:106 | Hardcoded openai_key: sk-1...cdef | Open |
| F005 | Secret: aws_credentials | CRITICAL | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:115 | Hardcoded aws_access_key: AKIA...MPLE | Open |
| F006 | Secret: aws_credentials | CRITICAL | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:139 | Hardcoded aws_access_key: AKIA...MPLE | Open |
| F007 | Secret: aws_credentials | CRITICAL | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:169 | Hardcoded aws_access_key: AKIA...MPLE | Open |
| F008 | Secret: aws_credentials | CRITICAL | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:190 | Hardcoded aws_access_key: AKIA...MPLE | Open |
| F009 | Secret: aws_credentials | CRITICAL | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:304 | Hardcoded aws_access_key: AKIA...MPLE | Open |
| F010 | Secret: aws_credentials | CRITICAL | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:336 | Hardcoded aws_access_key: AKIA...MPLE | Open |
| F011 | Secret: aws_credentials | CRITICAL | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:337 | Hardcoded aws_access_key: AKIA...MPLE | Open |
| F012 | Secret: aws_credentials | CRITICAL | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:338 | Hardcoded aws_access_key: AKIA...MPLE | Open |
| F013 | Secret: aws_credentials | CRITICAL | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:467 | Hardcoded aws_access_key: AKIA...MPLE | Open |
| F014 | Secret: api_key | HIGH | C:\DevProjects\KiroMLE-STAR\tests\unit\test_security_scanner.py:79 | Hardcoded generic_api_key: sk-1...ef12 | Open |
| F015 | Secret: api_key | HIGH | C:\DevProjects\KiroMLE-STAR\tests\unit\test_security_scanner.py:106 | Hardcoded generic_api_key: sk-1...ef12 | Open |
| F016 | Secret: api_key | HIGH | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:115 | Hardcoded generic_api_key: AKIA...MPLE | Open |
| F017 | Secret: api_key | HIGH | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:139 | Hardcoded generic_api_key: AKIA...MPLE | Open |
| F018 | Secret: api_key | HIGH | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:169 | Hardcoded generic_api_key: AKIA...MPLE | Open |
| F019 | Secret: api_key | HIGH | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:190 | Hardcoded generic_api_key: AKIA...MPLE | Open |
| F020 | Secret: api_key | HIGH | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:304 | Hardcoded generic_api_key: AKIA...MPLE | Open |
| F021 | Secret: api_key | HIGH | C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:467 | Hardcoded generic_api_key: AKIA...MPLE | Open |
| F022 | API: A01:2021-Broken Access Control | HIGH | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:163 | Endpoint POST /api/pipeline/start does not appear to have authorization checks. ... | Open |
| F023 | API: A01:2021-Broken Access Control | HIGH | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:223 | Endpoint POST /api/pipeline/pause/{run_id} does not appear to have authorization... | Open |
| F024 | API: A01:2021-Broken Access Control | HIGH | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:249 | Endpoint POST /api/pipeline/resume/{run_id} does not appear to have authorizatio... | Open |
| F025 | API: A01:2021-Broken Access Control | HIGH | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:275 | Endpoint POST /api/pipeline/stop/{run_id} does not appear to have authorization ... | Open |
| F026 | API: A01:2021-Broken Access Control | HIGH | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:344 | Endpoint POST /api/datasets/upload does not appear to have authorization checks.... | Open |
| F027 | API: A01:2021-Broken Access Control | HIGH | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:429 | Endpoint DELETE /api/datasets/{filename} does not appear to have authorization c... | Open |
| F028 | API: A01:2021-Broken Access Control | MEDIUM | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:157 | Endpoint GET /health does not appear to have authorization checks. This could al... | Open |
| F029 | API: A03:2021-Injection | MEDIUM | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:163 | Endpoint POST /api/pipeline/start may have unvalidated input parameters. This co... | Open |
| F030 | API: A01:2021-Broken Access Control | MEDIUM | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:210 | Endpoint GET /api/pipeline/status does not appear to have authorization checks. ... | Open |
| F031 | API: A03:2021-Injection | MEDIUM | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:223 | Endpoint POST /api/pipeline/pause/{run_id} may have unvalidated input parameters... | Open |
| F032 | API: A03:2021-Injection | MEDIUM | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:249 | Endpoint POST /api/pipeline/resume/{run_id} may have unvalidated input parameter... | Open |
| F033 | API: A03:2021-Injection | MEDIUM | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:275 | Endpoint POST /api/pipeline/stop/{run_id} may have unvalidated input parameters.... | Open |
| F034 | API: A01:2021-Broken Access Control | MEDIUM | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:300 | Endpoint GET /api/submission/download/{run_id} does not appear to have authoriza... | Open |
| F035 | API: A01:2021-Broken Access Control | MEDIUM | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:320 | Endpoint GET /api/runs does not appear to have authorization checks. This could ... | Open |
| F036 | API: A01:2021-Broken Access Control | MEDIUM | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:407 | Endpoint GET /api/datasets/list does not appear to have authorization checks. Th... | Open |
| F037 | API: A03:2021-Injection | LOW | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:210 | Endpoint GET /api/pipeline/status may have unvalidated input parameters. This co... | Open |
| F038 | API: A03:2021-Injection | LOW | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:300 | Endpoint GET /api/submission/download/{run_id} may have unvalidated input parame... | Open |
| F039 | API: A03:2021-Injection | LOW | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:320 | Endpoint GET /api/runs may have unvalidated input parameters. This could lead to... | Open |
| F040 | API: A03:2021-Injection | LOW | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:407 | Endpoint GET /api/datasets/list may have unvalidated input parameters. This coul... | Open |
| F041 | API: A03:2021-Injection | LOW | C:\DevProjects\KiroMLE-STAR\src\mle_star\api\server.py:429 | Endpoint DELETE /api/datasets/{filename} may have unvalidated input parameters. ... | Open |

## Remediation Plan

### Priority 1: Critical Issues (Immediate Action Required)

- [ ] **C:\DevProjects\KiroMLE-STAR\src\mle_star\security\models.py:19** - Use environment variables or a secure vault for passwords
- [ ] **C:\DevProjects\KiroMLE-STAR\src\mle_star\security\report_generator.py:290** - Use environment variables or a secure vault for passwords
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_security_scanner.py:79** - Move API key to environment variable or secrets manager
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_security_scanner.py:106** - Move API key to environment variable or secrets manager
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:115** - Use IAM roles or AWS Secrets Manager instead
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:139** - Use IAM roles or AWS Secrets Manager instead
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:169** - Use IAM roles or AWS Secrets Manager instead
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:190** - Use IAM roles or AWS Secrets Manager instead
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:304** - Use IAM roles or AWS Secrets Manager instead
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:336** - Use IAM roles or AWS Secrets Manager instead
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:337** - Use IAM roles or AWS Secrets Manager instead
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:338** - Use IAM roles or AWS Secrets Manager instead
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:467** - Use IAM roles or AWS Secrets Manager instead

### Priority 2: High Severity Issues

- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_security_scanner.py:79** - Move API key to environment variable or secrets manager
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_security_scanner.py:106** - Move API key to environment variable or secrets manager
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:115** - Move API key to environment variable or secrets manager
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:139** - Move API key to environment variable or secrets manager
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:169** - Move API key to environment variable or secrets manager
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:190** - Move API key to environment variable or secrets manager
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:304** - Move API key to environment variable or secrets manager
- [ ] **C:\DevProjects\KiroMLE-STAR\tests\unit\test_source_marker.py:467** - Move API key to environment variable or secrets manager
- [ ] **/api/pipeline/start** (POST) - Add authentication/authorization checks
- [ ] **/api/pipeline/pause/{run_id}** (POST) - Add authentication/authorization checks
- [ ] **/api/pipeline/resume/{run_id}** (POST) - Add authentication/authorization checks
- [ ] **/api/pipeline/stop/{run_id}** (POST) - Add authentication/authorization checks
- [ ] **/api/datasets/upload** (POST) - Add authentication/authorization checks
- [ ] **/api/datasets/{filename}** (DELETE) - Add authentication/authorization checks

### Priority 3: Medium/Low Severity Issues

- [ ] **/health** (GET) - Add authentication/authorization checks
- [ ] **/api/pipeline/start** (POST) - Add input validation and parameterized queries
- [ ] **/api/pipeline/status** (GET) - Add authentication/authorization checks
- [ ] **/api/pipeline/status** (GET) - Add input validation and parameterized queries
- [ ] **/api/pipeline/pause/{run_id}** (POST) - Add input validation and parameterized queries
- [ ] **/api/pipeline/resume/{run_id}** (POST) - Add input validation and parameterized queries
- [ ] **/api/pipeline/stop/{run_id}** (POST) - Add input validation and parameterized queries
- [ ] **/api/submission/download/{run_id}** (GET) - Add authentication/authorization checks
- [ ] **/api/submission/download/{run_id}** (GET) - Add input validation and parameterized queries
- [ ] **/api/runs** (GET) - Add authentication/authorization checks
- [ ] **/api/runs** (GET) - Add input validation and parameterized queries
- [ ] **/api/datasets/list** (GET) - Add authentication/authorization checks
- [ ] **/api/datasets/list** (GET) - Add input validation and parameterized queries
- [ ] **/api/datasets/{filename}** (DELETE) - Add input validation and parameterized queries

---

_This report was automatically generated by the MLE-STAR Security Scanner._
