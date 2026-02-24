import requests
import sys
import json
from datetime import datetime

class HairSalonAPITester:
    def __init__(self, base_url="https://hair-salon-portal-1.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.client_id = None
        self.service_id = None
        self.appointment_id = None
        self.operator_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, auth=True):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.content:
                    try:
                        error_data = response.json()
                        print(f"   Error: {error_data}")
                    except:
                        print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic API health"""
        return self.run_test("Health Check", "GET", "", 200, auth=False)

    def test_register(self):
        """Test user registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        register_data = {
            "email": f"test_salon_{timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test Salon Owner",
            "salon_name": "Test Hair Salon"
        }
        
        success, response = self.run_test(
            "User Registration", 
            "POST", 
            "auth/register", 
            200, 
            register_data, 
            auth=False
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Token acquired: {self.token[:20]}...")
            return True
        return False

    def test_login(self):
        """Test user login"""
        # Use existing credentials for login test
        login_data = {
            "email": "test_salon_owner@test.com", 
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Login", 
            "POST", 
            "auth/login", 
            200, 
            login_data, 
            auth=False
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_get_profile(self):
        """Test get user profile"""
        return self.run_test("Get Profile", "GET", "auth/me", 200)

    def test_create_client(self):
        """Test creating a client"""
        client_data = {
            "name": "Maria Rossi",
            "phone": "+39 123 456 7890",
            "email": "maria.rossi@test.com",
            "notes": "Cliente VIP - preferisce appuntamenti mattutini",
            "sms_reminder": True
        }
        
        success, response = self.run_test(
            "Create Client", 
            "POST", 
            "clients", 
            200, 
            client_data
        )
        
        if success and 'id' in response:
            self.client_id = response['id']
            print(f"   Client created: {self.client_id}")
            return True
        return False

    def test_get_clients(self):
        """Test getting all clients"""
        return self.run_test("Get Clients", "GET", "clients", 200)

    def test_get_client(self):
        """Test getting specific client"""
        if not self.client_id:
            print("❌ No client ID available")
            return False
        return self.run_test("Get Single Client", "GET", f"clients/{self.client_id}", 200)

    def test_update_client(self):
        """Test updating a client"""
        if not self.client_id:
            print("❌ No client ID available")
            return False
            
        update_data = {
            "notes": "Cliente VIP - aggiornata preferenza orario serale"
        }
        
        return self.run_test(
            "Update Client", 
            "PUT", 
            f"clients/{self.client_id}", 
            200, 
            update_data
        )

    def test_get_services(self):
        """Test getting all services"""
        success, response = self.run_test("Get Services", "GET", "services", 200)
        
        # Store first service ID for appointment tests
        if success and response and len(response) > 0:
            self.service_id = response[0]['id']
            print(f"   Using service ID: {self.service_id}")
        
        return success

    def test_create_service(self):
        """Test creating a service"""
        service_data = {
            "name": "Taglio Test",
            "category": "taglio", 
            "duration": 45,
            "price": 35.0
        }
        
        success, response = self.run_test(
            "Create Service", 
            "POST", 
            "services", 
            200, 
            service_data
        )
        
        if success and 'id' in response:
            # Update service_id to use the new one
            self.service_id = response['id']
            print(f"   Service created: {self.service_id}")
            return True
        return False

    def test_update_service(self):
        """Test updating a service"""
        if not self.service_id:
            print("❌ No service ID available")
            return False
            
        update_data = {
            "price": 40.0
        }
        
        return self.run_test(
            "Update Service", 
            "PUT", 
            f"services/{self.service_id}", 
            200, 
            update_data
        )

    def test_create_appointment(self):
        """Test creating an appointment"""
        if not self.client_id or not self.service_id:
            print("❌ Missing client ID or service ID")
            return False
            
        appointment_data = {
            "client_id": self.client_id,
            "service_ids": [self.service_id],
            "date": "2025-01-15",
            "time": "10:00",
            "notes": "Primo appuntamento di test"
        }
        
        success, response = self.run_test(
            "Create Appointment", 
            "POST", 
            "appointments", 
            200, 
            appointment_data
        )
        
        if success and 'id' in response:
            self.appointment_id = response['id']
            print(f"   Appointment created: {self.appointment_id}")
            return True
        return False

    def test_get_appointments(self):
        """Test getting appointments"""
        return self.run_test("Get Appointments", "GET", "appointments?date=2025-01-15", 200)

    def test_get_appointment(self):
        """Test getting specific appointment"""
        if not self.appointment_id:
            print("❌ No appointment ID available")
            return False
        return self.run_test("Get Single Appointment", "GET", f"appointments/{self.appointment_id}", 200)

    def test_update_appointment(self):
        """Test updating an appointment"""
        if not self.appointment_id:
            print("❌ No appointment ID available")
            return False
            
        update_data = {
            "status": "completed",
            "notes": "Appuntamento completato con successo"
        }
        
        return self.run_test(
            "Update Appointment", 
            "PUT", 
            f"appointments/{self.appointment_id}", 
            200, 
            update_data
        )

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        return self.run_test("Dashboard Stats", "GET", "stats/dashboard", 200)

    def test_revenue_stats(self):
        """Test revenue statistics"""
        return self.run_test(
            "Revenue Stats", 
            "GET", 
            "stats/revenue?start_date=2025-01-01&end_date=2025-01-31", 
            200
        )

    def test_get_settings(self):
        """Test getting settings"""
        return self.run_test("Get Settings", "GET", "settings", 200)

    def test_create_operator(self):
        """Test creating an operator"""
        operator_data = {
            "name": "Giulia Bianchi",
            "phone": "+39 987 654 3210",
            "color": "#789F8A"
        }
        
        success, response = self.run_test(
            "Create Operator", 
            "POST", 
            "operators", 
            200, 
            operator_data
        )
        
        if success and 'id' in response:
            self.operator_id = response['id']
            print(f"   Operator created: {self.operator_id}")
            return True
        return False

    def test_get_operators(self):
        """Test getting all operators"""
        return self.run_test("Get Operators", "GET", "operators", 200)

    def test_get_operator(self):
        """Test getting specific operator"""
        if not self.operator_id:
            print("❌ No operator ID available")
            return False
        return self.run_test("Get Single Operator", "GET", f"operators/{self.operator_id}", 200)

    def test_update_operator(self):
        """Test updating an operator"""
        if not self.operator_id:
            print("❌ No operator ID available")
            return False
            
        update_data = {
            "active": False
        }
        
        return self.run_test(
            "Update Operator (Toggle Active)", 
            "PUT", 
            f"operators/{self.operator_id}", 
            200, 
            update_data
        )

    def test_sms_status(self):
        """Test SMS status endpoint"""
        return self.run_test("SMS Status", "GET", "sms/status", 200)

    def test_send_sms_reminder(self):
        """Test sending SMS reminder (should fail if Twilio not configured)"""
        if not self.appointment_id:
            print("❌ No appointment ID available")
            return False
            
        sms_data = {
            "appointment_id": self.appointment_id,
            "message": "Test SMS reminder message"
        }
        
        # This should return 200 but with success=false if Twilio not configured
        success, response = self.run_test(
            "Send SMS Reminder", 
            "POST", 
            "sms/send-reminder", 
            200, 
            sms_data
        )
        
        if success:
            print(f"   SMS Result: {response}")
        
        return success

    def test_update_settings(self):
        """Test updating settings"""
        settings_data = {
            "salon_name": "Test Hair Salon Updated",
            "opening_time": "08:30",
            "closing_time": "20:00"
        }
        
        return self.run_test("Update Settings", "PUT", "settings", 200, settings_data)

    def test_create_appointment_with_operator(self):
        """Test creating an appointment with operator assignment"""
        if not self.client_id or not self.service_id or not self.operator_id:
            print("❌ Missing client ID, service ID, or operator ID")
            return False
            
        appointment_data = {
            "client_id": self.client_id,
            "service_ids": [self.service_id],
            "operator_id": self.operator_id,
            "date": "2025-01-16",
            "time": "14:00",
            "notes": "Appuntamento con operatore assegnato"
        }
        
        success, response = self.run_test(
            "Create Appointment with Operator", 
            "POST", 
            "appointments", 
            200, 
            appointment_data
        )
        
        if success and 'id' in response:
            print(f"   Appointment with operator created: {response['id']}")
            return True
        return False

    # Cleanup tests
    def test_delete_operator(self):
        """Test deleting an operator"""
        if not self.operator_id:
            print("❌ No operator ID available")
            return False
        return self.run_test("Delete Operator", "DELETE", f"operators/{self.operator_id}", 200)

    def test_delete_appointment(self):
        """Test deleting an appointment"""
        if not self.appointment_id:
            print("❌ No appointment ID available")
            return False
        return self.run_test("Delete Appointment", "DELETE", f"appointments/{self.appointment_id}", 200)

    def test_delete_client(self):
        """Test deleting a client"""
        if not self.client_id:
            print("❌ No client ID available")
            return False
        return self.run_test("Delete Client", "DELETE", f"clients/{self.client_id}", 200)

    def test_delete_service(self):
        """Test deleting a service"""
        if not self.service_id:
            print("❌ No service ID available")
            return False
        return self.run_test("Delete Service", "DELETE", f"services/{self.service_id}", 200)

    def test_export_stats_pdf(self):
        """Test PDF export functionality"""
        return self.run_test(
            "Export Stats PDF", 
            "GET", 
            "stats/export-pdf?start_date=2025-01-01&end_date=2025-01-31", 
            200
        )

def main():
    """Run all tests"""
    print("🚀 Starting Hair Salon API Tests...")
    print("=" * 50)
    
    tester = HairSalonAPITester()
    
    # Test sequence
    tests = [
        ("Health Check", tester.test_health_check),
        ("User Registration", tester.test_register), 
        ("Get Profile", tester.test_get_profile),
        ("Get Services (Default)", tester.test_get_services),
        ("Create Operator", tester.test_create_operator),
        ("Get Operators", tester.test_get_operators),
        ("Update Operator", tester.test_update_operator),
        ("SMS Status Check", tester.test_sms_status),
        ("Create Client", tester.test_create_client),
        ("Get Clients", tester.test_get_clients),
        ("Get Single Client", tester.test_get_client),
        ("Update Client", tester.test_update_client),
        ("Create Service", tester.test_create_service),
        ("Update Service", tester.test_update_service),
        ("Create Appointment", tester.test_create_appointment),
        ("Create Appointment with Operator", tester.test_create_appointment_with_operator),
        ("Get Appointments", tester.test_get_appointments),
        ("Get Single Appointment", tester.test_get_appointment),
        ("Update Appointment", tester.test_update_appointment),
        ("Send SMS Reminder", tester.test_send_sms_reminder),
        ("Dashboard Stats", tester.test_dashboard_stats),
        ("Revenue Stats", tester.test_revenue_stats),
        ("Export Stats PDF", tester.test_export_stats_pdf),
        ("Get Settings", tester.test_get_settings),
        ("Update Settings", tester.test_update_settings),
        ("Delete Appointment", tester.test_delete_appointment),
        ("Delete Client", tester.test_delete_client),
        ("Delete Service", tester.test_delete_service),
        ("Delete Operator", tester.test_delete_operator),
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
            tester.tests_run += 1

    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())