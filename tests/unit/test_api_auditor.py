"""
Unit tests for the API Auditor module.

Tests the endpoint detection, authorization check detection,
input validation check, and endpoint analysis aggregation.
"""

import tempfile
from pathlib import Path

import pytest

from src.mle_star.security.api_auditor import APIAuditor
from src.mle_star.security.models import OWASPCategory


class TestAPIAuditor:
    """Test suite for APIAuditor class."""
    
    @pytest.fixture
    def auditor(self):
        """Create an APIAuditor instance for testing."""
        return APIAuditor()
    
    # Test endpoint detection (5.1)
    
    def test_detect_fastapi_get_endpoint(self, auditor):
        """Test detection of FastAPI GET endpoint."""
        code = '''
@app.get("/users")
async def get_users():
    return []
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            endpoints = auditor.detect_endpoints(Path(f.name))
        
        assert len(endpoints) == 1
        line, method, path = endpoints[0]
        assert method == 'GET'
        assert path == '/users'
    
    def test_detect_fastapi_post_endpoint(self, auditor):
        """Test detection of FastAPI POST endpoint."""
        code = '''
@app.post("/users")
async def create_user(user: UserCreate):
    return user
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            endpoints = auditor.detect_endpoints(Path(f.name))
        
        assert len(endpoints) == 1
        line, method, path = endpoints[0]
        assert method == 'POST'
        assert path == '/users'
    
    def test_detect_fastapi_router_endpoint(self, auditor):
        """Test detection of FastAPI router endpoint."""
        code = '''
@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            endpoints = auditor.detect_endpoints(Path(f.name))
        
        assert len(endpoints) == 1
        line, method, path = endpoints[0]
        assert method == 'DELETE'
        assert path == '/items/{item_id}'
    
    def test_detect_multiple_endpoints(self, auditor):
        """Test detection of multiple endpoints in one file."""
        code = '''
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/data")
async def create_data(data: dict):
    return data

@app.put("/api/data/{id}")
async def update_data(id: int, data: dict):
    return data
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            endpoints = auditor.detect_endpoints(Path(f.name))
        
        assert len(endpoints) == 3
        methods = [e[1] for e in endpoints]
        assert 'GET' in methods
        assert 'POST' in methods
        assert 'PUT' in methods

    # Test authorization check detection (5.2)
    
    def test_check_auth_with_depends(self, auditor):
        """Test auth detection with Depends(get_current_user)."""
        context = '''
@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"user": current_user}
'''
        assert auditor.check_auth(context) is True
    
    def test_check_auth_with_requires_auth_decorator(self, auditor):
        """Test auth detection with @requires_auth decorator."""
        context = '''
@app.get("/admin")
@requires_auth
async def admin_route():
    return {"admin": True}
'''
        assert auditor.check_auth(context) is True
    
    def test_check_auth_with_login_required(self, auditor):
        """Test auth detection with @login_required decorator."""
        context = '''
@app.get("/dashboard")
@login_required
async def dashboard():
    return {"data": []}
'''
        assert auditor.check_auth(context) is True
    
    def test_check_auth_missing(self, auditor):
        """Test auth detection when no auth is present."""
        context = '''
@app.get("/public")
async def public_route():
    return {"public": True}
'''
        assert auditor.check_auth(context) is False
    
    def test_check_auth_with_oauth2(self, auditor):
        """Test auth detection with OAuth2PasswordBearer."""
        context = '''
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/secure")
async def secure_route(token: str = Depends(oauth2_scheme)):
    return {"secure": True}
'''
        assert auditor.check_auth(context) is True
    
    # Test input validation check (5.3)
    
    def test_check_validation_with_pydantic_model(self, auditor):
        """Test validation detection with Pydantic BaseModel."""
        context = '''
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str

@app.post("/users")
async def create_user(user: UserCreate):
    return user
'''
        assert auditor.check_input_validation(context) is True
    
    def test_check_validation_with_field(self, auditor):
        """Test validation detection with Field()."""
        context = '''
@app.post("/items")
async def create_item(
    name: str = Field(..., min_length=1, max_length=100)
):
    return {"name": name}
'''
        assert auditor.check_input_validation(context) is True
    
    def test_check_validation_with_query(self, auditor):
        """Test validation detection with Query()."""
        context = '''
@app.get("/search")
async def search(
    q: str = Query(..., min_length=1)
):
    return {"query": q}
'''
        assert auditor.check_input_validation(context) is True
    
    def test_check_validation_missing(self, auditor):
        """Test validation detection when no validation is present."""
        context = '''
@app.get("/items")
async def get_items(skip: int, limit: int):
    return []
'''
        assert auditor.check_input_validation(context) is False
    
    def test_has_parameters_true(self, auditor):
        """Test parameter detection when parameters exist."""
        context = '''
async def get_items(skip: int, limit: int):
    return []
'''
        assert auditor._has_parameters(context) is True
    
    def test_has_parameters_false_only_self(self, auditor):
        """Test parameter detection with only self."""
        context = '''
def get_items(self):
    return []
'''
        assert auditor._has_parameters(context) is False
    
    # Test endpoint analysis aggregation (5.4)
    
    def test_scan_file_finds_auth_issues(self, auditor):
        """Test that scan_file finds missing auth issues."""
        code = '''
@app.get("/public")
async def public_route():
    return {"public": True}

@app.post("/data")
async def create_data(data: dict):
    return data
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            findings = auditor.scan_file(Path(f.name))
        
        # Should find auth issues for both endpoints
        auth_findings = [f for f in findings if f.vulnerability == "Missing Authorization Check"]
        assert len(auth_findings) >= 2
    
    def test_scan_file_owasp_category_mapping(self, auditor):
        """Test that findings are mapped to correct OWASP categories."""
        code = '''
@app.post("/users")
async def create_user(name: str, email: str):
    return {"name": name}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            findings = auditor.scan_file(Path(f.name))
        
        # Check OWASP categories
        categories = [f.owasp_category for f in findings]
        assert OWASPCategory.A01_BROKEN_ACCESS_CONTROL in categories
    
    def test_generate_summary(self, auditor):
        """Test summary generation from findings."""
        code = '''
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/data")
async def create_data(data: dict):
    return data

@app.delete("/data/{id}")
async def delete_data(id: int):
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            findings = auditor.scan_file(Path(f.name))
        
        summary = auditor.generate_summary(findings)
        
        assert "total_findings" in summary
        assert "by_severity" in summary
        assert "by_owasp_category" in summary
        assert "unique_endpoints" in summary
        assert summary["total_findings"] > 0
    
    def test_severity_based_on_http_method(self, auditor):
        """Test that severity is higher for mutating methods."""
        code = '''
@app.get("/read")
async def read_data():
    return []

@app.post("/write")
async def write_data(data: dict):
    return data
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            findings = auditor.scan_file(Path(f.name))
        
        auth_findings = [f for f in findings if f.vulnerability == "Missing Authorization Check"]
        
        # POST should have higher severity than GET
        get_finding = next((f for f in auth_findings if f.http_method == 'GET'), None)
        post_finding = next((f for f in auth_findings if f.http_method == 'POST'), None)
        
        if get_finding and post_finding:
            assert post_finding.severity == 'high'
            assert get_finding.severity == 'medium'
