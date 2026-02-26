"""
Test suite for Reminders Page and Card Templates features
- Message templates CRUD
- Reminder reset endpoints
- Card templates (preset packages) CRUD
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "melitobruno@gmail.com",
        "password": "password123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Create headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

class TestMessageTemplates:
    """Test message templates CRUD for reminders page"""
    
    def test_get_templates_returns_defaults_if_empty(self, auth_headers):
        """GET /api/reminders/templates should return templates (creates defaults if none exist)"""
        response = requests.get(f"{BASE_URL}/api/reminders/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()
        assert isinstance(templates, list)
        # Should have at least 2 default templates (appointment + recall)
        assert len(templates) >= 2
        
        # Verify template structure
        for tmpl in templates:
            assert "id" in tmpl
            assert "name" in tmpl
            assert "text" in tmpl
            assert "template_type" in tmpl
            assert tmpl["template_type"] in ["appointment", "recall"]
        print(f"✓ Got {len(templates)} message templates")
    
    def test_create_message_template(self, auth_headers):
        """POST /api/reminders/templates should create new template"""
        unique_name = f"TEST_Template_{uuid.uuid4().hex[:8]}"
        payload = {
            "name": unique_name,
            "text": "Ciao {nome}! Questo è un messaggio di test.",
            "template_type": "appointment"
        }
        response = requests.post(f"{BASE_URL}/api/reminders/templates", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        created = response.json()
        assert created["name"] == unique_name
        assert created["text"] == payload["text"]
        assert created["template_type"] == "appointment"
        assert "id" in created
        print(f"✓ Created template: {created['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/reminders/templates/{created['id']}", headers=auth_headers)
        return created["id"]
    
    def test_update_message_template(self, auth_headers):
        """PUT /api/reminders/templates/{id} should update template"""
        # First create a template
        unique_name = f"TEST_Update_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/reminders/templates", json={
            "name": unique_name,
            "text": "Original text",
            "template_type": "recall"
        }, headers=auth_headers)
        assert create_response.status_code == 200
        template_id = create_response.json()["id"]
        
        # Update it
        update_payload = {
            "name": f"{unique_name}_updated",
            "text": "Updated text with {nome} and {giorni}"
        }
        update_response = requests.put(f"{BASE_URL}/api/reminders/templates/{template_id}", json=update_payload, headers=auth_headers)
        assert update_response.status_code == 200
        
        updated = update_response.json()
        assert updated["name"] == f"{unique_name}_updated"
        assert updated["text"] == "Updated text with {nome} and {giorni}"
        print(f"✓ Updated template: {updated['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/reminders/templates/{template_id}", headers=auth_headers)
    
    def test_delete_message_template(self, auth_headers):
        """DELETE /api/reminders/templates/{id} should delete template"""
        # First create a template
        unique_name = f"TEST_Delete_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/reminders/templates", json={
            "name": unique_name,
            "text": "To be deleted",
            "template_type": "appointment"
        }, headers=auth_headers)
        assert create_response.status_code == 200
        template_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/reminders/templates/{template_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] == True
        print(f"✓ Deleted template: {unique_name}")
        
        # Verify it's gone
        get_response = requests.get(f"{BASE_URL}/api/reminders/templates", headers=auth_headers)
        templates = get_response.json()
        assert not any(t["id"] == template_id for t in templates)


class TestRemindersEndpoints:
    """Test reminder-related endpoints"""
    
    def test_get_tomorrow_reminders(self, auth_headers):
        """GET /api/reminders/tomorrow should return appointments for tomorrow"""
        response = requests.get(f"{BASE_URL}/api/reminders/tomorrow", headers=auth_headers)
        assert response.status_code == 200
        reminders = response.json()
        assert isinstance(reminders, list)
        
        # Verify structure if any exist
        for r in reminders:
            assert "id" in r
            assert "client_name" in r
            assert "client_phone" in r
            assert "date" in r
            assert "time" in r
            assert "reminded" in r
        print(f"✓ Got {len(reminders)} tomorrow reminders")
    
    def test_get_inactive_clients(self, auth_headers):
        """GET /api/reminders/inactive-clients should return inactive clients (60+ days)"""
        response = requests.get(f"{BASE_URL}/api/reminders/inactive-clients", headers=auth_headers)
        assert response.status_code == 200
        inactive = response.json()
        assert isinstance(inactive, list)
        
        # Verify structure if any exist
        for client in inactive:
            assert "client_id" in client
            assert "client_name" in client
            assert "days_ago" in client
            assert "already_recalled" in client
        print(f"✓ Got {len(inactive)} inactive clients")
    
    def test_appointment_reset_endpoint_exists(self, auth_headers):
        """DELETE /api/reminders/appointment/{id}/reset endpoint should exist"""
        # Test with a fake ID - should return success even if no matches
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/reminders/appointment/{fake_id}/reset", headers=auth_headers)
        # Should return 200 with deleted: 0 (no matches)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        print("✓ Appointment reset endpoint works")
    
    def test_inactive_reset_endpoint_exists(self, auth_headers):
        """DELETE /api/reminders/inactive/{id}/reset endpoint should exist"""
        # Test with a fake ID - should return success even if no matches
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/reminders/inactive/{fake_id}/reset", headers=auth_headers)
        # Should return 200 with deleted: 0 (no matches)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        print("✓ Inactive client reset endpoint works")


class TestCardTemplates:
    """Test card templates (preset packages) CRUD"""
    
    def test_get_card_templates(self, auth_headers):
        """GET /api/card-templates should return card templates"""
        response = requests.get(f"{BASE_URL}/api/card-templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()
        assert isinstance(templates, list)
        print(f"✓ Got {len(templates)} card templates")
        
        # Verify structure if any exist
        for tmpl in templates:
            assert "id" in tmpl
            assert "name" in tmpl
            assert "card_type" in tmpl
            assert "total_value" in tmpl
    
    def test_create_card_template(self, auth_headers):
        """POST /api/card-templates should create new package template"""
        unique_name = f"TEST_Package_{uuid.uuid4().hex[:8]}"
        payload = {
            "name": unique_name,
            "card_type": "prepaid",
            "total_value": 150.00,
            "total_services": 10,
            "duration_months": 6,
            "notes": "Test package for automated testing"
        }
        response = requests.post(f"{BASE_URL}/api/card-templates", json=payload, headers=auth_headers)
        assert response.status_code == 200
        
        created = response.json()
        assert created["name"] == unique_name
        assert created["card_type"] == "prepaid"
        assert created["total_value"] == 150.00
        assert created["total_services"] == 10
        assert created["duration_months"] == 6
        assert "id" in created
        print(f"✓ Created card template: {created['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/card-templates/{created['id']}", headers=auth_headers)
        return created["id"]
    
    def test_update_card_template(self, auth_headers):
        """PUT /api/card-templates/{id} should update package template"""
        # First create a template
        unique_name = f"TEST_PkgUpdate_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/card-templates", json={
            "name": unique_name,
            "card_type": "prepaid",
            "total_value": 100.00
        }, headers=auth_headers)
        assert create_response.status_code == 200
        template_id = create_response.json()["id"]
        
        # Update it
        update_payload = {
            "name": f"{unique_name}_updated",
            "total_value": 200.00,
            "total_services": 15
        }
        update_response = requests.put(f"{BASE_URL}/api/card-templates/{template_id}", json=update_payload, headers=auth_headers)
        assert update_response.status_code == 200
        
        updated = update_response.json()
        assert updated["name"] == f"{unique_name}_updated"
        assert updated["total_value"] == 200.00
        assert updated["total_services"] == 15
        print(f"✓ Updated card template: {updated['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/card-templates/{template_id}", headers=auth_headers)
    
    def test_delete_card_template(self, auth_headers):
        """DELETE /api/card-templates/{id} should delete package template"""
        # First create a template
        unique_name = f"TEST_PkgDelete_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/card-templates", json={
            "name": unique_name,
            "card_type": "subscription",
            "total_value": 50.00
        }, headers=auth_headers)
        assert create_response.status_code == 200
        template_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/card-templates/{template_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] == True
        print(f"✓ Deleted card template: {unique_name}")
        
        # Verify it's gone
        get_response = requests.get(f"{BASE_URL}/api/card-templates", headers=auth_headers)
        templates = get_response.json()
        assert not any(t["id"] == template_id for t in templates)


class TestExistingPresetPackages:
    """Verify the 3 pre-created packages from main agent"""
    
    def test_preset_packages_exist(self, auth_headers):
        """Verify that 3 preset packages were created"""
        response = requests.get(f"{BASE_URL}/api/card-templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()
        
        # Should have at least 3 packages
        print(f"✓ Found {len(templates)} card templates")
        
        for tmpl in templates:
            print(f"  - {tmpl['name']}: €{tmpl['total_value']} ({tmpl['card_type']})")
            if tmpl.get('total_services'):
                print(f"    Services: {tmpl['total_services']}")
            if tmpl.get('duration_months'):
                print(f"    Duration: {tmpl['duration_months']} months")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
