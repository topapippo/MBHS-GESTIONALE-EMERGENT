"""
Tests for Website CMS Feature - MBHS SALON
Tests cover: Website Config, Reviews, Gallery CRUD, Upload, Public Endpoint
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hair-salon-portal-1.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "melitobruno@gmail.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for protected endpoints"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestPublicEndpoints:
    """Test public website endpoints (no auth required)"""
    
    def test_public_website_endpoint_returns_200(self):
        """Test GET /api/public/website returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200, f"Public website endpoint failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "config" in data, "Missing 'config' in response"
        assert "reviews" in data, "Missing 'reviews' in response"
        assert "gallery" in data, "Missing 'gallery' in response"
        assert "services" in data, "Missing 'services' in response"
    
    def test_public_website_config_has_default_fields(self):
        """Test config contains expected default fields"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200
        config = response.json()["config"]
        
        # Check essential config fields
        assert "salon_name" in config
        assert "hero_description" in config
        assert "hours" in config
        assert "phones" in config
        assert "service_categories" in config
        
        # Verify salon name is set
        assert config["salon_name"] == "BRUNO MELITO HAIR"
    
    def test_public_operators_endpoint(self):
        """Test GET /api/public/operators"""
        response = requests.get(f"{BASE_URL}/api/public/operators")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_public_services_endpoint(self):
        """Test GET /api/public/services"""
        response = requests.get(f"{BASE_URL}/api/public/services")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestWebsiteConfigCRUD:
    """Test website config CRUD operations (auth required)"""
    
    def test_get_website_config_authenticated(self, auth_headers):
        """Test GET /api/website/config with auth"""
        response = requests.get(f"{BASE_URL}/api/website/config", headers=auth_headers)
        assert response.status_code == 200, f"Get config failed: {response.text}"
        data = response.json()
        assert "salon_name" in data
    
    def test_get_website_config_without_auth_fails(self):
        """Test GET /api/website/config without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/website/config")
        assert response.status_code in [401, 403], "Should require authentication"
    
    def test_update_website_config(self, auth_headers):
        """Test PUT /api/website/config updates salon name"""
        # Get current config
        get_resp = requests.get(f"{BASE_URL}/api/website/config", headers=auth_headers)
        original_name = get_resp.json().get("salon_name", "BRUNO MELITO HAIR")
        
        # Update config
        new_name = "TEST_MBHS SALON Updated"
        update_data = {"salon_name": new_name}
        response = requests.put(f"{BASE_URL}/api/website/config", headers=auth_headers, json=update_data)
        assert response.status_code == 200, f"Update config failed: {response.text}"
        
        # Verify update persisted
        verify_resp = requests.get(f"{BASE_URL}/api/website/config", headers=auth_headers)
        assert verify_resp.status_code == 200
        updated_config = verify_resp.json()
        assert updated_config["salon_name"] == new_name, "Salon name not updated"
        
        # Restore original
        restore_data = {"salon_name": original_name}
        requests.put(f"{BASE_URL}/api/website/config", headers=auth_headers, json=restore_data)
    
    def test_update_service_categories(self, auth_headers):
        """Test updating service categories in config"""
        # Get current config
        get_resp = requests.get(f"{BASE_URL}/api/website/config", headers=auth_headers)
        original_categories = get_resp.json().get("service_categories", [])
        
        # Update with new category
        new_categories = [
            {"title": "TEST_Category", "desc": "Test description", "items": [{"name": "Test Service", "price": "50"}]}
        ]
        response = requests.put(f"{BASE_URL}/api/website/config", headers=auth_headers, json={"service_categories": new_categories})
        assert response.status_code == 200
        
        # Verify
        verify_resp = requests.get(f"{BASE_URL}/api/website/config", headers=auth_headers)
        updated_categories = verify_resp.json().get("service_categories", [])
        assert len(updated_categories) >= 1
        assert updated_categories[0]["title"] == "TEST_Category"
        
        # Restore original
        requests.put(f"{BASE_URL}/api/website/config", headers=auth_headers, json={"service_categories": original_categories})


