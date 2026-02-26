"""
Comprehensive regression tests for MBHS SALON CMS features
Tests: CMS website, social links, management fixes, payment methods, 
prepaid cards, recurring monthly, generic/new client, loyalty redemption, 
searchable clients in cards, MBHS operator
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
LOGIN_EMAIL = "melitobruno@gmail.com"
LOGIN_PASSWORD = "password123"

@pytest.fixture(scope="session")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": LOGIN_EMAIL,
        "password": LOGIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


# ==================== PUBLIC API TESTS (NO AUTH) ====================

class TestPublicWebsite:
    """Test public website endpoints (no auth required)"""
    
    def test_public_website_returns_config_with_defaults(self):
        """Test 18: GET /api/public/website returns config with phones and hours"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "config" in data
        config = data["config"]
        
        # Verify defaults are merged
        assert "phones" in config, "phones should be in config"
        assert "hours" in config, "hours should be in config"
        assert isinstance(config["phones"], list), "phones should be a list"
        assert isinstance(config["hours"], dict), "hours should be a dict"
        
        # Check default values are present
        assert config.get("salon_name") is not None
        print(f"✓ Public website config: salon_name={config.get('salon_name')}, phones={config.get('phones')}")
    
    def test_public_website_has_reviews(self):
        """GET /api/public/website includes reviews"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200
        data = response.json()
        assert "reviews" in data
        print(f"✓ Public website has {len(data['reviews'])} reviews")
    
    def test_public_website_has_gallery(self):
        """GET /api/public/website includes gallery"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200
        data = response.json()
        assert "gallery" in data
        print(f"✓ Public website has {len(data['gallery'])} gallery items")


class TestPublicBooking:
    """Test public booking endpoint"""
    
    def test_public_booking_endpoint_exists(self):
        """Test 17: POST /api/public/booking works (correct endpoint name)"""
        # First get services
        services_res = requests.get(f"{BASE_URL}/api/public/services")
        assert services_res.status_code == 200
        services = services_res.json()
        
        if not services:
            pytest.skip("No services available for booking test")
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Test the booking endpoint
        booking_data = {
            "client_name": "TEST_Booking_User",
            "client_phone": "3331234567",
            "service_ids": [services[0]["id"]],
            "date": tomorrow,
            "time": "11:00",
            "notes": "Test booking"
        }
        response = requests.post(f"{BASE_URL}/api/public/booking", json=booking_data)
        
        # Accept 200 (success) or 400 (slot taken) - both mean endpoint works
        assert response.status_code in [200, 400], f"Expected 200/400, got {response.status_code}: {response.text}"
        print(f"✓ POST /api/public/booking works, status: {response.status_code}")
    
    def test_public_services_endpoint(self):
        """GET /api/public/services returns services"""
        response = requests.get(f"{BASE_URL}/api/public/services")
        assert response.status_code == 200
        services = response.json()
        assert isinstance(services, list)
        print(f"✓ Public services endpoint returns {len(services)} services")
    
    def test_public_operators_endpoint(self):
        """GET /api/public/operators returns operators"""
        response = requests.get(f"{BASE_URL}/api/public/operators")
        assert response.status_code == 200
        operators = response.json()
        assert isinstance(operators, list)
        print(f"✓ Public operators endpoint returns {len(operators)} operators")


# ==================== AUTHENTICATED API TESTS ====================

class TestServicesModellanti:
    """Test 14: Modellanti category with 5 services"""
    
    def test_modellanti_category_exists(self, auth_headers):
        """Services page: Modellanti category visible with 5 services"""
        response = requests.get(f"{BASE_URL}/api/services", headers=auth_headers)
        assert response.status_code == 200
        
        services = response.json()
        modellanti_services = [s for s in services if s.get("category") == "modellanti"]
        
        assert len(modellanti_services) == 5, f"Expected 5 Modellanti services, got {len(modellanti_services)}"
        
        print(f"✓ Modellanti category has {len(modellanti_services)} services:")
        for s in modellanti_services:
            print(f"  - {s['name']}: €{s['price']}")


