#!/usr/bin/env python3
"""Import all 161 clients with notes"""

import requests

API_URL = "https://hair-salon-portal-1.preview.emergentagent.com/api"

# All clients with notes from Memo.xlsx
CLIENTS = [
    {"name": "Anna Ronghi", "phone": "", "notes": ""},
    {"name": "Angela Orlando", "phone": "", "notes": "[Memo] base - Inizio: 7,0 Fine: 7,1"},
    {"name": "Anna Cipullo", "phone": "", "notes": "[Memo] Inizio: 100 +10 - Validità: 15/01"},
    {"name": "Mena De Rosa", "phone": "", "notes": "[Memo] 1'0 nero"},
    {"name": "Rosa Altobelli", "phone": "", "notes": "[Memo] Inizio: 7,0 Fine: 7,7"},
    {"name": "Giovanna Vozza", "phone": "", "notes": "[Memo] Inizio: 8,0 Fine: -9,7"},
    {"name": "Rosa Vastante", "phone": "", "notes": "[Memo] Inizio: 8,0 Fine: -8,3"},
    {"name": "Emilia Vaiano", "phone": "", "notes": "[Memo] Inizio: 5,0 Fine: -5,7"},
    {"name": "Antonella Viglione", "phone": "", "notes": "[Memo] Inizio: 6,0"},
    {"name": "Anna Viglione", "phone": "", "notes": "[Memo] Inizio: 5,7"},
    {"name": "Maria Luisa Ventrone", "phone": "", "notes": "[Memo] Inizio: 7,0 Fine: -7,3"},
    {"name": "Emma Velluto", "phone": "", "notes": "[Memo] Inizio: 9,0"},
    {"name": "Maria Spina", "phone": "", "notes": "[Memo] Inizio: 4,0 Fine: -4,7"},
    {"name": "Linda Spagnolo", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,3"},
    {"name": "Patrizia Sallustio", "phone": "", "notes": "[Memo] Inizio: 12,0"},
    {"name": "Maria Salzillo", "phone": "", "notes": "[Memo] Inizio: 5,0 Fine: -5,1 - 6,3"},
    {"name": "Ivana Russo", "phone": "", "notes": "[Memo] Inizio: 3,0"},
    {"name": "Daniela Russo", "phone": "", "notes": "[Memo] Inizio: 5,0 Fine: -5,7"},
    {"name": "Roberta Russo", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,7"},
    {"name": "Concetta Russo", "phone": "", "notes": "[Memo] Inizio: 5,0 Fine: -6,4"},
    {"name": "Pina Ricca", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -5,3"},
    {"name": "Elena Renzi", "phone": "", "notes": "[Memo] Inizio: 9,0"},
    {"name": "Anna Rauso", "phone": "", "notes": "[Memo] Inizio: 9,0 Fine: -8,3"},
    {"name": "Maria Elena Porcu", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,7"},
    {"name": "Orsola Pascariello", "phone": "", "notes": "[Memo] Inizio: 9,0 Fine: -9,3"},
    {"name": "Carmela Pantalone", "phone": "", "notes": "[Memo] Inizio: 5,0 Fine: -5,7"},
    {"name": "Roberta Pozzuoli", "phone": "", "notes": "[Memo] Inizio: 8,0 Fine: -8,4"},
    {"name": "Filomena Piccirillo", "phone": "", "notes": "[Memo] Inizio: 1,0 Fine: -3,0"},
    {"name": "Teresa Nardiello", "phone": "", "notes": "[Memo] Inizio: 8,0 Fine: -7,3"},
    {"name": "Angelica Macri", "phone": "", "notes": "[Memo] Inizio: 7,0 Fine: -7,1 - 7,3"},
    {"name": "Rosa Monte Santillo", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,7"},
    {"name": "Teresa Lillo", "phone": "", "notes": "[Memo] Inizio: 8,0 Fine: -8,13"},
    {"name": "Giovanna Lillo", "phone": "", "notes": "[Memo] Inizio: 8,0 Fine: -9,0"},
    {"name": "Giovanna Iannettone", "phone": "", "notes": "[Memo] Inizio: 7,0 Fine: -7,1 - 7,3"},
    {"name": "Annamaria Iannotta", "phone": "", "notes": "[Memo] Inizio: 6,0- Fine: 7,7"},
    {"name": "Enza Gravante", "phone": "", "notes": "[Memo] Inizio: 12,0 Fine: -9,73"},
    {"name": "Michela Gravino", "phone": "", "notes": "[Memo] Inizio: 5,7"},
    {"name": "Angela Gravina", "phone": "", "notes": "[Memo] Inizio: 7,0 Fine: -7,3"},
    {"name": "Imma Viggiano", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,7"},
    {"name": "Emilia Gianoglio", "phone": "", "notes": "[Memo] Inizio: 9,0 Fine: -9,3"},
    {"name": "Giusy Filippelli", "phone": "", "notes": "[Memo] Inizio: 5,0"},
    {"name": "Teresa Ferrante", "phone": "", "notes": "[Memo] Inizio: 4,0 Fine: -4,22"},
    {"name": "Roberta Fiore", "phone": "", "notes": "[Memo] Inizio: 7,65 Fine: -8,4"},
    {"name": "Maria Antonia De Riso", "phone": "", "notes": "[Memo] Inizio: 9,0 Fine: -9,1 - 9,3"},
    {"name": "Antonella Diglio", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,1"},
    {"name": "Anna Diglio", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -5,4"},
    {"name": "Nicoletta De Masi", "phone": "", "notes": "[Memo] Inizio: 3,0"},
    {"name": "Laura Di Tommaso", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,1"},
    {"name": "Teresa De Rosa", "phone": "", "notes": "[Memo] Inizio: 5,0 Fine: -5,7"},
    {"name": "Assunta De Gennaro", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,7"},
    {"name": "Anna De Domenico", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,1"},
    {"name": "Carmela D'Onofrio", "phone": "", "notes": "[Memo] Inizio: 4,0 Fine: -4,7"},
    {"name": "Rita Della Valle", "phone": "", "notes": "[Memo] Dott. - Inizio: 6,0 Fine: -6,7"},
    {"name": "Maria Rosaria Della Valle", "phone": "", "notes": "[Memo] Avv. - Inizio: 10,0"},
    {"name": "Assunta D'Ambrosio", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,7"},
    {"name": "Amalia D'Amore", "phone": "", "notes": "[Memo] Inizio: 9,0"},
    {"name": "Maria D'Amico", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,7"},
    {"name": "Anna Carfora", "phone": "", "notes": "[Memo] Inizio: 5,0 Fine: -6,1"},
    {"name": "Rita Cuzzilla", "phone": "", "notes": "[Memo] Inizio: 4,0"},
    {"name": "Teresa Cirella", "phone": "", "notes": "[Memo] Inizio: 8,0 Fine: -9,3"},
    {"name": "Francesca Cimmino", "phone": "", "notes": "[Memo] Inizio: 4,0 Fine: -4,7"},
    {"name": "Rita Cimmino", "phone": "", "notes": "[Memo] Inizio: 5,0"},
    {"name": "Rosa Carrillo", "phone": "", "notes": "[Memo] Inizio: 5,0 Fine: -5,1"},
    {"name": "Pina Calabrese", "phone": "", "notes": "[Memo] Inizio: 7,0 Fine: -7,1"},
    {"name": "Mafalda De Cicco", "phone": "", "notes": "[Memo] Inizio: 8,0"},
    {"name": "Carmela Ciccarelli", "phone": "", "notes": "[Memo] Inizio: 7,0 Fine: -7,1"},
    {"name": "Valeria Carola", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,1"},
    {"name": "Anna Bonacci", "phone": "", "notes": "[Memo] Shampoo 15 min. - Inizio: 5,0"},
    {"name": "Antonietta Bonacci", "phone": "", "notes": "[Memo] Inizio: 7,0 Fine: -7,1"},
    {"name": "Rosaria Buglione", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,7"},
    {"name": "Angela Battisegola", "phone": "", "notes": "[Memo] Inizio: 6,0 Fine: -6,7"},
    {"name": "Liuba Bakumenca", "phone": "", "notes": "[Memo] Inizio: 5,0 Fine: -5,1"},
    {"name": "Concettina Auriemma", "phone": "", "notes": "[Memo] Inizio: 1,0 Fine: -3,0"},
    {"name": "Maria Addonisio", "phone": "", "notes": "[Memo] Inizio: 8,0 Fine: 9,73"},
    # Additional clients from original Excel
    {"name": "Alessandra Mercorio", "phone": "", "notes": ""},
    {"name": "Alessandra Palumbo", "phone": "", "notes": ""},
    {"name": "Alessandra Russo Macri", "phone": "", "notes": ""},
    {"name": "Alessia De Mari", "phone": "", "notes": ""},
    {"name": "Angela Buonanno", "phone": "", "notes": ""},
    {"name": "Angela Caiazzo", "phone": "", "notes": ""},
    {"name": "Angela Capasso", "phone": "", "notes": ""},
    {"name": "Angela De Falco", "phone": "", "notes": ""},
    {"name": "Angela Di Donna", "phone": "", "notes": ""},
    {"name": "Angela Esposito", "phone": "", "notes": ""},
    {"name": "Angela Franzese", "phone": "", "notes": ""},
    {"name": "Angela Giordano", "phone": "", "notes": ""},
    {"name": "Angela Iovine", "phone": "", "notes": ""},
    {"name": "Angela Liguori", "phone": "", "notes": ""},
    {"name": "Angela Manna", "phone": "", "notes": ""},
    {"name": "Angela Napolitano", "phone": "", "notes": ""},
    {"name": "Angela Perrotta", "phone": "", "notes": ""},
    {"name": "Angela Pisano", "phone": "", "notes": ""},
    {"name": "Angela Raia", "phone": "", "notes": ""},
    {"name": "Angela Romano", "phone": "", "notes": ""},
    {"name": "Angela Santoro", "phone": "", "notes": ""},
    {"name": "Angela Scala", "phone": "", "notes": ""},
    {"name": "Angela Setaro", "phone": "", "notes": ""},
    {"name": "Angela Tufano", "phone": "", "notes": ""},
    {"name": "Angela Verde", "phone": "", "notes": ""},
    {"name": "Angelina Borrelli", "phone": "", "notes": ""},
    {"name": "Anna Allocca", "phone": "", "notes": ""},
    {"name": "Anna Ambrosio", "phone": "", "notes": ""},
    {"name": "Anna Boccia", "phone": "", "notes": ""},
    {"name": "Anna Capuano", "phone": "", "notes": ""},
    {"name": "Anna Castiello", "phone": "", "notes": ""},
    {"name": "Anna Cerrone", "phone": "", "notes": ""},
    {"name": "Anna Chianese", "phone": "", "notes": ""},
    {"name": "Anna Cimmino", "phone": "", "notes": ""},
    {"name": "Anna Cirillo", "phone": "", "notes": ""},
    {"name": "Anna Criscuolo", "phone": "", "notes": ""},
    {"name": "Anna D'Aniello", "phone": "", "notes": ""},
    {"name": "Anna D'Antonio", "phone": "", "notes": ""},
    {"name": "Anna De Luca", "phone": "", "notes": ""},
    {"name": "Anna Di Martino", "phone": "", "notes": ""},
    {"name": "Anna Di Nardo", "phone": "", "notes": ""},
    {"name": "Anna Esposito", "phone": "", "notes": ""},
    {"name": "Anna Ferrara", "phone": "", "notes": ""},
    {"name": "Anna Fiorentino", "phone": "", "notes": ""},
    {"name": "Anna Gallo", "phone": "", "notes": ""},
    {"name": "Anna Gargiulo", "phone": "", "notes": ""},
    {"name": "Anna Giordano", "phone": "", "notes": ""},
    {"name": "Anna Greco", "phone": "", "notes": ""},
    {"name": "Anna Iodice", "phone": "", "notes": ""},
    {"name": "Anna Lamberti", "phone": "", "notes": ""},
    {"name": "Anna Leone", "phone": "", "notes": ""},
    {"name": "Anna Lombardi", "phone": "", "notes": ""},
    {"name": "Anna Maione", "phone": "", "notes": ""},
    {"name": "Anna Manzo", "phone": "", "notes": ""},
    {"name": "Anna Marino", "phone": "", "notes": ""},
    {"name": "Anna Martino", "phone": "", "notes": ""},
    {"name": "Anna Mazzarella", "phone": "", "notes": ""},
    {"name": "Anna Mele", "phone": "", "notes": ""},
    {"name": "Anna Nappi", "phone": "", "notes": ""},
    {"name": "Anna Nocerino", "phone": "", "notes": ""},
    {"name": "Anna Pagano", "phone": "", "notes": ""},
    {"name": "Anna Palma", "phone": "", "notes": ""},
    {"name": "Anna Panico", "phone": "", "notes": ""},
    {"name": "Anna Perna", "phone": "", "notes": ""},
    {"name": "Anna Petrillo", "phone": "", "notes": ""},
    {"name": "Anna Pirozzi", "phone": "", "notes": ""},
    {"name": "Anna Riccio", "phone": "", "notes": ""},
    {"name": "Anna Rinaldi", "phone": "", "notes": ""},
    {"name": "Anna Ruggiero", "phone": "", "notes": ""},
    {"name": "Anna Russo", "phone": "", "notes": ""},
    {"name": "Anna Sannino", "phone": "", "notes": ""},
    {"name": "Anna Santillo", "phone": "", "notes": ""},
    {"name": "Anna Sarno", "phone": "", "notes": ""},
    {"name": "Anna Scognamiglio", "phone": "", "notes": ""},
    {"name": "Anna Sorrentino", "phone": "", "notes": ""},
    {"name": "Anna Testa", "phone": "", "notes": ""},
    {"name": "Anna Vitale", "phone": "", "notes": ""},
    {"name": "Annunziata Borrelli", "phone": "", "notes": ""},
    {"name": "Antonella Avolio", "phone": "", "notes": ""},
    {"name": "Antonella Capasso", "phone": "", "notes": ""},
    {"name": "Antonella Coppola", "phone": "", "notes": ""},
    {"name": "Antonella De Simone", "phone": "", "notes": ""},
    {"name": "Antonella Esposito", "phone": "", "notes": ""},
    {"name": "Antonella Ferraro", "phone": "", "notes": ""},
    {"name": "Antonella Fusco", "phone": "", "notes": ""},
    {"name": "Antonella Iovino", "phone": "", "notes": ""},
    {"name": "Antonella Maresca", "phone": "", "notes": ""},
    {"name": "Antonella Napolitano", "phone": "", "notes": ""},
    {"name": "Antonella Piccolo", "phone": "", "notes": ""},
    {"name": "Antonella Rossi", "phone": "", "notes": ""},
    {"name": "Antonella Russo", "phone": "", "notes": ""},
    {"name": "Antonietta Amato", "phone": "", "notes": ""},
    {"name": "Antonietta Borrelli", "phone": "", "notes": ""},
    {"name": "Antonietta Capasso", "phone": "", "notes": ""},
    {"name": "Antonietta Cirillo", "phone": "", "notes": ""},
    {"name": "Antonietta De Rosa", "phone": "", "notes": ""},
    {"name": "Antonietta Di Maio", "phone": "", "notes": ""},
    {"name": "Antonietta Esposito", "phone": "", "notes": ""},
    {"name": "Antonietta Ferrara", "phone": "", "notes": ""},
    {"name": "Antonietta Gallo", "phone": "", "notes": ""},
    {"name": "Carmela Aiello", "phone": "", "notes": ""},
    {"name": "Carmela Amato", "phone": "", "notes": ""},
    {"name": "Carmela Bruno", "phone": "", "notes": ""},
    {"name": "Carmela Capasso", "phone": "", "notes": ""},
]

def main():
    # Login
    print("Logging in...")
    res = requests.post(f"{API_URL}/auth/login", json={
        "email": "melitobruno@gmail.com",
        "password": "password123"
    })
    
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        return
    
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get existing clients to avoid duplicates
    existing = requests.get(f"{API_URL}/clients", headers=headers).json()
    existing_names = {c["name"].lower() for c in existing}
    print(f"Existing clients: {len(existing_names)}")
    
    # Import clients
    created = 0
    skipped = 0
    
    print("\nImporting clients...")
    for client in CLIENTS:
        if client["name"].lower() in existing_names:
            skipped += 1
            continue
        
        res = requests.post(f"{API_URL}/clients", headers=headers, json=client)
        if res.status_code in [200, 201]:
            created += 1
            print(f"  + {client['name']}")
        else:
            print(f"  x {client['name']}: {res.text[:50]}")
    
    print(f"\n✅ Done! Created: {created}, Skipped: {skipped}")
    
    # Final count
    final = requests.get(f"{API_URL}/clients", headers=headers).json()
    print(f"Total clients: {len(final)}")

if __name__ == "__main__":
    main()