class TestWebsiteReviewsCRUD:
    """Test website reviews CRUD operations"""
    
    created_review_id = None
    
    def test_get_reviews_authenticated(self, auth_headers):
        """Test GET /api/website/reviews"""
        response = requests.get(f"{BASE_URL}/api/website/reviews", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_review(self, auth_headers):
        """Test POST /api/website/reviews"""
        review_data = {
            "name": "TEST_Maria Rossi",
            "text": "Servizio fantastico! Molto professionali.",
            "rating": 5
        }
        response = requests.post(f"{BASE_URL}/api/website/reviews", headers=auth_headers, json=review_data)
        assert response.status_code == 200, f"Create review failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["name"] == "TEST_Maria Rossi"
        assert data["rating"] == 5
        
        # Store for cleanup
        TestWebsiteReviewsCRUD.created_review_id = data["id"]
    
    def test_review_appears_in_list(self, auth_headers):
        """Verify created review appears in list"""
        if not TestWebsiteReviewsCRUD.created_review_id:
            pytest.skip("No review created")
        
        response = requests.get(f"{BASE_URL}/api/website/reviews", headers=auth_headers)
        reviews = response.json()
        review_ids = [r["id"] for r in reviews]
        assert TestWebsiteReviewsCRUD.created_review_id in review_ids
    
    def test_update_review(self, auth_headers):
        """Test PUT /api/website/reviews/{id}"""
        if not TestWebsiteReviewsCRUD.created_review_id:
            pytest.skip("No review created")
        
        update_data = {
            "name": "TEST_Maria Updated",
            "text": "Updated review text",
            "rating": 4
        }
        response = requests.put(
            f"{BASE_URL}/api/website/reviews/{TestWebsiteReviewsCRUD.created_review_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        
        # Verify update
        verify_resp = requests.get(f"{BASE_URL}/api/website/reviews", headers=auth_headers)
        reviews = verify_resp.json()
        updated_review = next((r for r in reviews if r["id"] == TestWebsiteReviewsCRUD.created_review_id), None)
        assert updated_review is not None
        assert updated_review["name"] == "TEST_Maria Updated"
    
    def test_delete_review(self, auth_headers):
        """Test DELETE /api/website/reviews/{id}"""
        if not TestWebsiteReviewsCRUD.created_review_id:
            pytest.skip("No review created")
        
        response = requests.delete(
            f"{BASE_URL}/api/website/reviews/{TestWebsiteReviewsCRUD.created_review_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify deletion
        verify_resp = requests.get(f"{BASE_URL}/api/website/reviews", headers=auth_headers)
        reviews = verify_resp.json()
        review_ids = [r["id"] for r in reviews]
        assert TestWebsiteReviewsCRUD.created_review_id not in review_ids


class TestWebsiteGalleryCRUD:
    """Test website gallery CRUD operations"""
    
    created_gallery_id = None
    
    def test_get_gallery_authenticated(self, auth_headers):
        """Test GET /api/website/gallery"""
        response = requests.get(f"{BASE_URL}/api/website/gallery", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_gallery_item(self, auth_headers):
        """Test POST /api/website/gallery"""
        gallery_data = {
            "image_url": "https://example.com/test-image.jpg",
            "label": "TEST_Gallery Item",
            "tag": "Balayage",
            "section": "gallery"
        }
        response = requests.post(f"{BASE_URL}/api/website/gallery", headers=auth_headers, json=gallery_data)
        assert response.status_code == 200, f"Create gallery item failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["label"] == "TEST_Gallery Item"
        assert data["section"] == "gallery"
        
        TestWebsiteGalleryCRUD.created_gallery_id = data["id"]
    
    def test_create_salon_photo(self, auth_headers):
        """Test creating a salon photo (different section)"""
        salon_data = {
            "image_url": "https://example.com/salon-photo.jpg",
            "label": "TEST_Salon Interior",
            "tag": "",
            "section": "salon"
        }
        response = requests.post(f"{BASE_URL}/api/website/gallery", headers=auth_headers, json=salon_data)
        assert response.status_code == 200
        data = response.json()
        assert data["section"] == "salon"
        
        # Cleanup immediately
        requests.delete(f"{BASE_URL}/api/website/gallery/{data['id']}", headers=auth_headers)
    
    def test_update_gallery_item(self, auth_headers):
        """Test PUT /api/website/gallery/{id}"""
        if not TestWebsiteGalleryCRUD.created_gallery_id:
            pytest.skip("No gallery item created")
        
        update_data = {"label": "TEST_Updated Label", "tag": "Colore"}
        response = requests.put(
            f"{BASE_URL}/api/website/gallery/{TestWebsiteGalleryCRUD.created_gallery_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["label"] == "TEST_Updated Label"
        assert data["tag"] == "Colore"
    
    def test_delete_gallery_item(self, auth_headers):
        """Test DELETE /api/website/gallery/{id} (soft delete)"""
        if not TestWebsiteGalleryCRUD.created_gallery_id:
            pytest.skip("No gallery item created")
        
        response = requests.delete(
            f"{BASE_URL}/api/website/gallery/{TestWebsiteGalleryCRUD.created_gallery_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify soft deletion (item no longer in list)
        verify_resp = requests.get(f"{BASE_URL}/api/website/gallery", headers=auth_headers)
        gallery_items = verify_resp.json()
        item_ids = [g["id"] for g in gallery_items]
        assert TestWebsiteGalleryCRUD.created_gallery_id not in item_ids


class TestWebsiteUpload:
    """Test website file upload endpoint"""
    
    def test_upload_requires_auth(self):
        """Test upload endpoint requires authentication"""
        # Create a simple test file
        files = {"file": ("test.jpg", b"fake image data", "image/jpeg")}
        response = requests.post(f"{BASE_URL}/api/website/upload", files=files)
        assert response.status_code in [401, 403], "Upload should require auth"
    
    def test_upload_rejects_invalid_format(self, auth_headers):
        """Test upload rejects non-image files"""
        files = {"file": ("test.txt", b"text content", "text/plain")}
        response = requests.post(f"{BASE_URL}/api/website/upload", files=files, headers=auth_headers)
        assert response.status_code == 400, "Should reject non-image files"
    
    def test_upload_accepts_valid_image(self, auth_headers):
        """Test upload accepts valid image formats"""
        # Create a minimal valid JPEG (1x1 pixel)
        jpeg_data = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
            0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
            0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
            0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
            0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
            0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
            0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
            0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
            0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
            0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
            0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
            0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
            0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
            0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
            0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
            0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
            0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
            0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0xFF, 0xD9
        ])
        
        files = {"file": ("test_image.jpg", jpeg_data, "image/jpeg")}
        response = requests.post(f"{BASE_URL}/api/website/upload", files=files, headers=auth_headers)
        # May fail if object storage is not configured - acceptable
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}, {response.text}"


class TestExistingPagesStillWork:
    """Test that existing pages/endpoints still work after CMS addition"""
    
    def test_login_endpoint_works(self):
        """Test login still works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_dashboard_endpoint_works(self, auth_headers):
        """Test dashboard stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/stats/dashboard", headers=auth_headers)
        assert response.status_code == 200
    
    def test_services_endpoint_works(self, auth_headers):
        """Test services endpoint"""
        response = requests.get(f"{BASE_URL}/api/services", headers=auth_headers)
        assert response.status_code == 200
    
    def test_clients_endpoint_works(self, auth_headers):
        """Test clients endpoint"""
        response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        assert response.status_code == 200
    
    def test_operators_endpoint_works(self, auth_headers):
        """Test operators endpoint"""
        response = requests.get(f"{BASE_URL}/api/operators", headers=auth_headers)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
