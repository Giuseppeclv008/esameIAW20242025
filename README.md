# Festival del Tacco - Web Application

Questa è un'applicazione web per la gestione di un festival musicale, chiamata "Festival Del Tacco". Permette agli utenti di registrarsi come partecipanti o organizzatori, visualizzare le performance, acquistare biglietti e, per gli organizzatori, gestire le performance e visualizzare statistiche.

## Contenuto dell'Archivio (.zip)

L'archivio `.zip` contiene:

1.  **Codice Sorgente:**
    *   Tutti i file Python (`.py`): `app.py`, `festival_dao.py`, `festival_config.py`, `seed_data.py`.
    *   Template HTML (`.html`): situati nella cartella `templates/`.
    *   File CSS (`.css`): situati nella cartella `static/css/`.
    *   File JavaScript (`.js`): situati nella cartella `static/js/`.
    *   Immagini: situate nelle cartelle `static/images/` (logo, performances, placeholder, etc.).
    *   Favicon e file manifest.
    *   `requirements.txt`: file contenente le dipendenze Python del progetto.
2.  **Database:**
    *   `festival.db`: file SQLite contenente il database dell'applicazione, pre-popolato con dati di esempio tramite `seed_data.py`.
3.  **Documentazione:**
    *   `README.md` (questo file): contenente credenziali, istruzioni e descrizione del progetto.

## Credenziali Utenti di Esempio

Le seguenti credenziali sono state create dal file `seed_data.py` e possono essere utilizzate per testare l'applicazione:

| Email                      | Nickname      | Password    | Ruolo       |
| :------------------------- | :------------ | :---------- | :---------- |
| `organizer1@example.com`   | FestivalBoss  | `password123` | Organizer   |
| `organizer2@example.com`   | StageMaster   | `password123` | Organizer   |
| `participant1@example.com` | MusicLover1   | `password123` | Participant |
| `participant2@example.com` | Groover22     | `password123` | Participant |
| `participant3@example.com` | Fanatic3      | `password123` | Participant |

## Istruzioni per Eseguire l'Applicazione Web (Localmente)

Per eseguire l'applicazione localmente, segui questi passaggi:

1.  **Prerequisiti:**
    *   Assicurati di avere Python 3.9 installato.
    *   `pip` (Python package installer) deve essere disponibile.

2.  **Setup Ambiente Virtuale (Consigliato):**
    ```bash
    python -m venv venv
    # Su Windows
    venv\Scripts\activate
    # Su macOS/Linux
    source venv/bin/activate
    ```

3.  **Installazione Dipendenze:**
    Naviga nella directory principale del progetto (dove si trova `requirements.txt`) ed esegui:
    ```bash
    pip install -r requirements.txt
    ```
    Il contenuto di `requirements.txt` dovrebbe essere:
    ```
    Flask>=2.0
    Flask-Login>=0.5
    Werkzeug>=2.0
    ```

4.  **Inizializzazione e Popolamento Database:**
    Esegui lo script per creare le tabelle del database e popolarle con dati di esempio (utenti, performance, biglietti) - nel caso 
    in cui festival.db risultasse vuoto:
    ```bash
    python seed_data.py
    ```
    

5.  **Avvio dell'Applicazione Flask:**
    Esegui lo script principale dell'applicazione:
    ```bash
    python app.py
    ```

6.  **Accesso all'Applicazione:**
    Apri il tuo browser web e naviga all'indirizzo: `http://127.0.0.1:5000/`

## Deploy

L'applicazione è stata deployata ed è visibile al seguente indirizzo:

**[https://giuseppeclv008.pythonanywhere.com/](https://giuseppeclv008.pythonanywhere.com/)**

Se si desidera eseguire l'applicazione localmente, è comunque possibile seguire le istruzioni riportate sopra.

## Funzionalità Implementate

### Per Tutti gli Utenti (Anche Non Registrati)

*   **Homepage & Filtro Performance:**
    *   Visualizzazione delle performance pubblicate.
    *   Un filtro permette di cercare le performance per giorno, palco e genere.
    *   Su desktop, il filtro rimane fisso durante lo scorrimento della lista delle performance, fino al raggiungimento della mappa.
    *   Su dispositivi mobili, il filtro è accessibile tramite un pulsante che apre un modale.
*   **Dettaglio Performance:** Visualizzazione dei dettagli di una singola performance.
*   **Mappa:** Una mappa Leaflet nella homepage mostra la localizzazione del festival.
*   **Pulsante Acquisto Biglietto (Flottante):**
    *   Sempre visibile per utenti non registrati o partecipanti senza biglietto.
    *   Se non registrati, il click reindirizza alla pagina di registrazione.

### Registrazione e Login

*   Gli utenti possono registrarsi come "Participant" o "Organizer".
*   Validazione dei dati di input durante la registrazione (formato email, lunghezza nickname, corrispondenza password).
*   Controllo dell'unicità di email e nickname.
*   Funzionalità di login e logout sicure.

### Per Utenti Partecipanti (Autenticati)

*   **Acquisto Biglietto:**
    *   Accessibile tramite pulsante flottante o dal menu dropdown del profilo (se non si possiede già un biglietto).
    *   Scelta tra diversi tipi di biglietto (Giornaliero, Pass 2 Giorni, Full Pass).
    *   Selezione dei giorni specifici per biglietti giornalieri o pass 2 giorni (con controllo sulla consecutività dei giorni per il pass 2 giorni).
    *   Form di checkout simulato (nessun pagamento reale) con validazione dei campi della carta.
    *   Controllo sul numero massimo di partecipanti giornalieri (`MAX_DAILY_ATTENDEES`).
*   **Pagina Profilo:**
    *   Visualizzazione delle informazioni dell'utente.
    *   Se un biglietto è stato acquistato, vengono mostrati i dettagli del biglietto (tipo, giorni validi, data acquisto).
    *   Se non è stato acquistato, viene mostrato un link per l'acquisto.

### Per Utenti Organizzatori (Autenticati)

*   **Dashboard Statistiche (`/organizer/stats`):**
    *   Accessibile tramite un pulsante dedicato nella navbar.
    *   Visualizzazione della percentuale di biglietti venduti per ciascun giorno del festival rispetto alla capienza massima.
    *   **Nota:** La vendita dei biglietti per il giorno "Friday" è stata parzialmente pre-impostata (manualmente nel DB) a 197 (su 200) per facilitare il test del limite di acquisto biglietti.
    *   Tabella con i dettagli di tutti i biglietti venduti (ID biglietto, nickname utente, email utente, tipo biglietto, giorni validi, data acquisto).
    *   Filtro per visualizzare i biglietti per tipo (es. solo "Biglietto Giornaliero").
*   **Gestione Performance:**
    *   **Visualizzazione:** Nella pagina profilo dell'organizzatore e nella homepage, gli organizzatori vedono tutte le performance pubblicate e *solo le proprie bozze* (performance non pubblicate). Le bozze sono evidenziate.
    *   **Creazione Nuova Performance:**
        *   Tramite un pulsante flottante "+" in basso a destra (apre un modale). Questo pulsante è nascosto tramite CSS nella pagina `/manage_performance` per evitare duplicazioni.
        *   Tramite il link "New Performance" nel menu dropdown del profilo, che porta alla pagina `/manage_performance`.
        *   Le nuove performance vengono create come bozze (non pubblicate).
        *   Include upload di immagini promozionali con validazione del tipo di file.
    *   **Modifica Performance:**
        *   Le bozze create dall'organizzatore possono essere modificate.
        *   Le performance pubblicate non possono essere modificate (un messaggio lo indica).
    *   **Pubblicazione Performance:**
        *   Un organizzatore può pubblicare le proprie bozze.
        *   Viene effettuato un controllo per evitare sovrapposizioni di orario/palco con altre performance già pubblicate.
    *   **Eliminazione Performance:**
        *   Un organizzatore può eliminare *solo le proprie performance* (siano esse bozze o pubblicate).
        *   L'azione richiede una conferma.
        *   Il pulsante di eliminazione è presente nella pagina profilo e nella pagina di dettaglio della performance (se l'organizzatore corrente è il proprietario).

### Responsive Design

*   L'applicazione è stata sviluppata utilizzando Bootstrap 5 per garantire una buona esperienza utente su diversi dispositivi (desktop, tablet, smartphone).
*   Elementi come la navbar, le card delle performance e i form sono responsivi.
*   Il filtro delle performance nella homepage si adatta: sidebar fissa su schermi grandi, modale su schermi piccoli.
*   Le media query CSS sono usate per aggiustamenti specifici.

### Gestione Errori

*   Pagina 404 personalizzata per URL non trovati.
*   Messaggi flash per feedback all'utente (successo, errore, informazioni, avvisi).
*   Gestione di errori comuni come tentativi di accesso a pagine non autorizzate.

---

Questo documento dovrebbe fornire una panoramica completa del progetto e delle sue funzionalità.