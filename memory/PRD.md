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
- Dashboard con moduli cliccabili (15 moduli con navigazione alle sottopagine)
- Planning giornaliero con griglia 15 minuti + DRAG & DROP per spostare appuntamenti
- Vista settimanale con slot 15 minuti (Lun-Sab)
- Vista mensile
- Gestione Clienti (CRUD) - 183 clienti
- Gestione Servizi (CRUD) - 20 servizi in 6 categorie
- Operatore unico BRUNO con possibilità di aggiungerne altri
- Statistiche con export PDF
- Storico appuntamenti

#### Servizi (6 categorie, ordinati per numero)
- **Taglio:** 01 Taglio Donna, 06 Taglio uomo
- **Colore:** 11-15 (Parziale, Completo, Colpi di sole, Cartine, Balayage)
- **Piega:** 02-04 (Cap.corti, Cap.lunghi, Fantasy)
- **Trattamento:** 08-10 (Maschera, Fiala, Laminazione)
- **Modellanti:** 16-20 (Permanente, Anticrespo, Ondulazione, Stiratura Classica, Stiratura New) - Da €40
- **Altro:** 05, 07

#### Funzionalità Avanzate
- Checkout in-appointment con metodi pagamento e sconti
- Card Prepagate / Abbonamenti
- Ricerca Rapida Cliente nel Planning
- Appuntamenti Ricorrenti
- Report Incassi + Statistiche
- Backup dati con export Excel
- Pagina Impostazioni

#### PWA & Offline
- Progressive Web App installabile con icona desktop
- Service Worker per funzionalità offline

#### Prenotazione Online & Landing Page
- Pagina pubblica /prenota con tema blu scuro chiaro (#1a1a2e)
- Bordi morbidi arrotondati (rounded-3xl) colorati con effetto glow al hover
- Artwork "Metti la testa a posto!!" centrato nella hero
- 6 foto reali nella gallery acconciature
- Servizi collassabili, indirizzo cliccabile Google Maps
- Orari: Mar-Sab 08:00-19:00
- Flusso prenotazione a 3 step

#### Programma Fedeltà (punti azzerati il 25 Feb 2026)
- 1 punto ogni €10 spesi
- Premi configurabili
- Pagina dedicata /loyalty

#### Promemoria & Richiami
- Promemoria appuntamenti via WhatsApp
- Richiamo clienti inattivi
- Pagina dedicata /reminders

#### Riepilogo Giornaliero (25 Feb 2026)
- Pagina /daily-summary con navigazione per data
- Incasso totale con confronto vs giorno precedente
- Numero clienti serviti e media per cliente
- Grafico a barre distribuzione oraria (08:00-20:00)
- Top 5 servizi più richiesti del giorno
- Metodi di pagamento utilizzati
- Ora di punta automatica

## Credenziali Test
- Email: melitobruno@gmail.com
- Password: password123

## Backlog Futuro
- (P1) Attivare Twilio SMS Reminders (richiede chiavi API utente)
- (P1) Cambio nome repository/username GitHub
- (P2) Stampa ricevuta dopo pagamento
- (P2) Blocco fasce orarie (pause/ferie)
- (P2) Refactoring server.py in moduli separati (>2000 righe)
