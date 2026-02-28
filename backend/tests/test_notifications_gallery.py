"""
Test cases for:
1. Notification banner feature - new online booking notifications
2. Website gallery photos loading
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestNotificationEndpoints:
    """Tests for online booking notification feature"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_get_new_bookings_endpoint_returns_online_bookings(self, auth_token):
        """GET /api/notifications/new-bookings returns list of online bookings"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/new-bookings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify all returned bookings have source='online'
        for booking in data:
            assert booking.get("source") == "online", f"Booking {booking.get('id')} should be online"
            assert "client_name" in booking
            assert "date" in booking
            assert "time" in booking
            assert "services" in booking
    
    def test_get_new_bookings_returns_booking_details(self, auth_token):
        """Verify booking details include required fields for notification display"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/new-bookings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 0:
            booking = data[0]
            # Notification banner needs: client_name, date, time, services
            assert "id" in booking
            assert "client_name" in booking
            assert "date" in booking
            assert "time" in booking
            assert "services" in booking and isinstance(booking["services"], list)
            
            # Services should have name
            if len(booking["services"]) > 0:
                assert "name" in booking["services"][0]
    
    def test_mark_seen_endpoint_updates_booking(self, auth_token):
        """POST /api/notifications/mark-seen sets seen_at timestamp"""
        # First get list of bookings
        get_response = requests.get(
            f"{BASE_URL}/api/notifications/new-bookings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 200
        
        bookings = get_response.json()
        if len(bookings) == 0:
            pytest.skip("No online bookings to test with")
        
        # Find an unseen booking or use first one
        test_booking_id = bookings[0]["id"]
        
        # Mark it as seen
        mark_response = requests.post(
            f"{BASE_URL}/api/notifications/mark-seen",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"appointment_ids": [test_booking_id]}
        )
        assert mark_response.status_code == 200
        
        result = mark_response.json()
        assert "marked" in result
        assert result["marked"] == 1
    
    def test_mark_multiple_bookings_seen(self, auth_token):
        """Mark-seen endpoint handles multiple appointment IDs"""
        # Get bookings
        get_response = requests.get(
            f"{BASE_URL}/api/notifications/new-bookings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        bookings = get_response.json()
        
        if len(bookings) < 2:
            pytest.skip("Need at least 2 bookings to test multiple mark")
        
        # Mark first 2 as seen
        apt_ids = [bookings[0]["id"], bookings[1]["id"]]
        mark_response = requests.post(
            f"{BASE_URL}/api/notifications/mark-seen",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"appointment_ids": apt_ids}
        )
        assert mark_response.status_code == 200
        assert mark_response.json()["marked"] == 2


class TestWebsiteGallery:
    """Tests for website gallery photos feature"""
    
    def test_public_website_endpoint_returns_gallery(self):
        """GET /api/public/website returns gallery array"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200
        
        data = response.json()
        assert "gallery" in data, "Response should have gallery field"
        assert isinstance(data["gallery"], list)
    
    def test_gallery_has_salon_photos(self):
        """Gallery contains salon photos (section='salon')"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200
        
        data = response.json()
        salon_photos = [g for g in data.get("gallery", []) if g.get("section") == "salon"]
        
        assert len(salon_photos) >= 4, f"Expected at least 4 salon photos, got {len(salon_photos)}"
        
        # Verify expected salon photo labels
        labels = [p.get("label") for p in salon_photos]
        expected_labels = ["Il Salone", "Reception", "Interni", "Postazioni"]
        for expected in expected_labels:
            assert expected in labels, f"Missing salon photo: {expected}"
    
    def test_gallery_photos_have_valid_urls(self):
        """All gallery items have valid image_url"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200
        
        data = response.json()
        for item in data.get("gallery", []):
            assert "image_url" in item, f"Gallery item {item.get('id')} missing image_url"
            assert item["image_url"].startswith("http"), f"Image URL should be absolute: {item.get('image_url')}"
            assert "customer-assets.emergentagent.com" in item["image_url"], "Should use customer-assets"
    
    def test_gallery_photos_have_required_fields(self):
        """Gallery items have all required fields"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200
        
        data = response.json()
        for item in data.get("gallery", []):
            assert "id" in item
            assert "image_url" in item
            assert "section" in item
            assert item["section"] in ["salon", "works", "gallery"]
            # label is optional but should exist for salon photos
            if item["section"] == "salon":
                assert "label" in item
    
    def test_gallery_has_works_photos(self):
        """Gallery contains hairstyle work photos (section='works' or 'gallery')"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200
        
        data = response.json()
        works_photos = [g for g in data.get("gallery", []) if g.get("section") in ["works", "gallery"]]
        
        assert len(works_photos) >= 4, f"Expected at least 4 works photos, got {len(works_photos)}"


class TestPublicBookingFlow:
    """Tests for public booking page (/prenota)"""
    
    def test_public_services_endpoint(self):
        """GET /api/public/services returns list of services"""
        response = requests.get(f"{BASE_URL}/api/public/services")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should have at least one service"
        
        # Verify service structure
        service = data[0]
        assert "id" in service
        assert "name" in service
        assert "duration" in service
        assert "price" in service
    
    def test_public_operators_endpoint(self):
        """GET /api/public/operators returns list of operators"""
        response = requests.get(f"{BASE_URL}/api/public/operators")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # May be empty if not configured, but should not error


class TestLoginFlow:
    """Test login still works"""
    
    def test_login_valid_credentials(self):
        """Login with valid credentials returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "melitobruno@gmail.com"
    
    def test_login_invalid_credentials(self):
        """Login with wrong password returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


class TestPlanningAppointments:
    """Test planning page appointments still work"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        return response.json()["access_token"]
    
    def test_get_appointments_by_date(self, auth_token):
        """GET /api/appointments with date filter works"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/appointments?date={today}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_operators(self, auth_token):
        """GET /api/operators returns active operators"""
        response = requests.get(
            f"{BASE_URL}/api/operators",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should have at least one operator"
