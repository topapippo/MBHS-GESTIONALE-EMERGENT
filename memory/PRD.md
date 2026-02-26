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
- Metodi pagamento: solo Contanti e Abbonamento/Prepagata (rimossi Carta e Bonifico)
- Checkout con card prepagata: mostra card attive del cliente, scala servizi e valore
- Riscatto punti fedelta in cassa
- Appuntamento ricorrente: settimanale E mensile
- Cliente Generico per appuntamenti senza nominativo
- Nuovo Cliente: crea al volo dal dialog appuntamento (non serve rubrica)
- Operatore MBHS aggiunto come colonna nel planning
- Ricerca cliente con prime lettere nella pagina Card/Abbonamenti
- Frecce navigazione giorno centrate e ben visibili
- Swipe touch per cambiare giorno su mobile
- Report Incassi aggiornati con nuovi label metodi pagamento
- Categoria Modellanti confermata con 5 servizi (gia esistente)

## Credenziali Test
- Email: melitobruno@gmail.com
- Password: password123

## Backlog
- (P2) Sezione Promemoria: modifica/cancellazione/reinvio
- (P1) Attivare Twilio SMS Reminders (richiede chiavi API)
- (P1) Aggiungere EMERGENT_LLM_KEY nelle env di Render per upload foto
- (P2) Stampa ricevuta dopo checkout
- (P2) Blocco fasce orarie (pause/ferie)
- (P2) Refactoring server.py in moduli separati
