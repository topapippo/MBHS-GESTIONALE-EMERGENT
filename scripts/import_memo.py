#!/usr/bin/env python3
"""Script to update client notes from Memo.xlsx data"""

import requests
import sys

API_URL = "https://hair-salon-portal-1.preview.emergentagent.com/api"

# Client notes extracted from Memo.xlsx
# Format: client name -> notes (combining all memo data)
CLIENT_NOTES = {
    "Anna Ronghi": "",
    "Angela Orlando": "base - Inizio: 7,0 Fine: 7,1",
    "Anna Cipullo": "Inizio: 100 +10 - Validità: 15/01",
    "Mena De Rosa": "1'0 nero",
    "Rosa Altobelli": "Inizio: 7,0 Fine: 7,7",
    "Giovanna Vozza": "Inizio: 8,0 Fine: -9,7",
    "Rosa Vastante": "Inizio: 8,0 Fine: -8,3",
    "Emilia Vaiano": "Inizio: 5,0 Fine: -5,7",
    "Antonella Viglione": "Inizio: 6,0",
    "Anna Viglione": "Inizio: 5,7",
    "Maria Luisa Ventrone": "Inizio: 7,0 Fine: -7,3",
    "Emma Velluto": "Inizio: 9,0",
    "Maria Spina": "Inizio: 4,0 Fine: -4,7",
    "Linda Spagnolo": "Inizio: 6,0 Fine: -6,3",
    "Patrizia Sallustio": "Inizio: 12,0",
    "Maria Salzillo": "Inizio: 5,0 Fine: -5,1 - 6,3",
    "Ivana Russo": "Inizio: 3,0",
    "Daniela Russo": "Inizio: 5,0 Fine: -5,7",
    "Roberta Russo": "Inizio: 6,0 Fine: -6,7",
    "Concetta Russo": "Inizio: 5,0 Fine: -6,4",
    "Pina Ricca": "Inizio: 6,0 Fine: -5,3",
    "Elena Renzi": "Inizio: 9,0",
    "Anna Rauso": "Inizio: 9,0 Fine: -8,3",
    "Maria Elena Porcu": "Inizio: 6,0 Fine: -6,7",
    "Orsola Pascariello": "Inizio: 9,0 Fine: -9,3",
    "Carmela Pantalone": "Inizio: 5,0 Fine: -5,7",
    "Roberta Pozzuoli": "Inizio: 8,0 Fine: -8,4",
    "Filomena Piccirillo": "Inizio: 1,0 Fine: -3,0",
    "Teresa Nardiello": "Inizio: 8,0 Fine: -7,3",
    "Angelica Macrì": "Inizio: 7,0 Fine: -7,1 - 7,3",
    "Rosa Monte Santillo": "Inizio: 6,0 Fine: -6,7",
    "Teresa Lillo": "Inizio: 8,0 Fine: -8,13",
    "Giovanna Lillo": "Inizio: 8,0 Fine: -9,0",
    "Giovanna Iannettone": "Inizio: 7,0 Fine: -7,1 - 7,3",
    "Annamaria Iannotta": "Inizio: 6,0- Fine: 7,7",
    "Enza Gravante": "Inizio: 12,0 Fine: -9,73",
    "Michela Gravino": "Inizio: 5,7",
    "Angela Gravina": "Inizio: 7,0 Fine: -7,3",
    "Imma Viggiano": "Inizio: 6,0 Fine: -6,7",
    "Emilia Gianoglio": "Inizio: 9,0 Fine: -9,3",
    "Giusy Filippelli": "Inizio: 5,0",
    "Teresa Ferrante": "Inizio: 4,0 Fine: -4,22",
    "Roberta Fiore": "Inizio: 7,65 Fine: -8,4",
    "Maria Antonia De Riso": "Inizio: 9,0 Fine: -9,1 - 9,3",
    "Antonella Diglio": "Inizio: 6,0 Fine: -6,1",
    "Anna Diglio": "Inizio: 6,0 Fine: -5,4",
    "Nicoletta De Masi": "Inizio: 3,0",
    "Laura Di Tommaso": "Inizio: 6,0 Fine: -6,1",
    "Teresa De Rosa": "Inizio: 5,0 Fine: -5,7",
    "Assunta De Gennaro": "Inizio: 6,0 Fine: -6,7",
    "Anna De Domenico": "Inizio: 6,0 Fine: -6,1",
    "Carmela D'Onofrio": "Inizio: 4,0 Fine: -4,7",
    "Rita Della Valle": "Dott. - Inizio: 6,0 Fine: -6,7",
    "Maria Rosaria Della Valle": "Avv. - Inizio: 10,0",
    "Assunta D'Ambrosio": "Inizio: 6,0 Fine: -6,7",
    "Amalia D'Amore": "Inizio: 9,0",
    "Maria D'Amico": "Inizio: 6,0 Fine: -6,7",
    "Anna Carfora": "Inizio: 5,0 Fine: -6,1",
    "Rita Cuzzilla": "Inizio: 4,0",
    "Teresa Cirella": "Inizio: 8,0 Fine: -9,3",
    "Francesca Cimmino": "Inizio: 4,0 Fine: -4,7",
    "Rita Cimmino": "Inizio: 5,0",
    "Rosa Carrillo": "Inizio: 5,0 Fine: -5,1",
    "Pina Calabrese": "Inizio: 7,0 Fine: -7,1",
    "Mafalda De Cicco": "Inizio: 8,0",
    "Carmela Ciccarelli": "Inizio: 7,0 Fine: -7,1",
    "Valeria Carola": "Inizio: 6,0 Fine: -6,1",
    "Anna Bonacci": "Shampoo 15 min. - Inizio: 5,0",
    "Antonietta Bonacci": "Inizio: 7,0 Fine: -7,1",
    "Rosaria Buglione": "Inizio: 6,0 Fine: -6,7",
    "Angela Battisegola": "Inizio: 6,0 Fine: -6,7",
    "Liuba Bakumenca": "Inizio: 5,0 Fine: -5,1",
    "Concettina Auriemma": "Inizio: 1,0 Fine: -3,0",
    "Maria Addonisio": "Inizio: 8,0 Fine: 9,73",
}


