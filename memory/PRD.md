# PRD - MBHS SALON

## Problema Originale
Applicazione gestionale completa per un salone di parrucchiera con autenticazione, gestione appuntamenti, clienti, servizi, operatori, statistiche e funzionalità avanzate.

## Stato Attuale: COMPLETO E LIVE

### Hosting Produzione
- **Frontend:** Render.com (Static Site)
- **Backend:** Render.com (Web Service)
- **Database:** MongoDB Atlas (Free Tier)
- **URL Live:** https://mbhssalon.onrender.com

### Funzionalità Implementate

#### Core Application
- Autenticazione JWT (email/password)
- Dashboard principale
- Planning giornaliero con griglia 15 minuti
- Vista settimanale e mensile
- Gestione Clienti (CRUD)
- Gestione Servizi (CRUD)
- Gestione Operatori (CRUD)
- Statistiche con export PDF
- Storico appuntamenti

#### Funzionalità Avanzate
- Promemoria SMS (Twilio - richiede credenziali)
- Export PDF statistiche
- Card Prepagate / Abbonamenti
- Ricerca Rapida Cliente nel Planning
- Appuntamenti Ricorrenti
- Checkout in-appointment con metodi pagamento e sconti

#### Import Dati
- Import clienti da Excel (161 clienti)
- 18 Trattamenti importati da XML
- 61 Note Clienti aggiornate da Excel

#### PWA & Offline
- Progressive Web App installabile
- Service Worker per funzionalità offline

#### Prenotazione Online & Landing Page
- Pagina pubblica /prenota con tema scuro elegante
- Artwork "Metti la testa a posto!!" centrato nella hero section
- Servizi collassabili con 3 categorie: Taglio & Piega, Colorazione (Da €30), Modellanti (Da €40)
- Indirizzo cliccabile che apre Google Maps
- Gallery con foto reali del salone (4 foto interni + 6 foto lavori)
- Orari: Mar-Sab 08:00-19:00
- Flusso prenotazione a 3 step
- Controllo sovrapposizione orari
- Pulsante WhatsApp diretto

#### Report & Backup
- Report Incassi
- Backup Dati con export Excel

#### Programma Fedeltà (24 Feb 2026)
- 1 punto ogni €10 spesi (assegnazione automatica al checkout)
- Premio: Sconto 20% Colorazione (5 punti)
- Premio: Taglio Gratuito (10 punti)
- Pagina dedicata /loyalty
- Notifica WhatsApp automatica al raggiungimento soglia 5/10 punti

#### Promemoria & Richiami (24 Feb 2026)
- Promemoria appuntamenti del giorno dopo via WhatsApp
- Richiamo clienti inattivi (60+ giorni) con offerta sconto 10% entro 7 giorni
- Pagina dedicata /reminders
- Banner notifica sul Planning con conteggio promemoria pendenti

#### Landing Page Redesign (25 Feb 2026)
- Ripristinato tema scuro (#0a0a0a) con accenti amber/gold
- Artwork utente come hero image centrale
- Servizi collassabili (Mostra/Nascondi listino)
- 6 foto reali nella gallery acconciature
- Indirizzo cliccabile -> Google Maps
- Orari aggiornati 08:00-19:00
- Layout responsive mobile con CTA fisso in basso

## Credenziali Test
- Email: melitobruno@gmail.com
- Password: password123

## Backlog Futuro
- (P1) Attivare Twilio SMS Reminders (richiede chiavi API utente)
- (P1) Cambio nome repository/username GitHub
- (P2) Stampa ricevuta dopo pagamento
- (P2) Blocco fasce orarie (pause/ferie)
- (P2) Refactoring server.py in moduli separati (>2000 righe)
