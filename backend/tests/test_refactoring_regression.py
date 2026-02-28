"""
Comprehensive Regression Test Suite for MBHS SALON Backend Refactoring
Tests ALL API endpoints to ensure the modular refactoring didn't break anything.
The backend was refactored from a monolithic 3314-line server.py into:
- server.py (53 lines)
- database.py, auth.py, models.py, utils.py
- 14 route files under routes/
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hair-salon-portal-1.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "melitobruno@gmail.com"
TEST_PASSWORD = "password123"


class TestAPIRoot:
    """Test the root API endpoint"""
    
    def test_api_root(self):
        """Test /api/ returns ok status"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✓ API root endpoint working")


class TestAuthEndpoints:
    """Test authentication endpoints - routes/auth.py"""
    
    def test_login_valid_credentials(self):
        """Test POST /api/auth/login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        print("✓ Login endpoint working")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test POST /api/auth/login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("✓ Login rejects invalid credentials")
    
    def test_get_me(self):
        """Test GET /api/auth/me with valid token"""
        token = self.test_login_valid_credentials()
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        print("✓ Get current user endpoint working")


@pytest.fixture(scope="class")
def auth_headers():
    """Get auth headers for authenticated requests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestOperatorsEndpoints:
    """Test operator endpoints - routes/operators.py"""
    
    @pytest.fixture(autouse=True)
    def setup(self, auth_headers):
        self.headers = auth_headers
    
    def test_get_operators(self, auth_headers):
        """Test GET /api/operators"""
        response = requests.get(f"{BASE_URL}/api/operators", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Get operators - found {len(data)} operators")
    
    def test_create_update_delete_operator(self, auth_headers):
        """Test full CRUD for operators"""
        # Create
        create_data = {"name": f"TEST_Operator_{uuid.uuid4().hex[:6]}", "phone": "1234567890", "color": "#FF5733"}
        response = requests.post(f"{BASE_URL}/api/operators", json=create_data, headers=auth_headers)
        assert response.status_code == 200
        created = response.json()
        operator_id = created["id"]
        assert created["name"] == create_data["name"]
        print(f"✓ Created operator: {operator_id}")
        
        # Update
        response = requests.put(f"{BASE_URL}/api/operators/{operator_id}", 
                              json={"name": "TEST_Updated_Operator"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "TEST_Updated_Operator"
        print("✓ Updated operator")
        
        # Delete
        response = requests.delete(f"{BASE_URL}/api/operators/{operator_id}", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Deleted operator")


class TestClientsEndpoints:
    """Test client endpoints - routes/clients.py"""
    
    def test_get_clients(self, auth_headers):
        """Test GET /api/clients"""
        response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Get clients - found {len(data)} clients")
    
    def test_create_update_delete_client(self, auth_headers):
        """Test full CRUD for clients"""
        # Create
        create_data = {"name": f"TEST_Client_{uuid.uuid4().hex[:6]}", "phone": "3331234567", "email": "test@test.com"}
        response = requests.post(f"{BASE_URL}/api/clients", json=create_data, headers=auth_headers)
        assert response.status_code == 200
        created = response.json()
        client_id = created["id"]
        assert created["name"] == create_data["name"]
        print(f"✓ Created client: {client_id}")
        
        # Get single client
        response = requests.get(f"{BASE_URL}/api/clients/{client_id}", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get single client")
        
        # Update
        response = requests.put(f"{BASE_URL}/api/clients/{client_id}", 
                              json={"name": "TEST_Updated_Client"}, headers=auth_headers)
        assert response.status_code == 200
        print("✓ Updated client")
        
        # Get client history
        response = requests.get(f"{BASE_URL}/api/clients/{client_id}/history", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get client history")
        
        # Get client cards
        response = requests.get(f"{BASE_URL}/api/clients/{client_id}/cards", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get client cards")
        
        # Get client loyalty
        response = requests.get(f"{BASE_URL}/api/clients/{client_id}/loyalty", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get client loyalty")
        
        # Delete
        response = requests.delete(f"{BASE_URL}/api/clients/{client_id}", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Deleted client")
    
    def test_search_client_appointments(self, auth_headers):
        """Test GET /api/clients/search/appointments"""
        response = requests.get(f"{BASE_URL}/api/clients/search/appointments?query=bruno", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Search client appointments")


class TestServicesEndpoints:
    """Test service endpoints - routes/services.py"""
    
    def test_get_services(self, auth_headers):
        """Test GET /api/services"""
        response = requests.get(f"{BASE_URL}/api/services", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have default services
        print(f"✓ Get services - found {len(data)} services")
    
    def test_create_update_delete_service(self, auth_headers):
        """Test full CRUD for services"""
        # Create
        create_data = {"name": f"TEST_Service_{uuid.uuid4().hex[:6]}", "category": "test", "duration": 30, "price": 25.0}
        response = requests.post(f"{BASE_URL}/api/services", json=create_data, headers=auth_headers)
        assert response.status_code == 200
        created = response.json()
        service_id = created["id"]
        print(f"✓ Created service: {service_id}")
        
        # Update
        response = requests.put(f"{BASE_URL}/api/services/{service_id}", 
                              json={"price": 30.0}, headers=auth_headers)
        assert response.status_code == 200
        print("✓ Updated service")
        
        # Delete
        response = requests.delete(f"{BASE_URL}/api/services/{service_id}", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Deleted service")


class TestAppointmentsEndpoints:
    """Test appointment endpoints - routes/appointments.py"""
    
    def test_get_appointments(self, auth_headers):
        """Test GET /api/appointments with date filter"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/appointments?date={today}", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Get appointments for {today}")
    
    def test_get_appointments_date_range(self, auth_headers):
        """Test GET /api/appointments with date range"""
        start = datetime.now().strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/appointments?start_date={start}&end_date={end}", headers=auth_headers)
        assert response.status_code == 200
        print(f"✓ Get appointments for date range {start} to {end}")
    
    def test_create_and_manage_appointment(self, auth_headers):
        """Test full appointment lifecycle"""
        # Get a service first
        services_resp = requests.get(f"{BASE_URL}/api/services", headers=auth_headers)
        services = services_resp.json()
        if not services:
            pytest.skip("No services available")
        service_id = services[0]["id"]
        
        # Get an operator
        operators_resp = requests.get(f"{BASE_URL}/api/operators", headers=auth_headers)
        operators = operators_resp.json()
        operator_id = operators[0]["id"] if operators else None
        
        # Create appointment
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        create_data = {
            "client_name": f"TEST_AppClient_{uuid.uuid4().hex[:4]}",
            "client_phone": "3339999999",
            "service_ids": [service_id],
            "operator_id": operator_id,
            "date": tomorrow,
            "time": "14:00",
            "notes": "Test appointment"
        }
        response = requests.post(f"{BASE_URL}/api/appointments", json=create_data, headers=auth_headers)
        assert response.status_code == 200
        created = response.json()
        apt_id = created["id"]
        print(f"✓ Created appointment: {apt_id}")
        
        # Get single appointment
        response = requests.get(f"{BASE_URL}/api/appointments/{apt_id}", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get single appointment")
        
        # Update appointment
        response = requests.put(f"{BASE_URL}/api/appointments/{apt_id}", 
                              json={"time": "15:00"}, headers=auth_headers)
        assert response.status_code == 200
        print("✓ Updated appointment")
        
        # Delete appointment
        response = requests.delete(f"{BASE_URL}/api/appointments/{apt_id}", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Deleted appointment")


class TestCardsEndpoints:
    """Test prepaid card endpoints - routes/cards.py"""
    
    def test_get_cards(self, auth_headers):
        """Test GET /api/cards"""
        response = requests.get(f"{BASE_URL}/api/cards", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get prepaid cards")
    
    def test_get_card_templates(self, auth_headers):
        """Test GET /api/card-templates"""
        response = requests.get(f"{BASE_URL}/api/card-templates", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get card templates")


class TestStatsEndpoints:
    """Test stats and settings endpoints - routes/stats.py"""
    
    def test_get_dashboard(self, auth_headers):
        """Test GET /api/stats/dashboard"""
        response = requests.get(f"{BASE_URL}/api/stats/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "today_appointments" in data
        assert "total_clients" in data
        print("✓ Get dashboard stats")
    
    def test_get_daily_summary(self, auth_headers):
        """Test GET /api/stats/daily-summary"""
        response = requests.get(f"{BASE_URL}/api/stats/daily-summary", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get daily summary")
    
    def test_get_revenue_stats(self, auth_headers):
        """Test GET /api/stats/revenue"""
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/stats/revenue?start_date={start}&end_date={end}", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get revenue stats")
    
    def test_get_settings(self, auth_headers):
        """Test GET /api/settings"""
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "salon_name" in data
        print("✓ Get settings")
    
    def test_get_payments(self, auth_headers):
        """Test GET /api/payments"""
        response = requests.get(f"{BASE_URL}/api/payments", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get payments")


class TestRemindersEndpoints:
    """Test reminders endpoints - routes/reminders.py"""
    
    def test_get_sms_status(self, auth_headers):
        """Test GET /api/sms/status"""
        response = requests.get(f"{BASE_URL}/api/sms/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        print("✓ Get SMS status")
    
    def test_get_tomorrow_reminders(self, auth_headers):
        """Test GET /api/reminders/tomorrow"""
        response = requests.get(f"{BASE_URL}/api/reminders/tomorrow", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get tomorrow reminders")
    
    def test_get_auto_reminder_check(self, auth_headers):
        """Test GET /api/reminders/auto-check"""
        response = requests.get(f"{BASE_URL}/api/reminders/auto-check", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "is_reminder_time" in data
        print("✓ Get auto reminder check")
    
    def test_get_color_expiry_reminders(self, auth_headers):
        """Test GET /api/reminders/color-expiry"""
        response = requests.get(f"{BASE_URL}/api/reminders/color-expiry", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get color expiry reminders")
    
    def test_get_inactive_clients(self, auth_headers):
        """Test GET /api/reminders/inactive-clients"""
        response = requests.get(f"{BASE_URL}/api/reminders/inactive-clients", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get inactive clients")
    
    def test_get_message_templates(self, auth_headers):
        """Test GET /api/reminders/templates"""
        response = requests.get(f"{BASE_URL}/api/reminders/templates", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get message templates")


class TestLoyaltyEndpoints:
    """Test loyalty endpoints - routes/loyalty.py"""
    
    def test_get_all_loyalty(self, auth_headers):
        """Test GET /api/loyalty"""
        response = requests.get(f"{BASE_URL}/api/loyalty", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get all loyalty records")
    
    def test_get_loyalty_config(self, auth_headers):
        """Test GET /api/loyalty/config"""
        response = requests.get(f"{BASE_URL}/api/loyalty/config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "points_per_euro" in data
        assert "rewards" in data
        print("✓ Get loyalty config")


class TestExpensesEndpoints:
    """Test expenses endpoints - routes/expenses.py"""
    
    def test_get_expenses(self, auth_headers):
        """Test GET /api/expenses"""
        response = requests.get(f"{BASE_URL}/api/expenses", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get expenses")
    
    def test_get_upcoming_expenses(self, auth_headers):
        """Test GET /api/expenses/upcoming"""
        response = requests.get(f"{BASE_URL}/api/expenses/upcoming", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get upcoming expenses")
    
    def test_create_update_delete_expense(self, auth_headers):
        """Test full CRUD for expenses"""
        # Create
        create_data = {
            "description": f"TEST_Expense_{uuid.uuid4().hex[:6]}",
            "amount": 100.0,
            "category": "test",
            "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        response = requests.post(f"{BASE_URL}/api/expenses", json=create_data, headers=auth_headers)
        assert response.status_code == 200
        created = response.json()
        expense_id = created["id"]
        print(f"✓ Created expense: {expense_id}")
        
        # Update
        response = requests.put(f"{BASE_URL}/api/expenses/{expense_id}", 
                              json={"amount": 150.0}, headers=auth_headers)
        assert response.status_code == 200
        print("✓ Updated expense")
        
        # Delete
        response = requests.delete(f"{BASE_URL}/api/expenses/{expense_id}", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Deleted expense")


class TestPromotionsEndpoints:
    """Test promotions endpoints - routes/promotions.py"""
    
    def test_get_promotions(self, auth_headers):
        """Test GET /api/promotions"""
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Get promotions - found {len(data)} promotions")
    
    def test_public_promotions(self):
        """Test GET /api/public/promotions/all"""
        response = requests.get(f"{BASE_URL}/api/public/promotions/all")
        assert response.status_code == 200
        print("✓ Get public promotions")


class TestNotificationsEndpoints:
    """Test notifications endpoints - routes/notifications.py"""
    
    def test_get_new_bookings(self, auth_headers):
        """Test GET /api/notifications/new-bookings"""
        response = requests.get(f"{BASE_URL}/api/notifications/new-bookings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Get new bookings - found {len(data)} online bookings")
    
    def test_mark_bookings_seen(self, auth_headers):
        """Test POST /api/notifications/mark-seen"""
        response = requests.post(f"{BASE_URL}/api/notifications/mark-seen", 
                               json={"appointment_ids": []}, headers=auth_headers)
        assert response.status_code == 200
        print("✓ Mark bookings seen")


class TestPublicEndpoints:
    """Test public booking endpoints - routes/public.py"""
    
    def test_get_public_services(self):
        """Test GET /api/public/services"""
        response = requests.get(f"{BASE_URL}/api/public/services")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Get public services - found {len(data)} services")
    
    def test_get_public_operators(self):
        """Test GET /api/public/operators"""
        response = requests.get(f"{BASE_URL}/api/public/operators")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Get public operators - found {len(data)} operators")
    
    def test_public_booking_flow(self):
        """Test public booking creation"""
        # Get services
        services_resp = requests.get(f"{BASE_URL}/api/public/services")
        services = services_resp.json()
        if not services:
            pytest.skip("No public services available")
        service_id = services[0]["id"]
        
        # Create booking
        tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        booking_data = {
            "client_name": f"TEST_PublicClient_{uuid.uuid4().hex[:4]}",
            "client_phone": "3339998877",
            "service_ids": [service_id],
            "date": tomorrow,
            "time": "16:00",
            "notes": "Test public booking"
        }
        response = requests.post(f"{BASE_URL}/api/public/booking", json=booking_data)
        # May fail due to time slot conflict, but endpoint should be accessible
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            print("✓ Public booking created")
        else:
            print("✓ Public booking endpoint accessible (slot may be taken)")
    
    def test_lookup_my_appointments(self):
        """Test GET /api/public/my-appointments"""
        response = requests.get(f"{BASE_URL}/api/public/my-appointments?phone=3339998877")
        assert response.status_code == 200
        print("✓ Public my-appointments lookup")


class TestWebsiteCMSEndpoints:
    """Test website CMS endpoints - routes/public.py"""
    
    def test_get_website_config(self, auth_headers):
        """Test GET /api/website/config"""
        response = requests.get(f"{BASE_URL}/api/website/config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "salon_name" in data
        print("✓ Get website config")
    
    def test_get_website_gallery(self, auth_headers):
        """Test GET /api/website/gallery"""
        response = requests.get(f"{BASE_URL}/api/website/gallery", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get website gallery")
    
    def test_get_website_reviews(self, auth_headers):
        """Test GET /api/website/reviews"""
        response = requests.get(f"{BASE_URL}/api/website/reviews", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Get website reviews")
    
    def test_public_website(self):
        """Test GET /api/public/website"""
        response = requests.get(f"{BASE_URL}/api/public/website")
        assert response.status_code == 200
        data = response.json()
        assert "config" in data
        assert "gallery" in data
        assert "reviews" in data
        print("✓ Get public website data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