def normalize_name(name):
    """Normalize name for matching"""
    return name.lower().strip()


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
    
    # Get existing clients
    print("Getting existing clients...")
    clients_res = requests.get(f"{API_URL}/clients", headers=headers)
    clients = clients_res.json()
    
    # Create lookup by normalized name
    client_lookup = {}
    for client in clients:
        normalized = normalize_name(client["name"])
        client_lookup[normalized] = client
    
    # Update client notes
    updated = 0
    not_found = 0
    
    for client_name, notes in CLIENT_NOTES.items():
        if not notes:
            continue
            
        # Try to find client
        normalized = normalize_name(client_name)
        client = client_lookup.get(normalized)
        
        # Try partial match if exact match fails
        if not client:
            for key, c in client_lookup.items():
                if normalized in key or key in normalized:
                    client = c
                    break
        
        if not client:
            print(f"  Not found: {client_name}")
            not_found += 1
            continue
        
        # Update notes (append if existing)
        existing_notes = client.get("notes", "")
        new_notes = f"{existing_notes}\n[Memo] {notes}".strip() if existing_notes else f"[Memo] {notes}"
        
        res = requests.put(
            f"{API_URL}/clients/{client['id']}", 
            headers=headers, 
            json={"notes": new_notes}
        )
        
        if res.status_code == 200:
            print(f"  Updated: {client_name}")
            updated += 1
        else:
            print(f"  Failed to update: {client_name} - {res.text}")
    
    print(f"\nDone! Updated: {updated}, Not found: {not_found}")


if __name__ == "__main__":
    main()
