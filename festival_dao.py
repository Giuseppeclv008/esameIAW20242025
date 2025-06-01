
import sqlite3
from datetime import datetime, timedelta

DATABASE_NAME = 'festival.db' # Will be overridden by Config if app is run

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    return conn

def init_db(db_name='festival.db'):
    global DATABASE_NAME
    DATABASE_NAME = db_name
    conn = get_db_connection()
    cursor = conn.cursor()

    # UTENTI Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UTENTI (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nickname TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('participant', 'organizer'))
        )
    ''')

    # PERFORMANCE Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PERFORMANCE (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artist_name TEXT NOT NULL UNIQUE,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL, -- HH:MM format
            duration_minutes INTEGER NOT NULL,
            description TEXT,
            stage_name TEXT NOT NULL,
            genre TEXT,
            image_path TEXT,
            is_published INTEGER NOT NULL DEFAULT 0, -- 0 for False, 1 for True
            organizer_id INTEGER NOT NULL,
            FOREIGN KEY (organizer_id) REFERENCES UTENTI (id)
        )
    ''')

    # BIGLIETTI Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS BIGLIETTI (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE, -- One ticket type per user
            ticket_type TEXT NOT NULL,
            valid_days TEXT NOT NULL, -- Comma-separated e.g., "Friday,Saturday"
            purchase_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES UTENTI (id)
        )
    ''')
    
    # PRESENZE_GIORNALIERE Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PRESENZE_GIORNALIERE (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            festival_day TEXT NOT NULL UNIQUE, -- "Friday", "Saturday", "Sunday"
            tickets_sold INTEGER NOT NULL DEFAULT 0
        )
    ''')
    
    # Initialize daily attendance if not present
    from festival_config import Config
    for day in Config.FESTIVAL_DAYS:
        cursor.execute("INSERT OR IGNORE INTO PRESENZE_GIORNALIERE (festival_day, tickets_sold) VALUES (?, 0)", (day,))

    conn.commit()
    conn.close()
    print(f"Database {DATABASE_NAME} initialized.")

