"""
Test Promotions API - MBHS Salon Promotions System
Tests all promotions CRUD, public endpoints, and checkout integration
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "melitobruno@gmail.com"
TEST_PASSWORD = "password123"

@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for testing"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get auth headers"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

# ============== GET /api/promotions ==============
class TestGetPromotions:
    """Test GET /api/promotions - should return promotions with usage_count"""
    
    def test_get_promotions_returns_list(self, auth_headers):
        """GET /api/promotions returns list of promotions"""
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_promotions_have_required_fields(self, auth_headers):
        """Each promo should have id, name, description, rule_type, free_service_name, promo_code, active, usage_count"""
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        assert response.status_code == 200
        promos = response.json()
        if len(promos) > 0:
            promo = promos[0]
            required_fields = ["id", "name", "rule_type", "free_service_name", "promo_code", "active"]
            for field in required_fields:
                assert field in promo, f"Missing field: {field}"
            # usage_count should be present
            assert "usage_count" in promo, "usage_count field missing"
            assert isinstance(promo["usage_count"], int), "usage_count should be integer"
    
    def test_returns_8_promotions(self, auth_headers):
        """Should return 8 default promotions as per requirement"""
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        assert response.status_code == 200
        promos = response.json()
        # Note: May have more if test created extras, but should have at least 8
        assert len(promos) >= 8, f"Expected at least 8 promotions, got {len(promos)}"
        print(f"Found {len(promos)} promotions")

# ============== POST /api/promotions ==============
class TestCreatePromotion:
    """Test POST /api/promotions - create new promotion"""
    
    def test_create_promotion_success(self, auth_headers):
        """Create a new promotion successfully"""
        test_promo = {
            "name": f"TEST_Promo_{uuid.uuid4().hex[:6]}",
            "description": "Test promo description",
            "rule_type": "promo_code",
            "free_service_name": "Piega Gratuita",
            "promo_code": f"TESTCODE{uuid.uuid4().hex[:4].upper()}",
            "active": True,
            "show_on_booking": True
        }
        response = requests.post(f"{BASE_URL}/api/promotions", json=test_promo, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert data["name"] == test_promo["name"]
        assert data["free_service_name"] == test_promo["free_service_name"]
        assert data["active"] == True
        assert "id" in data
        print(f"Created promo: {data['id']}")
        return data["id"]
    
    def test_create_promotion_generates_code_if_missing(self, auth_headers):
        """If promo_code not provided for promo_code type, generate one"""
        test_promo = {
            "name": f"TEST_AutoCode_{uuid.uuid4().hex[:6]}",
            "description": "Auto code test",
            "rule_type": "promo_code",
            "free_service_name": "Trattamento Gratis",
            "promo_code": "",  # Empty - should generate
            "active": True
        }
        response = requests.post(f"{BASE_URL}/api/promotions", json=test_promo, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        # Should have a generated code
        assert data.get("promo_code") is not None and len(data.get("promo_code", "")) > 0

# ============== PUT /api/promotions/{id} ==============
class TestUpdatePromotion:
    """Test PUT /api/promotions/{id} - update promotion including toggle"""
    
    def test_update_promotion_name(self, auth_headers):
        """Update promotion name"""
        # First get existing promotions
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        promos = response.json()
        if len(promos) == 0:
            pytest.skip("No promotions to update")
        
        promo_id = promos[0]["id"]
        original_name = promos[0]["name"]
        
        # Update
        new_name = f"Updated_{uuid.uuid4().hex[:6]}"
        update_response = requests.put(
            f"{BASE_URL}/api/promotions/{promo_id}",
            json={"name": new_name},
            headers=auth_headers
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Verify and restore
        updated = update_response.json()
        assert updated["name"] == new_name
        
        # Restore original
        requests.put(f"{BASE_URL}/api/promotions/{promo_id}", json={"name": original_name}, headers=auth_headers)
    
    def test_toggle_active_status(self, auth_headers):
        """Test toggling active status on/off"""
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        promos = response.json()
        if len(promos) == 0:
            pytest.skip("No promotions to toggle")
        
        promo = promos[0]
        promo_id = promo["id"]
        original_active = promo["active"]
        
        # Toggle off
        toggle_response = requests.put(
            f"{BASE_URL}/api/promotions/{promo_id}",
            json={"active": not original_active},
            headers=auth_headers
        )
        assert toggle_response.status_code == 200
        assert toggle_response.json()["active"] == (not original_active)
        
        # Restore
        requests.put(f"{BASE_URL}/api/promotions/{promo_id}", json={"active": original_active}, headers=auth_headers)
        print(f"Toggle test passed - original: {original_active}, toggled: {not original_active}")

# ============== DELETE /api/promotions/{id} ==============
class TestDeletePromotion:
    """Test DELETE /api/promotions/{id}"""
    
    def test_delete_promotion(self, auth_headers):
        """Create then delete a promotion"""
        # Create a test promo
        test_promo = {
            "name": f"TEST_ToDelete_{uuid.uuid4().hex[:6]}",
            "description": "Will be deleted",
            "rule_type": "promo_code",
            "free_service_name": "Delete Test Service",
            "active": True
        }
        create_resp = requests.post(f"{BASE_URL}/api/promotions", json=test_promo, headers=auth_headers)
        assert create_resp.status_code == 200
        promo_id = create_resp.json()["id"]
        
        # Delete it
        delete_resp = requests.delete(f"{BASE_URL}/api/promotions/{promo_id}", headers=auth_headers)
        assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.text}"
        
        # Verify deleted - trying to update should fail
        verify_resp = requests.put(f"{BASE_URL}/api/promotions/{promo_id}", json={"name": "test"}, headers=auth_headers)
        assert verify_resp.status_code == 404, "Should not find deleted promo"
        print(f"Deleted promo {promo_id} successfully")

# ============== GET /api/promotions/check/{client_id} ==============
class TestCheckClientPromotions:
    """Test GET /api/promotions/check/{client_id} - returns eligible promos"""
    
    def test_check_client_promotions(self, auth_headers):
        """Check eligible promotions for a client"""
        # First get a client
        clients_resp = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        assert clients_resp.status_code == 200
        clients = clients_resp.json()
        if len(clients) == 0:
            pytest.skip("No clients to check")
        
        client_id = clients[0]["id"]
        
        # Check promotions
        response = requests.get(f"{BASE_URL}/api/promotions/check/{client_id}", headers=auth_headers)
        assert response.status_code == 200, f"Check failed: {response.text}"
        eligible = response.json()
        assert isinstance(eligible, list), "Should return list of eligible promos"
        print(f"Client {clients[0]['name']} has {len(eligible)} eligible promotions")

# ============== POST /api/promotions/{id}/use ==============
class TestUsePromotion:
    """Test POST /api/promotions/{id}/use - record promo usage"""
    
    def test_use_promotion(self, auth_headers):
        """Record usage of a promotion"""
        # Get promos
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        promos = response.json()
        if len(promos) == 0:
            pytest.skip("No promotions to use")
        
        promo = promos[0]
        promo_id = promo["id"]
        
        # Get a client
        clients_resp = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = clients_resp.json()
        if len(clients) == 0:
            pytest.skip("No clients")
        
        client_id = clients[0]["id"]
        client_name = clients[0]["name"]
        
        # Use promotion
        use_response = requests.post(
            f"{BASE_URL}/api/promotions/{promo_id}/use",
            json={"client_id": client_id, "client_name": client_name},
            headers=auth_headers
        )
        assert use_response.status_code == 200, f"Use promo failed: {use_response.text}"
        print(f"Used promo {promo['name']} for client {client_name}")

# ============== GET /api/public/promotions/all (NO AUTH) ==============
class TestPublicPromotionsEndpoint:
    """Test GET /api/public/promotions/all - public endpoint, no auth required"""
    
    def test_public_promotions_no_auth(self):
        """Public endpoint should work without auth"""
        response = requests.get(f"{BASE_URL}/api/public/promotions/all")
        assert response.status_code == 200, f"Public endpoint failed: {response.text}"
        promos = response.json()
        assert isinstance(promos, list)
        print(f"Public endpoint returned {len(promos)} promotions")
    
    def test_public_promotions_returns_active_only(self):
        """Public endpoint should only return active promotions"""
        response = requests.get(f"{BASE_URL}/api/public/promotions/all")
        assert response.status_code == 200
        promos = response.json()
        for promo in promos:
            assert promo.get("active") == True, f"Found inactive promo: {promo.get('name')}"
    
    def test_public_promotions_returns_8_promos(self):
        """Should return 8 active public promotions as per requirement"""
        response = requests.get(f"{BASE_URL}/api/public/promotions/all")
        assert response.status_code == 200
        promos = response.json()
        # Should have at least 8 default promos
        assert len(promos) >= 8, f"Expected at least 8 public promos, got {len(promos)}"

# ============== Verify 8 Default Promotions ==============
class TestDefaultPromotions:
    """Verify the 8 default promotions exist with correct promo codes"""
    
    def test_expected_promo_codes_exist(self, auth_headers):
        """Check that expected promo codes exist: UNDER30, REVIEW, AMICA, BENVENUTA, AUGURI, VIP10, CARD15, ABBO"""
        expected_codes = ["UNDER30", "REVIEW", "AMICA", "BENVENUTA", "AUGURI", "VIP10", "CARD15", "ABBO"]
        
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        assert response.status_code == 200
        promos = response.json()
        
        found_codes = [p.get("promo_code") for p in promos if p.get("promo_code")]
        
        for code in expected_codes:
            assert code in found_codes, f"Expected promo code '{code}' not found. Found: {found_codes}"
        
        print(f"All 8 expected promo codes found: {expected_codes}")
    
    def test_promo_rule_types(self, auth_headers):
        """Verify rule types are set correctly"""
        expected_rules = {
            "UNDER30": "under_30",
            "REVIEW": "google_review",
            "AMICA": "bring_friend",
            "BENVENUTA": "first_visit",
            "AUGURI": "birthday",
            "VIP10": "fidelity_vip"
        }
        
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        promos = response.json()
        code_to_promo = {p["promo_code"]: p for p in promos if p.get("promo_code")}
        
        for code, expected_rule in expected_rules.items():
            if code in code_to_promo:
                actual_rule = code_to_promo[code].get("rule_type")
                assert actual_rule == expected_rule, f"Promo {code} expected rule_type '{expected_rule}', got '{actual_rule}'"
        
        print("Rule types verified correctly")

# ============== Cleanup Test Data ==============
@pytest.fixture(autouse=True, scope="module")
def cleanup_test_promos(auth_headers):
    """Clean up test promotions after all tests"""
    yield
    # Cleanup - delete TEST_ prefixed promotions
    try:
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        if response.status_code == 200:
            promos = response.json()
            for promo in promos:
                if promo.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/promotions/{promo['id']}", headers=auth_headers)
                    print(f"Cleaned up test promo: {promo['name']}")
    except Exception as e:
        print(f"Cleanup error: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
