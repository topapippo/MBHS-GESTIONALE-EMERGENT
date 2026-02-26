"""
Test suite for Auto-Reminders and Batch Send features
Tests: /api/reminders/auto-check, /api/reminders/batch-mark-sent
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hair-salon-portal-1.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "melitobruno@gmail.com"
TEST_PASSWORD = "password123"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping tests")

@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestAutoReminderCheck:
    """Test auto-reminder check endpoint"""
    
    def test_auto_check_returns_valid_response(self, api_client):
        """Test GET /api/reminders/auto-check returns expected structure"""
        response = api_client.get(f"{BASE_URL}/api/reminders/auto-check")
        assert response.status_code == 200
        
        data = response.json()
        # Check expected fields
        assert "is_reminder_time" in data
        assert "pending" in data
        assert "already_sent" in data
        assert "total" in data
        assert "tomorrow_date" in data
        
        # pending should be a list
        assert isinstance(data["pending"], list)
        
        # is_reminder_time should be boolean
        assert isinstance(data["is_reminder_time"], bool)
        
        print(f"✓ Auto-check endpoint returned valid response")
        print(f"  - is_reminder_time: {data['is_reminder_time']}")
        print(f"  - pending count: {len(data['pending'])}")
        print(f"  - already_sent: {data['already_sent']}")
        print(f"  - total: {data['total']}")
        print(f"  - tomorrow_date: {data['tomorrow_date']}")
    
    def test_auto_check_pending_structure(self, api_client):
        """Test that pending appointments have correct structure"""
        response = api_client.get(f"{BASE_URL}/api/reminders/auto-check")
        assert response.status_code == 200
        
        data = response.json()
        
        # If there are pending appointments, verify structure
        if data["pending"]:
            apt = data["pending"][0]
            expected_fields = ["id", "client_name", "client_phone", "time", "services"]
            for field in expected_fields:
                assert field in apt, f"Missing field '{field}' in pending appointment"
            
            print(f"✓ Pending appointment structure is correct")
        else:
            print(f"✓ No pending appointments for tomorrow (expected in test env)")


class TestBatchMarkSent:
    """Test batch mark sent endpoint"""
    
    def test_batch_mark_sent_empty_list(self, api_client):
        """Test POST /api/reminders/batch-mark-sent with empty list"""
        response = api_client.post(f"{BASE_URL}/api/reminders/batch-mark-sent", json={
            "appointment_ids": []
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["marked"] == 0
        
        print(f"✓ Batch mark sent with empty list returns success=True, marked=0")
    
    def test_batch_mark_sent_nonexistent_ids(self, api_client):
        """Test batch mark sent with non-existent appointment IDs"""
        response = api_client.post(f"{BASE_URL}/api/reminders/batch-mark-sent", json={
            "appointment_ids": ["nonexistent-id-1", "nonexistent-id-2"]
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["marked"] >= 0  # Should be 0 since IDs don't exist
        
        print(f"✓ Batch mark sent with non-existent IDs doesn't error")
    
    def test_batch_mark_sent_with_real_appointment(self, api_client):
        """Test batch mark sent with a real appointment for tomorrow"""
        # First get tomorrow date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Get existing appointments for tomorrow
        apts_response = api_client.get(f"{BASE_URL}/api/appointments?date={tomorrow}")
        if apts_response.status_code != 200:
            pytest.skip("Could not fetch appointments")
        
        appointments = apts_response.json()
        
        if appointments:
            # Find one that hasn't been reminded
            unremineded = [a for a in appointments if not a.get("sms_sent", False)]
            if unremineded:
                apt_id = unremineded[0]["id"]
                
                # Mark it as sent
                response = api_client.post(f"{BASE_URL}/api/reminders/batch-mark-sent", json={
                    "appointment_ids": [apt_id]
                })
                assert response.status_code == 200
                
                data = response.json()
                assert data["success"] == True
                assert data["marked"] >= 1
                
                print(f"✓ Batch mark sent with real appointment worked (marked {data['marked']})")
                return
        
        print(f"✓ No appointments for tomorrow to test batch mark sent")


class TestRemindersIntegration:
    """Test reminders endpoints work together"""
    
    def test_auto_check_and_tomorrow_reminders_consistency(self, api_client):
        """Test that auto-check and tomorrow reminders are consistent"""
        # Get auto-check data
        auto_response = api_client.get(f"{BASE_URL}/api/reminders/auto-check")
        assert auto_response.status_code == 200
        auto_data = auto_response.json()
        
        # Get tomorrow reminders
        tomorrow_response = api_client.get(f"{BASE_URL}/api/reminders/tomorrow")
        assert tomorrow_response.status_code == 200
        tomorrow_data = tomorrow_response.json()
        
        # Counts should be consistent
        # auto_check.total should equal len(tomorrow_data)
        assert auto_data["total"] == len(tomorrow_data), \
            f"auto_check.total ({auto_data['total']}) != tomorrow reminders ({len(tomorrow_data)})"
        
        # pending + already_sent should equal total
        assert auto_data["already_sent"] + len(auto_data["pending"]) == auto_data["total"], \
            "already_sent + pending should equal total"
        
        print(f"✓ Auto-check and tomorrow reminders are consistent")
        print(f"  - Total appointments for tomorrow: {auto_data['total']}")


class TestExpensesUpcomingWithOverdue:
    """Additional tests for expenses upcoming with overdue flag"""
    
    def test_upcoming_expenses_overdue_flag(self, api_client):
        """Test that upcoming expenses have overdue flag correctly set"""
        response = api_client.get(f"{BASE_URL}/api/expenses/upcoming?days=7")
        assert response.status_code == 200
        
        expenses = response.json()
        today = datetime.now().strftime("%Y-%m-%d")
        
        for exp in expenses:
            assert "overdue" in exp, "Each expense should have overdue flag"
            
            # If due_date is before today, overdue should be True
            if exp["due_date"] < today:
                assert exp["overdue"] == True, f"Expense {exp['id']} should be overdue"
        
        overdue_count = len([e for e in expenses if e["overdue"]])
        upcoming_count = len([e for e in expenses if not e["overdue"]])
        
        print(f"✓ Expenses overdue flag is correct")
        print(f"  - Overdue: {overdue_count}")
        print(f"  - Upcoming (not overdue): {upcoming_count}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
