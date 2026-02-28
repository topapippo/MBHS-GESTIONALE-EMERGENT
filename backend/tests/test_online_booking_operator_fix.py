"""
Test suite for the online booking operator auto-assign bug fix.
Bug: Appointments booked via public booking page without selecting an operator
     were not displayed in daily planning grid view (but appeared in weekly/monthly views).
Fix: 
  1) Backend auto-assigns first active operator when none selected in public booking
  2) Frontend adds 'Non assegnato' column as safety net
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestOnlineBookingOperatorAutoAssign:
    """Test the fix for online appointments not appearing in daily planning"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get active operators for verification
        ops_res = requests.get(f"{BASE_URL}/api/operators", headers=self.headers)
        self.operators = [op for op in ops_res.json() if op.get("active", True)]
        
        # Get services for booking
        services_res = requests.get(f"{BASE_URL}/api/public/services")
        self.services = services_res.json()
        
    def test_public_booking_without_operator_gets_auto_assigned(self):
        """
        CRITICAL TEST: When booking via public page WITHOUT selecting operator,
        the appointment should be auto-assigned to first active operator
        """
        if not self.services:
            pytest.skip("No services available")
            
        # Create booking without operator_id
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        unique_name = f"TEST_AutoAssign_{uuid.uuid4().hex[:6]}"
        unique_phone = f"3331234{uuid.uuid4().hex[:4]}"
        
        booking_data = {
            "client_name": unique_name,
            "client_phone": unique_phone,
            "service_ids": [self.services[0]["id"]],
            "operator_id": "",  # Empty - no operator selected
            "date": tomorrow,
            "time": "10:00",
            "notes": "Testing auto-assign fix"
        }
        
        # Create public booking
        response = requests.post(f"{BASE_URL}/api/public/booking", json=booking_data)
        assert response.status_code == 200, f"Public booking failed: {response.text}"
        
        booking_result = response.json()
        assert booking_result.get("success") == True
        appointment_id = booking_result.get("appointment_id")
        assert appointment_id, "No appointment_id returned"
        
        # Verify the appointment has an operator_id assigned
        apt_response = requests.get(
            f"{BASE_URL}/api/appointments/{appointment_id}", 
            headers=self.headers
        )
        assert apt_response.status_code == 200, f"Failed to get appointment: {apt_response.text}"
        
        appointment = apt_response.json()
        
        # KEY ASSERTION: operator_id should NOT be null/empty
        assert appointment.get("operator_id"), \
            "BUG: Appointment has no operator_id - it won't appear in daily planning!"
        
        # Verify it's one of the active operators
        if self.operators:
            operator_ids = [op["id"] for op in self.operators]
            assert appointment["operator_id"] in operator_ids, \
                f"Assigned operator {appointment['operator_id']} is not in active operators list"
        
        # Verify operator_name and operator_color are also set
        assert appointment.get("operator_name"), "operator_name should be set"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{appointment_id}", headers=self.headers)
        print(f"✓ Public booking without operator correctly auto-assigned to: {appointment.get('operator_name')}")
    
    def test_public_booking_with_operator_keeps_selected_operator(self):
        """Verify explicit operator selection still works correctly"""
        if not self.services or not self.operators:
            pytest.skip("No services or operators available")
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        unique_name = f"TEST_ExplicitOp_{uuid.uuid4().hex[:6]}"
        unique_phone = f"3332345{uuid.uuid4().hex[:4]}"
        selected_operator = self.operators[0]
        
        booking_data = {
            "client_name": unique_name,
            "client_phone": unique_phone,
            "service_ids": [self.services[0]["id"]],
            "operator_id": selected_operator["id"],  # Explicitly selected
            "date": tomorrow,
            "time": "11:00",
            "notes": "Testing explicit operator selection"
        }
        
        response = requests.post(f"{BASE_URL}/api/public/booking", json=booking_data)
        assert response.status_code == 200, f"Public booking failed: {response.text}"
        
        appointment_id = response.json().get("appointment_id")
        
        # Verify the explicitly selected operator was kept
        apt_response = requests.get(
            f"{BASE_URL}/api/appointments/{appointment_id}", 
            headers=self.headers
        )
        appointment = apt_response.json()
        
        assert appointment["operator_id"] == selected_operator["id"], \
            "Explicit operator selection was not preserved"
        assert appointment["operator_name"] == selected_operator["name"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{appointment_id}", headers=self.headers)
        print(f"✓ Explicit operator selection preserved: {selected_operator['name']}")
    
    def test_appointments_appear_in_daily_view_query(self):
        """Verify appointments with operators appear when querying by date"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        unique_name = f"TEST_DailyView_{uuid.uuid4().hex[:6]}"
        unique_phone = f"3333456{uuid.uuid4().hex[:4]}"
        
        if not self.services:
            pytest.skip("No services available")
        
        # Create a public booking without operator
        booking_data = {
            "client_name": unique_name,
            "client_phone": unique_phone,
            "service_ids": [self.services[0]["id"]],
            "operator_id": "",
            "date": tomorrow,
            "time": "14:00",
            "notes": ""
        }
        
        response = requests.post(f"{BASE_URL}/api/public/booking", json=booking_data)
        assert response.status_code == 200
        appointment_id = response.json().get("appointment_id")
        
        # Query appointments for that date (simulating daily view)
        daily_response = requests.get(
            f"{BASE_URL}/api/appointments?date={tomorrow}",
            headers=self.headers
        )
        assert daily_response.status_code == 200
        
        daily_appointments = daily_response.json()
        
        # Find our appointment in the daily list
        our_apt = next((a for a in daily_appointments if a["id"] == appointment_id), None)
        assert our_apt, "Appointment not found in daily view query!"
        
        # Verify it has operator_id (critical for daily grid rendering)
        assert our_apt.get("operator_id"), \
            "BUG: Appointment in daily view has no operator_id - it won't render in grid!"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{appointment_id}", headers=self.headers)
        print(f"✓ Appointment appears in daily view with operator_id: {our_apt.get('operator_id')}")


class TestInternalAppointmentCreation:
    """Verify internal appointment creation still works correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get operators and services
        ops_res = requests.get(f"{BASE_URL}/api/operators", headers=self.headers)
        self.operators = [op for op in ops_res.json() if op.get("active", True)]
        
        services_res = requests.get(f"{BASE_URL}/api/services", headers=self.headers)
        self.services = services_res.json()
        
        clients_res = requests.get(f"{BASE_URL}/api/clients", headers=self.headers)
        self.clients = clients_res.json()
    
    def test_internal_appointment_with_operator(self):
        """Create appointment from planning page with operator selected"""
        if not self.services or not self.operators or not self.clients:
            pytest.skip("Missing required data")
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        apt_data = {
            "client_id": self.clients[0]["id"],
            "service_ids": [self.services[0]["id"]],
            "operator_id": self.operators[0]["id"],
            "date": tomorrow,
            "time": "15:00",
            "notes": "Internal appointment test"
        }
        
        response = requests.post(f"{BASE_URL}/api/appointments", json=apt_data, headers=self.headers)
        assert response.status_code == 200, f"Failed to create appointment: {response.text}"
        
        appointment = response.json()
        assert appointment["operator_id"] == self.operators[0]["id"]
        assert appointment["operator_name"] == self.operators[0]["name"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{appointment['id']}", headers=self.headers)
        print(f"✓ Internal appointment creation works with operator: {appointment['operator_name']}")
    
    def test_internal_appointment_without_operator(self):
        """Create appointment from planning page without operator - should allow null"""
        if not self.services or not self.clients:
            pytest.skip("Missing required data")
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        apt_data = {
            "client_id": self.clients[0]["id"],
            "service_ids": [self.services[0]["id"]],
            "operator_id": None,  # No operator
            "date": tomorrow,
            "time": "16:00",
            "notes": "Internal appointment without operator"
        }
        
        response = requests.post(f"{BASE_URL}/api/appointments", json=apt_data, headers=self.headers)
        assert response.status_code == 200, f"Failed to create appointment: {response.text}"
        
        appointment = response.json()
        # Note: Internal appointments CAN have null operator (different from public booking fix)
        # The frontend 'Non assegnato' column catches these
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{appointment['id']}", headers=self.headers)
        print(f"✓ Internal appointment creation works without operator (operator_id: {appointment.get('operator_id')})")


class TestAppointmentUpdateAndDelete:
    """Test editing and deleting appointments from planning view"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        ops_res = requests.get(f"{BASE_URL}/api/operators", headers=self.headers)
        self.operators = [op for op in ops_res.json() if op.get("active", True)]
        
        services_res = requests.get(f"{BASE_URL}/api/services", headers=self.headers)
        self.services = services_res.json()
        
        clients_res = requests.get(f"{BASE_URL}/api/clients", headers=self.headers)
        self.clients = clients_res.json()
    
    def test_update_appointment_time(self):
        """Update appointment time from edit dialog"""
        if not self.services or not self.clients:
            pytest.skip("Missing required data")
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create appointment
        apt_data = {
            "client_id": self.clients[0]["id"],
            "service_ids": [self.services[0]["id"]],
            "operator_id": self.operators[0]["id"] if self.operators else None,
            "date": tomorrow,
            "time": "09:00",
            "notes": ""
        }
        create_res = requests.post(f"{BASE_URL}/api/appointments", json=apt_data, headers=self.headers)
        assert create_res.status_code == 200
        apt_id = create_res.json()["id"]
        
        # Update time
        update_res = requests.put(
            f"{BASE_URL}/api/appointments/{apt_id}",
            json={"time": "10:30"},
            headers=self.headers
        )
        assert update_res.status_code == 200, f"Update failed: {update_res.text}"
        
        updated_apt = update_res.json()
        assert updated_apt["time"] == "10:30"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{apt_id}", headers=self.headers)
        print(f"✓ Appointment time updated: 09:00 -> 10:30")
    
    def test_update_appointment_operator(self):
        """Update appointment operator from edit dialog"""
        if not self.services or not self.clients or len(self.operators) < 2:
            pytest.skip("Need at least 2 operators for this test")
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Create with first operator
        apt_data = {
            "client_id": self.clients[0]["id"],
            "service_ids": [self.services[0]["id"]],
            "operator_id": self.operators[0]["id"],
            "date": tomorrow,
            "time": "11:00",
            "notes": ""
        }
        create_res = requests.post(f"{BASE_URL}/api/appointments", json=apt_data, headers=self.headers)
        apt_id = create_res.json()["id"]
        
        # Update to second operator
        update_res = requests.put(
            f"{BASE_URL}/api/appointments/{apt_id}",
            json={"operator_id": self.operators[1]["id"]},
            headers=self.headers
        )
        assert update_res.status_code == 200
        
        updated_apt = update_res.json()
        assert updated_apt["operator_id"] == self.operators[1]["id"]
        assert updated_apt["operator_name"] == self.operators[1]["name"]
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{apt_id}", headers=self.headers)
        print(f"✓ Appointment operator updated: {self.operators[0]['name']} -> {self.operators[1]['name']}")
    
    def test_delete_appointment(self):
        """Delete appointment from planning view"""
        if not self.services or not self.clients:
            pytest.skip("Missing required data")
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        apt_data = {
            "client_id": self.clients[0]["id"],
            "service_ids": [self.services[0]["id"]],
            "operator_id": self.operators[0]["id"] if self.operators else None,
            "date": tomorrow,
            "time": "12:00",
            "notes": "To be deleted"
        }
        create_res = requests.post(f"{BASE_URL}/api/appointments", json=apt_data, headers=self.headers)
        apt_id = create_res.json()["id"]
        
        # Delete
        delete_res = requests.delete(f"{BASE_URL}/api/appointments/{apt_id}", headers=self.headers)
        assert delete_res.status_code == 200, f"Delete failed: {delete_res.text}"
        
        # Verify deletion
        get_res = requests.get(f"{BASE_URL}/api/appointments/{apt_id}", headers=self.headers)
        assert get_res.status_code == 404, "Appointment should be deleted"
        
        print(f"✓ Appointment deleted successfully")


class TestWeeklyAndMonthlyViews:
    """Verify weekly and monthly views still work correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_weekly_view_with_date_range(self):
        """Query appointments with date range (weekly view simulation)"""
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        response = requests.get(
            f"{BASE_URL}/api/appointments?start_date={start_of_week.strftime('%Y-%m-%d')}&end_date={end_of_week.strftime('%Y-%m-%d')}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Weekly query failed: {response.text}"
        
        appointments = response.json()
        print(f"✓ Weekly view query returned {len(appointments)} appointments")
    
    def test_monthly_view_with_date_range(self):
        """Query appointments with date range (monthly view simulation)"""
        today = datetime.now()
        start_of_month = today.replace(day=1)
        # Get last day of month
        next_month = start_of_month.replace(day=28) + timedelta(days=4)
        end_of_month = next_month.replace(day=1) - timedelta(days=1)
        
        response = requests.get(
            f"{BASE_URL}/api/appointments?start_date={start_of_month.strftime('%Y-%m-%d')}&end_date={end_of_month.strftime('%Y-%m-%d')}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Monthly query failed: {response.text}"
        
        appointments = response.json()
        print(f"✓ Monthly view query returned {len(appointments)} appointments")


class TestLoginFlow:
    """Verify login flow works correctly"""
    
    def test_login_valid_credentials(self):
        """Login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "melitobruno@gmail.com"
        print(f"✓ Login successful for {data['user']['email']}")
    
    def test_login_invalid_credentials(self):
        """Login with invalid credentials should fail"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, "Should fail with wrong password"
        print("✓ Invalid login correctly rejected")
