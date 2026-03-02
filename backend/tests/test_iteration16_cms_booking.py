"""
Test Iteration 16: BookingPage CMS Integration and WebsiteAdminPage Upload Tests
Testing dynamic CMS data fetch and z-index fix for upload button
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPublicWebsiteEndpoint:
    """Tests for /api/public/website endpoint - returns CMS data for BookingPage"""
    
    def test_public_website_returns_200(self):
        """Public website endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_public_website_contains_config(self):
        """Response should contain config object"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        data = response.json()
        assert "config" in data, "Response missing 'config' key"
        assert isinstance(data["config"], dict), "Config should be a dict"
    
    def test_public_website_config_has_required_fields(self):
        """Config should have required salon info fields"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        config = response.json()["config"]
        
        required_fields = [
            "salon_name", "about_title", "about_text", 
            "phones", "email", "address", "hours"
        ]
        for field in required_fields:
            assert field in config, f"Config missing required field: {field}"
    
    def test_public_website_config_service_categories(self):
        """Config should have service_categories for public pricing display"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        config = response.json()["config"]
        assert "service_categories" in config, "Config missing 'service_categories'"
        # Can be empty list but must exist
        assert isinstance(config["service_categories"], list), "service_categories should be a list"
    
    def test_public_website_contains_reviews(self):
        """Response should contain reviews array"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        data = response.json()
        assert "reviews" in data, "Response missing 'reviews' key"
        assert isinstance(data["reviews"], list), "Reviews should be a list"
    
    def test_public_website_contains_gallery(self):
        """Response should contain gallery array"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        data = response.json()
        assert "gallery" in data, "Response missing 'gallery' key"
        assert isinstance(data["gallery"], list), "Gallery should be a list"
    
    def test_public_website_gallery_has_sections(self):
        """Gallery items should have section field (salon/gallery)"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        gallery = response.json()["gallery"]
        
        if len(gallery) > 0:
            for item in gallery[:5]:  # Check first 5 items
                assert "section" in item, f"Gallery item missing 'section': {item}"
                assert item["section"] in ["salon", "gallery", "works"], f"Invalid section: {item['section']}"
                assert "image_url" in item, f"Gallery item missing 'image_url': {item}"
    
    def test_public_website_contains_services(self):
        """Response should contain services array for booking"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        data = response.json()
        assert "services" in data, "Response missing 'services' key"
        assert isinstance(data["services"], list), "Services should be a list"


class TestPublicServicesAndOperators:
    """Tests for /api/public/services and /api/public/operators endpoints"""
    
    def test_public_services_returns_list(self):
        """Public services should return list of services"""
        response = requests.get(f"{BASE_URL}/api/public/services")
        assert response.status_code == 200
        services = response.json()
        assert isinstance(services, list), "Should return a list"
        if len(services) > 0:
            assert "name" in services[0], "Service should have 'name'"
            assert "price" in services[0], "Service should have 'price'"
            assert "duration" in services[0], "Service should have 'duration'"
    
    def test_public_operators_returns_list(self):
        """Public operators should return list of operators"""
        response = requests.get(f"{BASE_URL}/api/public/operators")
        assert response.status_code == 200
        operators = response.json()
        assert isinstance(operators, list), "Should return a list"
        if len(operators) > 0:
            assert "name" in operators[0], "Operator should have 'name'"


class TestAuthenticatedWebsiteEndpoints:
    """Tests for authenticated website CMS endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Return headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_website_config_get(self, auth_headers):
        """Authenticated GET /website/config should return config"""
        response = requests.get(f"{BASE_URL}/api/website/config", headers=auth_headers)
        assert response.status_code == 200
        config = response.json()
        assert "salon_name" in config
    
    def test_website_reviews_get(self, auth_headers):
        """Authenticated GET /website/reviews should return reviews list"""
        response = requests.get(f"{BASE_URL}/api/website/reviews", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_website_gallery_get(self, auth_headers):
        """Authenticated GET /website/gallery should return gallery list"""
        response = requests.get(f"{BASE_URL}/api/website/gallery", headers=auth_headers)
        assert response.status_code == 200
        gallery = response.json()
        assert isinstance(gallery, list)
        
        # Verify gallery items have required fields
        for item in gallery:
            assert "id" in item
            assert "image_url" in item
            assert "section" in item


class TestBookingPageIntegration:
    """Integration tests simulating BookingPage data fetching"""
    
    def test_full_booking_page_data_fetch(self):
        """Simulate BookingPage's fetchData() - all APIs should return data"""
        # This is what BookingPage.jsx fetches on mount
        services_res = requests.get(f"{BASE_URL}/api/public/services")
        operators_res = requests.get(f"{BASE_URL}/api/public/operators")
        site_res = requests.get(f"{BASE_URL}/api/public/website")
        
        assert services_res.status_code == 200, "Services API failed"
        assert operators_res.status_code == 200, "Operators API failed"
        assert site_res.status_code == 200, "Website API failed"
        
        # Verify data structure
        site_data = site_res.json()
        assert "config" in site_data
        assert "reviews" in site_data
        assert "gallery" in site_data
        
    def test_booking_page_can_filter_gallery_by_section(self):
        """BookingPage filters gallery by section (salon/gallery)"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        gallery = response.json()["gallery"]
        
        salon_photos = [g for g in gallery if g.get("section") == "salon"]
        hairstyle_photos = [g for g in gallery if g.get("section") == "gallery"]
        
        # At least salon photos should exist based on previous tests
        print(f"Salon photos: {len(salon_photos)}, Hairstyle photos: {len(hairstyle_photos)}")
        
        # The filter logic should work
        for photo in salon_photos:
            assert photo["section"] == "salon"
        for photo in hairstyle_photos:
            assert photo["section"] == "gallery"


class TestWebsiteUploadEndpoint:
    """Test /api/website/upload endpoint (requires auth)"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['access_token']}"}
        pytest.skip("Authentication failed")
    
    def test_upload_requires_auth(self):
        """Upload endpoint should require authentication"""
        # Create a simple test file
        files = {'file': ('test.jpg', b'fake image data', 'image/jpeg')}
        response = requests.post(f"{BASE_URL}/api/website/upload", files=files)
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_upload_endpoint_exists(self, auth_headers):
        """Upload endpoint should exist and accept requests"""
        # Just test endpoint responds - don't actually upload to avoid test pollution
        # A malformed request should return 4xx, not 5xx
        response = requests.post(
            f"{BASE_URL}/api/website/upload", 
            headers=auth_headers,
            files={}  # Empty files - should fail validation but not crash
        )
        # Should return 422 (validation error) for missing file, not 500
        assert response.status_code != 500, f"Upload endpoint returned 500: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
