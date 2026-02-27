# PRD - MBHS SALON

## Problema Originale
Applicazione gestionale completa per un salone di parrucchiera.

## Stato Attuale: COMPLETO E LIVE
- URL Live: https://mbhssalon.onrender.com
- Frontend: Render.com (Static Site)
- Backend: Render.com (Web Service)
- Database: MongoDB Atlas

## Funzionalita Implementate

### Core
- Autenticazione JWT, Dashboard moduli, Planning giornaliero
- Vista settimanale/mensile, Gestione Clienti/Servizi/Operatori
- Checkout con auto-selezione card prepagate e promozioni
- Card Prepagate, Report Incassi, Backup dati
- PWA installabile, Riepilogo Giornaliero, Programma Fedelta

### Planning Avanzato (27 Feb 2026)
- Cambio data e ora nel dialog modifica appuntamento
- Blocco orari passati (gestionale + pagina pubblica + sito)
- Auto-selezione promo al checkout
- Auto-selezione card prepagate al checkout

### CMS Sito Web
- Pagina pubblica /sito con contenuti dinamici e promozioni
- Pagina admin /gestione-sito con 6 tab
- Upload immagini con Object Storage

### Promemoria & Richiami
- Template messaggi personalizzabili con variabili
- Invio WhatsApp individuale e batch automatico
- Banner auto-reminder nel Planning

### Registro Uscite / Scadenziario
- CRUD spese con 8 categorie
- Pagamenti ricorrenti automatici
- Banner scadenze evidenziato sul Planning

### Avviso Telefono Mancante
- Badge nel dropdown clienti e nella lista
- Card rossa nel Planning quando manca

### Sistema Promozioni
- 7 tipi di regole con servizio in omaggio
- 8 promozioni default auto-create
- Suggerimento automatico al checkout
- Visibili su pagina pubblica /prenota e /sito

### Navigazione
- Root (/) apre login gestionale (non piu pagina web)
- PWA start_url punta a /planning
- Dashboard con pulsanti rapidi per Uscite e Promozioni

## Link Principali
- Gestionale: https://mbhssalon.onrender.com (login)
- Sito pubblico: https://mbhssalon.onrender.com/sito
- Prenotazioni: https://mbhssalon.onrender.com/prenota

## Credenziali Test
- Email: melitobruno@gmail.com
- Password: password123

## Backlog
- (P1) Attivare Twilio SMS Reminders (richiede chiavi API utente)
- (P1) EMERGENT_LLM_KEY su Render per upload foto sito
- (P2) Stampa ricevuta dopo checkout
- (P2) Blocco fasce orarie (pause/ferie)
- (P2) Refactoring server.py (>3000 righe) in moduli separati
