# PRD - MBHS SALON

## Problema Originale
Applicazione gestionale completa per un salone di parrucchiera con autenticazione, gestione appuntamenti, clienti, servizi, operatori, statistiche e funzionalita avanzate.

## Stato Attuale: COMPLETO E LIVE

### Hosting Produzione
- **Frontend:** Render.com (Static Site)
- **Backend:** Render.com (Web Service)
- **Database:** MongoDB Atlas (Free Tier)
- **URL Live:** https://mbhssalon.onrender.com

### Funzionalita Implementate

#### Core Application
- Autenticazione JWT (email/password)
- Dashboard con moduli cliccabili (16 moduli con navigazione alle sottopagine)
- Planning giornaliero con griglia 15 minuti + DRAG & DROP per spostare appuntamenti
- Vista settimanale con slot 15 minuti (Lun-Sab)
- Vista mensile
- Gestione Clienti (CRUD) - 183 clienti
- Gestione Servizi (CRUD) - 20 servizi in 6 categorie con colori personalizzati
- Operatore unico BRUNO con possibilita di aggiungerne altri
- Statistiche con export PDF
- Storico appuntamenti

#### Landing Page / Sito Web (25 Feb 2026)
- URL principale mbhssalon.onrender.com mostra la landing page ai visitatori
- Utenti loggati vedono direttamente il Planning
- /prenota continua a funzionare come alias
- Sezioni: Hero, Servizi, Gallery Salone, Chi Siamo, Recensioni, Gallery Lavori, Contatti, Footer
- Tema scuro (#1a1a2e) con bordi colorati e effetto glow

#### Servizi (6 categorie, ordinati per numero)
- Taglio: 01 Taglio Donna, 06 Taglio uomo
- Colore: 11-15 (Parziale, Completo, Colpi di sole, Cartine, Balayage)
- Piega: 02-04 (Cap.corti, Cap.lunghi, Fantasy)
- Trattamento: 08-10 (Maschera, Fiala, Laminazione)
- Modellanti: 16-20 (Permanente, Anticrespo, Ondulazione, Stiratura Classica, Stiratura New) - Da 40 EUR
- Altro: 05, 07

#### Funzionalita Avanzate
- Checkout in-appointment con metodi pagamento e sconti
- Card Prepagate / Abbonamenti
- Ricerca Rapida Cliente nel Planning
- Appuntamenti Ricorrenti
- Report Incassi + Statistiche
- Backup dati con export Excel
- Pagina Impostazioni
- Riepilogo Giornaliero con grafico orario

## Bug Fix (25 Feb 2026)
- Fix percorsi Dashboard: i moduli Planning, Settimanale, Mensile e Card Prepagate puntavano a rotte inesistenti
- Aggiunta rotta /planning dedicata
- Landing page come homepage per visitatori non loggati

## Credenziali Test
- Email: melitobruno@gmail.com
- Password: password123

## Backlog Futuro
- (P1) Attivare Twilio SMS Reminders (richiede chiavi API utente)
- (P1) Cambio nome repository/username GitHub
- (P2) Stampa ricevuta dopo pagamento
- (P2) Blocco fasce orarie (pause/ferie)
- (P2) Refactoring server.py in moduli separati (>2500 righe)
