#!/usr/bin/env python3
"""Script to import services from Trattamenti.xml"""

import requests
import sys

API_URL = "https://hair-salon-portal-1.preview.emergentagent.com/api"

# Services to import from Trattamenti.xml
SERVICES = [
    {"name": "01 Taglio Donna", "category": "taglio", "duration": 10, "price": 10.00},
    {"name": "02 Piega cap.corti", "category": "piega", "duration": 10, "price": 10.00},
    {"name": "03 Piega cap.lunghi", "category": "piega", "duration": 10, "price": 12.00},
    {"name": "04 Piega fantasy", "category": "piega", "duration": 10, "price": 15.00},
    {"name": "05 Piastra o Arricciacapelli", "category": "styling", "duration": 5, "price": 3.00},
    {"name": "05 Taglio uomo", "category": "taglio", "duration": 10, "price": 15.00},
    {"name": "06 Shampoo specifico", "category": "altro", "duration": 5, "price": 2.00},
    {"name": "07 Maschera curativa", "category": "trattamento", "duration": 5, "price": 3.00},
    {"name": "08 Fiala anticaduta-ristrutturante", "category": "trattamento", "duration": 3, "price": 6.00},
    {"name": "09 Laminazione - Ki Power", "category": "trattamento", "duration": 10, "price": 20.00},
    {"name": "10 Colore parziale", "category": "colore", "duration": 10, "price": 18.00},
    {"name": "11 Colore completo", "category": "colore", "duration": 10, "price": 30.00},
    {"name": "12 Colpi di sole", "category": "colore", "duration": 15, "price": 40.00},
    {"name": "13 Colpi di sole cartine", "category": "colore", "duration": 15, "price": 50.00},
    {"name": "14 Balayage Trasparenze", "category": "colore", "duration": 15, "price": 60.00},
    {"name": "15 Permanente - Ondulazione", "category": "permanente", "duration": 15, "price": 40.00},
    {"name": "16 Stiratura - Anticrespo", "category": "stiratura", "duration": 10, "price": 40.00},
    {"name": "Abbonamento colore + 4 piega + maschera", "category": "abbonamento", "duration": 3, "price": 65.00},
]

def main():
    # Login
    print("Logging in...")
    login_res = requests.post(f"{API_URL}/auth/login", json={
        "email": "salone@example.com",
        "password": "password123"
    })
    
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        sys.exit(1)
    
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get existing services
    print("Getting existing services...")
    existing_res = requests.get(f"{API_URL}/services", headers=headers)
    existing_services = {s["name"].lower(): s for s in existing_res.json()}
    
    # Import services
    created = 0
    skipped = 0
    
    for service in SERVICES:
        if service["name"].lower() in existing_services:
            print(f"  Skipping (exists): {service['name']}")
            skipped += 1
            continue
        
        res = requests.post(f"{API_URL}/services", headers=headers, json=service)
        if res.status_code in [200, 201]:
            print(f"  Created: {service['name']}")
            created += 1
        else:
            print(f"  Failed: {service['name']} - {res.text}")
    
    print(f"\nDone! Created: {created}, Skipped: {skipped}")

if __name__ == "__main__":
    main()
