# PRD - MBHS SALON

## Problema Originale
Applicazione gestionale completa per un salone di parrucchiera con autenticazione, gestione appuntamenti, clienti, servizi, operatori, statistiche e funzionalità avanzate.

## Stato Attuale: COMPLETO

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

#### Prenotazione Online
- Pagina di benvenuto con logo, indirizzo (Via Vito Nicola Melorio 101, Santa Maria Capua Vetere CE) e numeri di telefono (0823 1878320 / 339 783 3526)
- Pagina pubblica /prenota con flusso a 3 step
- Controllo sovrapposizione orari

#### Report & Backup
- Report Incassi
- Backup Dati con export Excel

#### Programma Fedeltà (24 Feb 2026)
- 1 punto ogni €10 spesi (assegnazione automatica al checkout)
- Premio: Sconto 20% Colorazione (5 punti)
- Premio: Taglio Gratuito (10 punti)
- Pagina dedicata /loyalty
- Punti visibili nello storico cliente e checkout
- Notifica WhatsApp automatica al raggiungimento soglia 5/10 punti

#### Promemoria & Richiami (24 Feb 2026)
- Promemoria appuntamenti del giorno dopo via WhatsApp
- Richiamo clienti inattivi (60+ giorni) con offerta sconto 10% entro 7 giorni
- Pagina dedicata /reminders con due sezioni
- Banner notifica sul Planning con conteggio promemoria pendenti
- Tracciamento invii (evita doppi invii, cooldown 30 giorni per richiami)

#### Branding
- Logo MBHS SALON su login, booking, sidebar

## Credenziali Test
- Email: melitobruno@gmail.com
- Password: password123

## Backlog Futuro
- (P2) Stampa ricevuta dopo pagamento
- (P2) Blocco fasce orarie (pause/ferie)
- (P2) Refactoring server.py in moduli separati (>2000 righe)