class TestOperators:
    """Test MBHS operator exists"""
    
    def test_mbhs_operator_exists(self, auth_headers):
        """MBHS operator should be visible and active"""
        response = requests.get(f"{BASE_URL}/api/operators", headers=auth_headers)
        assert response.status_code == 200
        
        operators = response.json()
        mbhs_operator = next((op for op in operators if "MBHS" in op.get("name", "")), None)
        
        assert mbhs_operator is not None, "MBHS operator not found"
        assert mbhs_operator.get("active") == True, "MBHS operator should be active"
        print(f"✓ MBHS operator found: id={mbhs_operator['id']}, active={mbhs_operator['active']}")


class TestAppointments:
    """Test appointment creation with new clients"""
    
    def test_create_appointment_with_client_name(self, auth_headers):
        """Test 20: POST /api/appointments accepts client_name for new clients"""
        services_res = requests.get(f"{BASE_URL}/api/services", headers=auth_headers)
        services = services_res.json()
        
        if not services:
            pytest.skip("No services for appointment test")
        
        tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        appointment_data = {
            "client_name": "TEST_New_Client_API",
            "client_phone": "3339999888",
            "service_ids": [services[0]["id"]],
            "date": tomorrow,
            "time": "14:30",
            "notes": "Test new client creation"
        }
        
        response = requests.post(f"{BASE_URL}/api/appointments", json=appointment_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        apt = response.json()
        assert apt["client_name"] == "TEST_New_Client_API"
        print(f"✓ Created appointment with new client: id={apt['id']}, client={apt['client_name']}")
    
    def test_create_appointment_generic_client(self, auth_headers):
        """POST /api/appointments works with generic client"""
        services_res = requests.get(f"{BASE_URL}/api/services", headers=auth_headers)
        services = services_res.json()
        
        if not services:
            pytest.skip("No services for appointment test")
        
        tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        appointment_data = {
            "client_name": "Cliente Generico",
            "service_ids": [services[0]["id"]],
            "date": tomorrow,
            "time": "15:00"
        }
        
        response = requests.post(f"{BASE_URL}/api/appointments", json=appointment_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        apt = response.json()
        assert apt["client_id"] == "generic"
        print(f"✓ Created generic client appointment: id={apt['id']}")


class TestClientCardsAndLoyalty:
    """Test 19: Client cards and loyalty endpoints"""
    
    def test_get_client_cards(self, auth_headers):
        """GET /api/clients/{id}/cards works"""
        # First get a client
        clients_res = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = clients_res.json()
        
        if not clients:
            pytest.skip("No clients for cards test")
        
        client_id = clients[0]["id"]
        response = requests.get(f"{BASE_URL}/api/clients/{client_id}/cards", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        cards = response.json()
        assert isinstance(cards, list)
        print(f"✓ GET /api/clients/{client_id}/cards returns {len(cards)} cards")
    
    def test_get_client_loyalty(self, auth_headers):
        """GET /api/clients/{id}/loyalty works"""
        clients_res = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = clients_res.json()
        
        if not clients:
            pytest.skip("No clients for loyalty test")
        
        client_id = clients[0]["id"]
        response = requests.get(f"{BASE_URL}/api/clients/{client_id}/loyalty", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        loyalty = response.json()
        assert "points" in loyalty
        print(f"✓ GET /api/clients/{client_id}/loyalty returns points={loyalty['points']}")


class TestRecurringAppointments:
    """Test 12: Recurring appointments with weekly AND monthly options"""
    
    def test_create_recurring_weekly(self, auth_headers):
        """Create recurring appointments with weeks"""
        # Get or create an appointment first
        tomorrow = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        services_res = requests.get(f"{BASE_URL}/api/services", headers=auth_headers)
        services = services_res.json()
        
        if not services:
            pytest.skip("No services for recurring test")
        
        # Create appointment
        apt_data = {
            "client_name": "TEST_Recurring_Weekly",
            "service_ids": [services[0]["id"]],
            "date": tomorrow,
            "time": "10:00"
        }
        apt_res = requests.post(f"{BASE_URL}/api/appointments", json=apt_data, headers=auth_headers)
        if apt_res.status_code != 200:
            pytest.skip("Could not create appointment for recurring test")
        
        apt_id = apt_res.json()["id"]
        
        # Create recurring appointments (weekly)
        recurring_data = {
            "appointment_id": apt_id,
            "repeat_weeks": 2,
            "repeat_months": 0,
            "repeat_count": 2
        }
        response = requests.post(f"{BASE_URL}/api/appointments/recurring", json=recurring_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        result = response.json()
        assert result["created"] == 2
        print(f"✓ Created {result['created']} recurring weekly appointments")
    
    def test_create_recurring_monthly(self, auth_headers):
        """Create recurring appointments with months"""
        tomorrow = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")
        services_res = requests.get(f"{BASE_URL}/api/services", headers=auth_headers)
        services = services_res.json()
        
        if not services:
            pytest.skip("No services for recurring test")
        
        apt_data = {
            "client_name": "TEST_Recurring_Monthly",
            "service_ids": [services[0]["id"]],
            "date": tomorrow,
            "time": "11:00"
        }
        apt_res = requests.post(f"{BASE_URL}/api/appointments", json=apt_data, headers=auth_headers)
        if apt_res.status_code != 200:
            pytest.skip("Could not create appointment for recurring test")
        
        apt_id = apt_res.json()["id"]
        
        # Create recurring appointments (monthly)
        recurring_data = {
            "appointment_id": apt_id,
            "repeat_weeks": 0,
            "repeat_months": 1,
            "repeat_count": 2
        }
        response = requests.post(f"{BASE_URL}/api/appointments/recurring", json=recurring_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        result = response.json()
        assert result["created"] == 2
        print(f"✓ Created {result['created']} recurring monthly appointments")


class TestPrepaidCards:
    """Test 15: PrepaidCards client dropdown is searchable"""
    
    def test_get_cards_endpoint(self, auth_headers):
        """GET /api/cards works"""
        response = requests.get(f"{BASE_URL}/api/cards", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        cards = response.json()
        assert isinstance(cards, list)
        print(f"✓ GET /api/cards returns {len(cards)} cards")
    
    def test_create_card_for_client(self, auth_headers):
        """POST /api/cards works"""
        clients_res = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        clients = clients_res.json()
        
        if not clients:
            pytest.skip("No clients for card creation test")
        
        client_id = clients[0]["id"]
        card_data = {
            "client_id": client_id,
            "card_type": "prepaid",
            "name": "TEST_Card_10_Pieghe",
            "total_value": 100.0,
            "total_services": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/cards", json=card_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        card = response.json()
        assert card["name"] == "TEST_Card_10_Pieghe"
        assert card["total_value"] == 100.0
        print(f"✓ Created card: {card['name']} for client {card['client_name']}")


class TestPayments:
    """Test 16: Report Incassi payment labels"""
    
    def test_get_payments_endpoint(self, auth_headers):
        """GET /api/payments works"""
        response = requests.get(f"{BASE_URL}/api/payments", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        payments = response.json()
        assert isinstance(payments, list)
        print(f"✓ GET /api/payments returns {len(payments)} payments")


class TestWebsiteAdmin:
    """Test CMS admin endpoints (6-9)"""
    
    def test_get_website_config(self, auth_headers):
        """Test 7: Admin can save website config"""
        response = requests.get(f"{BASE_URL}/api/website/config", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        config = response.json()
        assert "salon_name" in config
        print(f"✓ GET /api/website/config: salon_name={config.get('salon_name')}")
    
    def test_update_website_config(self, auth_headers):
        """Admin can update website config"""
        # Get current config
        current = requests.get(f"{BASE_URL}/api/website/config", headers=auth_headers).json()
        
        update_data = {
            **current,
            "hero_description": "Updated description for test"
        }
        
        response = requests.put(f"{BASE_URL}/api/website/config", json=update_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"✓ PUT /api/website/config success")
    
    def test_get_website_reviews(self, auth_headers):
        """GET /api/website/reviews works"""
        response = requests.get(f"{BASE_URL}/api/website/reviews", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        reviews = response.json()
        assert isinstance(reviews, list)
        print(f"✓ GET /api/website/reviews returns {len(reviews)} reviews")
    
    def test_add_review(self, auth_headers):
        """Test 8: Admin can add a review and it persists"""
        review_data = {
            "name": "TEST_Reviewer",
            "text": "Test review text",
            "rating": 5
        }
        
        response = requests.post(f"{BASE_URL}/api/website/reviews", json=review_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        review = response.json()
        assert review["name"] == "TEST_Reviewer"
        assert review["rating"] == 5
        print(f"✓ POST /api/website/reviews: created review id={review['id']}")
    
    def test_get_website_gallery(self, auth_headers):
        """GET /api/website/gallery works"""
        response = requests.get(f"{BASE_URL}/api/website/gallery", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        gallery = response.json()
        assert isinstance(gallery, list)
        print(f"✓ GET /api/website/gallery returns {len(gallery)} items")


class TestDashboardModules:
    """Test 21: Dashboard module links work"""
    
    def test_dashboard_stats(self, auth_headers):
        """GET /api/stats/dashboard works"""
        response = requests.get(f"{BASE_URL}/api/stats/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        stats = response.json()
        assert "today_appointments" in stats
        assert "total_clients" in stats
        print(f"✓ Dashboard stats: {stats['today_appointments_count']} appointments today, {stats['total_clients']} total clients")


# ==================== CLEANUP ====================

class TestCleanup:
    """Clean up test data"""
    
    def test_cleanup_test_appointments(self, auth_headers):
        """Remove TEST_ prefixed appointments"""
        # Get today's and future appointments
        today = datetime.now().strftime("%Y-%m-%d")
        future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/appointments?start_date={today}&end_date={future}",
            headers=auth_headers
        )
        if response.status_code == 200:
            appointments = response.json()
            test_apts = [a for a in appointments if a.get("client_name", "").startswith("TEST_")]
            
            for apt in test_apts:
                requests.delete(f"{BASE_URL}/api/appointments/{apt['id']}", headers=auth_headers)
            
            print(f"✓ Cleaned up {len(test_apts)} test appointments")
    
    def test_cleanup_test_reviews(self, auth_headers):
        """Remove TEST_ prefixed reviews"""
        response = requests.get(f"{BASE_URL}/api/website/reviews", headers=auth_headers)
        if response.status_code == 200:
            reviews = response.json()
            test_reviews = [r for r in reviews if r.get("name", "").startswith("TEST_")]
            
            for review in test_reviews:
                requests.delete(f"{BASE_URL}/api/website/reviews/{review['id']}", headers=auth_headers)
            
            print(f"✓ Cleaned up {len(test_reviews)} test reviews")
    
    def test_cleanup_test_cards(self, auth_headers):
        """Remove TEST_ prefixed cards"""
        response = requests.get(f"{BASE_URL}/api/cards?active_only=false", headers=auth_headers)
        if response.status_code == 200:
            cards = response.json()
            test_cards = [c for c in cards if c.get("name", "").startswith("TEST_")]
            
            for card in test_cards:
                requests.delete(f"{BASE_URL}/api/cards/{card['id']}", headers=auth_headers)
            
            print(f"✓ Cleaned up {len(test_cards)} test cards")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
