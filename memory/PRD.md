# PRD - MBHS SALON

## Problema Originale
Applicazione gestionale completa per un salone di parrucchiera (MBHS SALON / Bruno Melito Hair).

## Stato Attuale: COMPLETO
- URL Live: https://mbhssalon.onrender.com
- Preview: https://hair-salon-portal-1.preview.emergentagent.com

## Funzionalita Implementate

### Core
- Autenticazione JWT, Dashboard, Planning giornaliero
- Gestione Clienti/Servizi/Operatori, Checkout, Card Prepagate
- Report Incassi, Backup dati, PWA, Programma Fedelta

### Planning (28 Feb 2026)
- Vista Giorno/Settimana/Mese con toggle
- Vista Settimana: 7 colonne con appuntamenti dettagliati + pulsante "+" per aggiungere appuntamenti direttamente
- Vista Mese: calendario con conteggio e anteprime
- Clic su giorno per tornare alla vista giornaliera
- Navigazione prev/next adattata per ogni vista
- BUG FIX: Appuntamenti online ora visibili in vista giornaliera (auto-assign operatore + colonna "Non assegnato")
- Notifica automatica nuove prenotazioni online (polling ogni 30s, banner con dettagli, dismiss singolo/tutti, click per navigare alla data)

### Punti Fedelta (28 Feb 2026)
- Pulsante "Azzera" per reset completo punti
- Visibili nel dialog modifica appuntamento
- Pulsanti Aggiungi/Rimuovi/Azzera

### SEO (28 Feb 2026)
- Meta tags Open Graph per condivisione social
- Keywords per motori di ricerca
- Descrizione ottimizzata per Google

### Logo e Tema
- Nuovo logo BM con sfondo bianco
- Pagine pubbliche con tema vivace crema/azzurro
- Icone PWA aggiornate

## Link
- Gestionale: https://mbhssalon.onrender.com (login)
- Sito pubblico: https://mbhssalon.onrender.com/sito
- Prenotazioni: https://mbhssalon.onrender.com/prenota

### Sito Web / Galleria (28 Feb 2026)
- Galleria foto salone popolata con 8 immagini reali (4 salone + 4 lavori)
- Foto caricate da CDN customer-assets (funzionano ovunque, anche su Render)

### Refactoring (28 Feb 2026)
- server.py monolitico (3314 righe) suddiviso in 19 file modulari
- Struttura: server.py (53), database.py, auth.py, models.py, utils.py, 14 route files
- 44/44 test API passati, frontend 100% verificato
- Zero regressioni

## Backlog
- (P1) Attivare Twilio SMS/WhatsApp Reminders automatici
- (P2) Stampa ricevuta dopo checkout
- (P2) Blocco fasce orarie per pause/ferie
- (P2) Programma fedelta avanzato