# --- User Functions ---
def add_user(email, nickname, password_hash, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO UTENTI (email, nickname, password_hash, role) VALUES (?, ?, ?, ?)",
            (email, nickname, password_hash, role)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError: # For UNIQUE constraint on email
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM UTENTI WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user

def get_user_by_nickname(nickname):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM UTENTI WHERE nickname = ?", (nickname,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM UTENTI WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

# Performance Functions 
def add_performance(artist_name, day, start_time, duration_minutes, description, stage_name, genre, image_path, organizer_id, is_published=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO PERFORMANCE (artist_name, day, start_time, duration_minutes, description, stage_name, genre, image_path, is_published, organizer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (artist_name, day, start_time, duration_minutes, description, stage_name, genre, image_path, is_published, organizer_id))
        conn.commit()
        
        return cursor.lastrowid # è un attributo del cursore che ritorna l'ID dell'ultima riga inserita, nel nostro caso corrisponde all'id della performance
    except sqlite3.IntegrityError: # For UNIQUE constraint on artist_name
        conn.rollback()
        return None
    finally: # viene eseguito sempre, anche in caso di eccezioni e o return 
        conn.close()

def get_performance_by_id(performance_id):
    conn = get_db_connection()
    performance = conn.execute("SELECT p.*, u.nickname as organizer_nickname FROM PERFORMANCE p JOIN UTENTI u ON p.organizer_id = u.id WHERE p.id = ?", (performance_id,)).fetchone()
    conn.close()
    return performance
 
# le assegnazioni dei parametri fanno si che la funzione possa essere usata per ottenere tutte le performance, ma anche filtrate in base a diversi criteri,
# la scrittura dei parametri inn questo modo permette di rendere la funzione flessibile e riutilizzabile
# posso chiamarla anche passando solamente uno dei parametri
# devo tenere in conto delle assegnazioni dei parametri di default
def get_all_performances(published_only=False, day_filter=None, stage_filter=None, genre_filter=None, organizer_id_filter=None):
    conn = get_db_connection()
    query = "SELECT p.*, u.nickname as organizer_nickname FROM PERFORMANCE p JOIN UTENTI u ON p.organizer_id = u.id"
    conditions = []
    params = []

    if published_only:
        conditions.append("p.is_published = 1")
    # opione per recuperare le performance di un organizzatore specifico, se non sono pubblicate
    # utilizzato nel template del profilo dell'organizzatore per mostrare le performance non pubblicate 
    if organizer_id_filter is not None and not published_only: 
         conditions.append("(p.is_published = 1 OR (p.is_published = 0 AND p.organizer_id = ?))")
         params.append(organizer_id_filter)
    elif organizer_id_filter is not None: # General filter by organizer if needed
        conditions.append("p.organizer_id = ?")
        params.append(organizer_id_filter)


    if day_filter:
        conditions.append("p.day = ?")
        params.append(day_filter)
    if stage_filter:
        conditions.append("p.stage_name = ?")
        params.append(stage_filter)
    if genre_filter:
        conditions.append("p.genre LIKE ?") # Use LIKE for partial matches
        params.append(f"%{genre_filter}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY CASE p.day WHEN 'Friday' THEN 1 WHEN 'Saturday' THEN 2 WHEN 'Sunday' THEN 3 ELSE 4 END, p.start_time"
    
    performances = conn.execute(query, tuple(params)).fetchall()
    conn.close()
    return performances
    
def get_performances_by_organizer(organizer_id, include_published=True, include_unpublished=True):
    conn = get_db_connection()
    query = "SELECT p.*, u.nickname as organizer_nickname FROM PERFORMANCE p JOIN UTENTI u ON p.organizer_id = u.id WHERE p.organizer_id = ?"
    params = [organizer_id]
    
    if not include_published and include_unpublished:
        query += " AND p.is_published = 0"
    elif include_published and not include_unpublished:
        query += " AND p.is_published = 1"
    elif not include_published and not include_unpublished: # Should not happen, but good to cover
        conn.close()
        return []
        
    query += " ORDER BY CASE p.day WHEN 'Friday' THEN 1 WHEN 'Saturday' THEN 2 WHEN 'Sunday' THEN 3 ELSE 4 END, p.start_time"
    
    performances = conn.execute(query, tuple(params)).fetchall()
    conn.close()
    return performances


def update_performance(performance_id, artist_name, day, start_time, duration_minutes, description, stage_name, genre, image_path=None, is_published=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    fields_to_update = []
    params = []

    if artist_name is not None: fields_to_update.append("artist_name = ?"); params.append(artist_name)
    if day is not None: fields_to_update.append("day = ?"); params.append(day)
    if start_time is not None: fields_to_update.append("start_time = ?"); params.append(start_time)
    if duration_minutes is not None: fields_to_update.append("duration_minutes = ?"); params.append(duration_minutes)
    if description is not None: fields_to_update.append("description = ?"); params.append(description)
    if stage_name is not None: fields_to_update.append("stage_name = ?"); params.append(stage_name)
    if genre is not None: fields_to_update.append("genre = ?"); params.append(genre)
    if image_path is not None: fields_to_update.append("image_path = ?"); params.append(image_path)
    
    # prima di pubblicare una performance, devo controllare che non ci siano sovrapposizioni con altre performance
    if is_published is not None: 
        fields_to_update.append("is_published = ?")
        performance = get_performance_by_id(performance_id)
        # effettuo questo controllo  perchè posso avere nel db performance che si sovrappongono ma che non sono pubblicate
        # effettuo questo controllo di sovrapposzione in modo da prevenire inserimenti errati 
        if not check_performance_overlap(performance['day'], performance['start_time'], performance['duration_minutes'], performance['stage_name'], exclude_performance_id=performance_id): 
            params.append(is_published)
        else:
            return False # Overlap detected, cannot publish
        
    if not fields_to_update:
        conn.close()
        return False # Nothing to update

    query = "UPDATE PERFORMANCE SET " + ", ".join(fields_to_update) + " WHERE id = ?"
    params.append(performance_id)
    
    try:
        cursor.execute(query, tuple(params))
        conn.commit()

        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        conn.rollback()

        return False
    finally:
        conn.close()

def get_all_ticket_details(ticket_type_filter=None): # Nuova funzione per i dettagli dei biglietti
    conn = get_db_connection()
    # Selezioniamo l'email e il nickname dell'utente, e tutti i dettagli del biglietto
    # Usiamo LEFT JOIN per assicurarci di prendere tutti i biglietti anche se, per qualche motivo,
    # un utente fosse stato cancellato (anche se la FK dovrebbe impedirlo).
    params = []
    
    base_query = """
        SELECT
            b.id as ticket_id,
            b.ticket_type,
            b.valid_days,      
            b.purchase_date,    
            u.id as user_id,        
            u.email as user_email, 
            u.nickname as user_nickname
        FROM BIGLIETTI b
        JOIN UTENTI u ON b.user_id = u.id
    """
    conditions = []
    if ticket_type_filter:# filtro opzionale per il tipo di biglietto
        conditions.append("b.ticket_type = ?")
        params.append(ticket_type_filter)

    if conditions: # Aggiungo le condizioni solo se ci sono filtri 
        base_query += " WHERE " + " AND ".join(conditions)
        
    base_query += " ORDER BY b.purchase_date DESC"
    tickets = conn.execute(base_query, tuple(params)).fetchall()
    conn.close()
    
    return tickets


def get_attendees_for_day(target_day):

    conn = get_db_connection()
    cursor = conn.cursor()
    # Per i biglietti 'full_pass', l'utente partecipa tutti i giorni.
    # Per i biglietti 'daily', days_selected è il giorno specifico.
    # Per i biglietti '2-day', days_selected è una stringa tipo 'Giorno1,Giorno2'.
    # La funzione INSTR verifica se target_day è contenuto in days_selected per i 2-day pass.

    attendees = cursor.execute("""
        SELECT u.id as user_id, u.nickname, u.email
        FROM UTENTI u
        JOIN BIGLIETTI b ON u.id = b.user_id
        WHERE
            (b.ticket_type = 'full_pass') OR
            (b.ticket_type = 'daily' AND t.days_selected = :target_day) OR
            (b.ticket_type = '2-day' AND INSTR(t.valid_days, :target_day) > 0) 
        ORDER BY u.nickname
    """, {'target_day': target_day}).fetchall() 
    # :target_day nella query è un placeholder per il parametro che verrà passato
    # passato al termine della execute, fra parentesi graffe
    # INSTR è una funzione SQLite che mi permette di verificare se il target_day è presente nella stringa valid_days per i biglietti '2-day'.
    # mi ritorna False se non è presente, grazie alla condizione > 0
    conn.close()
    return attendees

def check_performance_overlap(day, start_time_str, duration_minutes, stage_name, exclude_performance_id=None):
    # exclude performance id viene utilizzato per evitare conflitti quando si modifica una performance esistente
    # altrimenti si verificherebbe un conflitto con se stessa
    conn = get_db_connection()
    
    new_start_dt = datetime.strptime(start_time_str, "%H:%M")
    # Calcola il tempo di fine della performance
    new_end_dt = new_start_dt + timedelta(minutes=int(duration_minutes))

    query = "SELECT start_time, duration_minutes FROM PERFORMANCE WHERE day = ? AND stage_name = ? AND is_published = 1" # controllo solo le performance pubblicate
    params = [day, stage_name]
    if exclude_performance_id:
        query += " AND id != ?"
        params.append(exclude_performance_id)
        
    existing_performances = conn.execute(query, tuple(params)).fetchall()
    conn.close()

    for perf in existing_performances:
        existing_start_dt = datetime.strptime(perf['start_time'], "%H:%M")
        existing_end_dt = existing_start_dt + timedelta(minutes=perf['duration_minutes'])
        
        # Check for overlap: (StartA < EndB) and (EndA > StartB)
        if (new_start_dt < existing_end_dt) and (new_end_dt > existing_start_dt):
            return True # Overlap found
    return False # No overlap


# --- Ticket Functions ---
def add_ticket(user_id, ticket_type, valid_days_list, purchase_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    valid_days_str = ",".join(valid_days_list)
    try:
        cursor.execute(
            "INSERT INTO BIGLIETTI (user_id, ticket_type, valid_days, purchase_date) VALUES (?, ?, ?, ?)",
            (user_id, ticket_type, valid_days_str, purchase_date)
        )
        conn.commit()
        # Update daily attendance
        for day in valid_days_list:
            increment_daily_attendance(day)
        return cursor.lastrowid
    except sqlite3.IntegrityError: # Gestisce l'errore di UNIQUE constraint su user_id
        conn.rollback()
        return None
    finally:
        conn.close()

def get_ticket_by_user_id(user_id):
    conn = get_db_connection()
    ticket = conn.execute("SELECT * FROM BIGLIETTI WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return ticket

# --- Daily Attendance Functions ---
def get_daily_attendance(festival_day):
    conn = get_db_connection()
    attendance = conn.execute("SELECT tickets_sold FROM PRESENZE_GIORNALIERE WHERE festival_day = ?", (festival_day,)).fetchone()
    conn.close()
    return attendance['tickets_sold'] if attendance else 0

def increment_daily_attendance(festival_day, count=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE PRESENZE_GIORNALIERE SET tickets_sold = tickets_sold + ? WHERE festival_day = ?", (count, festival_day))
    conn.commit()
    conn.close()
    
def get_all_daily_attendance():
    conn = get_db_connection()
    attendance_data = conn.execute("SELECT festival_day, tickets_sold FROM PRESENZE_GIORNALIERE ORDER BY CASE festival_day WHEN 'Friday' THEN 1 WHEN 'Saturday' THEN 2 WHEN 'Sunday' THEN 3 ELSE 4 END").fetchall()
    conn.close()
    return attendance_data

def delete_performance(performance_id, requesting_organizer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Prima verifica che la performance esista e appartenga all'organizzatore richiedente
        performance = conn.execute("SELECT organizer_id FROM PERFORMANCE WHERE id = ?", (performance_id,)).fetchone()
        if not performance:
            return "not_found" # Performance non trovata
        if performance['organizer_id'] != requesting_organizer_id:
            return "unauthorized" # Non autorizzato a eliminare

        cursor.execute("DELETE FROM PERFORMANCE WHERE id = ?", (performance_id,))
        conn.commit()
        return "success" if cursor.rowcount > 0 else "not_found" # rowcount > 0 se l'eliminazione ha avuto successo
    except sqlite3.Error as e:
        conn.rollback() # in caso di errore, annullo la transazione, evito inconsisenze nel db, proprietà di atomicità
        print(f"Database error deleting performance: {e}")
        return "db_error"
    finally:
        conn.close()
        
        
if __name__ == '__main__':
    # This will initialize the database if the script is run directly
    # You might want to pass a specific db name from your app config
    from festival_config import Config
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE PRESENZE_GIORNALIERE SET tickets_sold = ? WHERE festival_day = ?", (200, Friday))
    conn.commit()
    conn.close()
    

