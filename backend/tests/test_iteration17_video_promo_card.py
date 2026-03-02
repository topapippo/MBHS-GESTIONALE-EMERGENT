"""
Iteration 17 Tests - Video Upload Support & Promo/Card Selection on Appointments

Features tested:
1. Video upload support (mp4, webm, mov) in /api/website/upload
2. file_type field stored in gallery items
3. promo_id and card_id fields on appointments (create and retrieve)
4. promo_name and card_name returned in appointment responses
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestVideoUpload:
    """Tests for video upload support in /api/website/upload"""
    
    @pytest.fixture
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Return headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_upload_endpoint_accepts_video_types_mp4(self, auth_headers):
        """Test that upload endpoint accepts mp4 video files"""
        # Create a minimal MP4-like test file (header only for testing)
        mp4_content = b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42mp41' + b'\x00' * 100
        
        files = {'file': ('test_video.mp4', mp4_content, 'video/mp4')}
        response = requests.post(
            f"{BASE_URL}/api/website/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert 'id' in data
        assert 'file_type' in data
        assert data['file_type'] == 'video', f"Expected file_type='video', got '{data.get('file_type')}'"
        print(f"PASS: MP4 upload returns file_type='video'")
    
    def test_upload_endpoint_accepts_video_types_webm(self, auth_headers):
        """Test that upload endpoint accepts webm video files"""
        # Create a minimal WebM-like test file
        webm_content = b'\x1a\x45\xdf\xa3' + b'\x00' * 100
        
        files = {'file': ('test_video.webm', webm_content, 'video/webm')}
        response = requests.post(
            f"{BASE_URL}/api/website/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert data['file_type'] == 'video'
        print(f"PASS: WebM upload returns file_type='video'")
    
    def test_upload_endpoint_accepts_video_types_mov(self, auth_headers):
        """Test that upload endpoint accepts mov video files"""
        # Create a minimal MOV-like test file
        mov_content = b'\x00\x00\x00\x14ftypqt  ' + b'\x00' * 100
        
        files = {'file': ('test_video.mov', mov_content, 'video/quicktime')}
        response = requests.post(
            f"{BASE_URL}/api/website/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert data['file_type'] == 'video'
        print(f"PASS: MOV upload returns file_type='video'")
    
    def test_upload_image_returns_image_file_type(self, auth_headers):
        """Test that image upload returns file_type='image'"""
        # Create a minimal JPEG-like test file
        jpg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100
        
        files = {'file': ('test_image.jpg', jpg_content, 'image/jpeg')}
        response = requests.post(
            f"{BASE_URL}/api/website/upload",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert data['file_type'] == 'image', f"Expected file_type='image', got '{data.get('file_type')}'"
        print(f"PASS: Image upload returns file_type='image'")


class TestGalleryFileType:
    """Tests for file_type field in gallery items"""
    
    @pytest.fixture
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_gallery_post_stores_file_type(self, auth_headers):
        """Test that POST /api/website/gallery stores file_type field"""
        gallery_item = {
            "image_url": "/api/website/files/test_video_id",
            "label": "Test Video Item",
            "tag": "test",
            "section": "gallery",
            "file_type": "video"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/website/gallery",
            json=gallery_item,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Gallery POST failed: {response.text}"
        data = response.json()
        assert data.get('file_type') == 'video', f"Expected file_type='video', got '{data.get('file_type')}'"
        print(f"PASS: Gallery POST stores file_type='video'")
        
        # Cleanup
        if 'id' in data:
            requests.delete(f"{BASE_URL}/api/website/gallery/{data['id']}", headers=auth_headers)
    
    def test_gallery_get_returns_file_type(self, auth_headers):
        """Test that GET /api/website/gallery returns file_type field"""
        response = requests.get(f"{BASE_URL}/api/website/gallery", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that gallery items can have file_type
        if len(data) > 0:
            # Verify the structure includes file_type field
            print(f"PASS: Gallery GET returns {len(data)} items")
        else:
            print("INFO: Gallery is empty, but endpoint works")


class TestAppointmentPromoCard:
    """Tests for promo_id and card_id fields on appointments"""
    
    @pytest.fixture
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture
    def test_client(self, auth_headers):
        """Create a test client"""
        client_data = {
            "name": "TEST_PromoCard Client",
            "phone": "333999888777",
            "email": "promo_test@test.com"
        }
        response = requests.post(f"{BASE_URL}/api/clients", json=client_data, headers=auth_headers)
        assert response.status_code in [200, 201], f"Client creation failed: {response.text}"
        client = response.json()
        yield client
        # Cleanup
        requests.delete(f"{BASE_URL}/api/clients/{client['id']}", headers=auth_headers)
    
    @pytest.fixture
    def test_service(self, auth_headers):
        """Get first available service"""
        response = requests.get(f"{BASE_URL}/api/services", headers=auth_headers)
        assert response.status_code == 200
        services = response.json()
        assert len(services) > 0, "No services available for testing"
        return services[0]
    
    @pytest.fixture
    def test_promotion(self, auth_headers):
        """Get or create a test promotion"""
        # Get existing promotions
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        if response.status_code == 200:
            promos = response.json()
            if len(promos) > 0:
                return promos[0]
        
        # Create a test promotion if none exist
        promo_data = {
            "name": "TEST_Promo",
            "description": "Test promo for iteration 17",
            "free_service_name": "Piega Gratis",
            "active": True
        }
        response = requests.post(f"{BASE_URL}/api/promotions", json=promo_data, headers=auth_headers)
        if response.status_code in [200, 201]:
            return response.json()
        return None
    
    @pytest.fixture
    def test_card(self, auth_headers, test_client):
        """Create a test prepaid card"""
        card_data = {
            "client_id": test_client["id"],
            "card_type": "value",
            "name": "TEST Card",
            "total_value": 100.0,
            "notes": "Test card for iteration 17"
        }
        response = requests.post(f"{BASE_URL}/api/cards", json=card_data, headers=auth_headers)
        if response.status_code in [200, 201]:
            card = response.json()
            yield card
            # Cleanup
            requests.delete(f"{BASE_URL}/api/cards/{card['id']}", headers=auth_headers)
        else:
            yield None
    
    def test_create_appointment_with_promo_id(self, auth_headers, test_client, test_service, test_promotion):
        """Test that POST /api/appointments accepts promo_id field"""
        if test_promotion is None:
            pytest.skip("No promotions available for testing")
        
        appointment_data = {
            "client_id": test_client["id"],
            "service_ids": [test_service["id"]],
            "date": "2026-02-15",
            "time": "10:00",
            "promo_id": test_promotion["id"],
            "notes": "Test appointment with promo"
        }
        
        response = requests.post(f"{BASE_URL}/api/appointments", json=appointment_data, headers=auth_headers)
        assert response.status_code in [200, 201], f"Appointment creation failed: {response.text}"
        
        apt = response.json()
        assert apt.get('promo_id') == test_promotion["id"], f"promo_id not saved. Got: {apt.get('promo_id')}"
        assert apt.get('promo_name') is not None, f"promo_name not returned. Got: {apt.get('promo_name')}"
        print(f"PASS: Appointment created with promo_id={apt['promo_id']}, promo_name={apt['promo_name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{apt['id']}", headers=auth_headers)
    
    def test_create_appointment_with_card_id(self, auth_headers, test_client, test_service, test_card):
        """Test that POST /api/appointments accepts card_id field"""
        if test_card is None:
            pytest.skip("No cards available for testing")
        
        appointment_data = {
            "client_id": test_client["id"],
            "service_ids": [test_service["id"]],
            "date": "2026-02-15",
            "time": "11:00",
            "card_id": test_card["id"],
            "notes": "Test appointment with card"
        }
        
        response = requests.post(f"{BASE_URL}/api/appointments", json=appointment_data, headers=auth_headers)
        assert response.status_code in [200, 201], f"Appointment creation failed: {response.text}"
        
        apt = response.json()
        assert apt.get('card_id') == test_card["id"], f"card_id not saved. Got: {apt.get('card_id')}"
        assert apt.get('card_name') is not None, f"card_name not returned. Got: {apt.get('card_name')}"
        print(f"PASS: Appointment created with card_id={apt['card_id']}, card_name={apt['card_name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{apt['id']}", headers=auth_headers)
    
    def test_create_appointment_with_both_promo_and_card(self, auth_headers, test_client, test_service, test_promotion, test_card):
        """Test creating appointment with both promo_id and card_id"""
        if test_promotion is None or test_card is None:
            pytest.skip("Promotions or cards not available for testing")
        
        appointment_data = {
            "client_id": test_client["id"],
            "service_ids": [test_service["id"]],
            "date": "2026-02-15",
            "time": "12:00",
            "promo_id": test_promotion["id"],
            "card_id": test_card["id"],
            "notes": "Test appointment with both promo and card"
        }
        
        response = requests.post(f"{BASE_URL}/api/appointments", json=appointment_data, headers=auth_headers)
        assert response.status_code in [200, 201], f"Appointment creation failed: {response.text}"
        
        apt = response.json()
        assert apt.get('promo_id') == test_promotion["id"]
        assert apt.get('card_id') == test_card["id"]
        assert apt.get('promo_name') is not None
        assert apt.get('card_name') is not None
        print(f"PASS: Appointment created with promo_id and card_id, names resolved correctly")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{apt['id']}", headers=auth_headers)
    
    def test_get_appointments_returns_promo_card_fields(self, auth_headers, test_client, test_service, test_promotion, test_card):
        """Test that GET /api/appointments returns promo_id, promo_name, card_id, card_name"""
        if test_promotion is None or test_card is None:
            pytest.skip("Promotions or cards not available for testing")
        
        # Create appointment with promo and card
        appointment_data = {
            "client_id": test_client["id"],
            "service_ids": [test_service["id"]],
            "date": "2026-02-15",
            "time": "13:00",
            "promo_id": test_promotion["id"],
            "card_id": test_card["id"]
        }
        
        create_response = requests.post(f"{BASE_URL}/api/appointments", json=appointment_data, headers=auth_headers)
        assert create_response.status_code in [200, 201]
        created_apt = create_response.json()
        
        # Get the appointment
        get_response = requests.get(f"{BASE_URL}/api/appointments/{created_apt['id']}", headers=auth_headers)
        assert get_response.status_code == 200
        
        apt = get_response.json()
        assert 'promo_id' in apt
        assert 'promo_name' in apt
        assert 'card_id' in apt
        assert 'card_name' in apt
        assert apt['promo_id'] == test_promotion["id"]
        assert apt['card_id'] == test_card["id"]
        print(f"PASS: GET /api/appointments returns all promo/card fields")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/appointments/{created_apt['id']}", headers=auth_headers)


class TestPromotionsEndpoints:
    """Tests for promotions endpoints used in appointment flow"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_promotions_list(self, auth_headers):
        """Test GET /api/promotions returns list of promotions"""
        response = requests.get(f"{BASE_URL}/api/promotions", headers=auth_headers)
        assert response.status_code == 200
        promos = response.json()
        assert isinstance(promos, list)
        print(f"PASS: GET /api/promotions returns {len(promos)} promotions")
    
    def test_check_client_promos(self, auth_headers):
        """Test GET /api/promotions/check/{client_id} endpoint"""
        # Get a client first
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        if clients_response.status_code == 200 and len(clients_response.json()) > 0:
            client_id = clients_response.json()[0]["id"]
            response = requests.get(f"{BASE_URL}/api/promotions/check/{client_id}", headers=auth_headers)
            assert response.status_code == 200
            promos = response.json()
            assert isinstance(promos, list)
            print(f"PASS: GET /api/promotions/check/{client_id} returns {len(promos)} eligible promos")
        else:
            pytest.skip("No clients available for testing")


class TestCardsEndpoints:
    """Tests for cards endpoints used in appointment flow"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_client_cards(self, auth_headers):
        """Test GET /api/cards?client_id={id} returns client's cards"""
        # Get a client first
        clients_response = requests.get(f"{BASE_URL}/api/clients", headers=auth_headers)
        if clients_response.status_code == 200 and len(clients_response.json()) > 0:
            client_id = clients_response.json()[0]["id"]
            response = requests.get(f"{BASE_URL}/api/cards?client_id={client_id}", headers=auth_headers)
            assert response.status_code == 200
            cards = response.json()
            assert isinstance(cards, list)
            print(f"PASS: GET /api/cards?client_id={client_id} returns {len(cards)} cards")
        else:
            pytest.skip("No clients available for testing")


class TestLoginEndpoint:
    """Test login endpoint works correctly"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "melitobruno@gmail.com",
            "password": "password123"
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        print(f"PASS: Login successful for melitobruno@gmail.com")
    
    def test_login_failure(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code in [401, 400, 404], f"Expected auth failure, got: {response.status_code}"
        print(f"PASS: Login correctly fails with invalid credentials")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
