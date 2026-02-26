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
- Autenticazione JWT, Dashboard moduli, Planning giornaliero con Drag & Drop
- Vista settimanale/mensile, Gestione Clienti/Servizi/Operatori
- Checkout, Card Prepagate, Report Incassi, Backup dati
- PWA installabile, Riepilogo Giornaliero, Programma Fedelta

### CMS Sito Web (25 Feb 2026)
- Pagina pubblica /sito con contenuti dinamici
- Pagina admin /gestione-sito con 6 tab
- Upload immagini con Object Storage

### Fix Gestionale (26 Feb 2026) - Batch Critici
- Metodi pagamento: solo Contanti e Abbonamento/Prepagata
- Checkout con card prepagata: mostra card attive, scala servizi e valore
- Riscatto punti fedelta in cassa
- Appuntamento ricorrente: settimanale E mensile
- Cliente Generico e Nuovo Cliente al volo
- Operatore MBHS aggiunto, Ricerca cliente card/abbonamenti
- Frecce navigazione e swipe touch per cambiare giorno
- Report Incassi con nuovi label

### Promemoria & Richiami (26 Feb 2026)
- Pagina /reminders completamente riscritta e funzionale
- Messaggi preimpostati (template) con variabili: {nome}, {ora}, {servizi}, {giorni}, {operatore}
- CRUD template messaggi (crea, modifica, elimina)
- Dialog anteprima messaggio prima dell'invio WhatsApp
- Selezione template nel dialog di invio
- Possibilita di reinviare promemoria (reset stato inviato)
- Pulsante WhatsApp funzionante con wa.me e messaggio personalizzabile
- Sezione clienti inattivi 60+ giorni con richiamo e reset

### Pacchetti Preimpostati Card/Abbonamenti (26 Feb 2026)
- Sezione "Pacchetti Preimpostati" nella pagina Card & Abbonamenti
- CRUD pacchetti (crea, modifica, elimina template pacchetti)
- Pacchetti con: nome, tipo, valore, n. servizi, durata mesi, note
- Pulsante "Assegna a Cliente" pre-compila il form nuova card
- 3 pacchetti di esempio creati: Card 10 Pieghe, Abbonamento Mensile, Card 5 Colori

## Credenziali Test
- Email: melitobruno@gmail.com
- Password: password123

## Backlog
- (P1) Attivare Twilio SMS Reminders (richiede chiavi API utente)
- (P1) Aggiungere EMERGENT_LLM_KEY nelle env di Render per upload foto
- (P2) Stampa ricevuta dopo checkout
- (P2) Blocco fasce orarie (pause/ferie)
- (P2) Refactoring server.py in moduli separati (>2500 righe)
- (P2) Refactoring PlanningPage.jsx in componenti piu piccoli
