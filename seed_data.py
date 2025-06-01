
import sqlite3
from werkzeug.security import generate_password_hash
from festival_dao import init_db, add_user, add_performance, add_ticket, get_daily_attendance, increment_daily_attendance
from festival_config import Config
from datetime import datetime

def seed():
    print("Initializing database...")
    init_db(Config.DATABASE) # Ensure tables are created

    conn = sqlite3.connect(Config.DATABASE)
    cursor = conn.cursor()



    print("Seeding users...")
    users_data = [
        {"email": "organizer1@example.com", "nickname": "FestivalBoss", "password": "password123", "role": "organizer"},
        {"email": "organizer2@example.com", "nickname": "StageMaster", "password": "password123", "role": "organizer"},
        {"email": "participant1@example.com", "nickname": "MusicLover1", "password": "password123", "role": "participant"},
        {"email": "participant2@example.com", "nickname": "Groover22", "password": "password123", "role": "participant"},
        {"email": "participant3@example.com", "nickname": "Fanatic3", "password": "password123", "role": "participant"},
    ]
    user_ids = {}
    for user_data in users_data:
        # Check if user already exists
        existing_user = conn.execute("SELECT id FROM UTENTI WHERE email = ?", (user_data["email"],)).fetchone()
        if existing_user:
            user_ids[user_data["email"]] = existing_user[0]
            print(f"User {user_data['email']} already exists with ID {user_ids[user_data['email']]}")
        else:
            user_id = add_user(
                user_data["email"],
                user_data["nickname"],
                generate_password_hash(user_data["password"],  method='pbkdf2:sha256'),
                user_data["role"]
            )
            user_ids[user_data["email"]] = user_id
            print(f"Added user {user_data['email']} with ID {user_id}")

    print("User IDs:", user_ids)


    print("\nSeeding performances...")
    org1_id = user_ids["organizer1@example.com"]
    org2_id = user_ids["organizer2@example.com"]

    print("Dropping old performances...")
    cursor.execute("DELETE FROM PERFORMANCE")
    conn.commit()

    performances_data = [
               # Venerdì
        {"artist_name": "Sud Sound System", "day": "Friday", "start_time": "18:00", "duration_minutes": 90, "description": "Reggae salentino con ritmi travolgenti.", "stage_name": "Palco Sole & Sale", "genre": "Reggae", "image_path": "images/performances/SudSoundSystem.jpg", "is_published": 1, "organizer_id": org1_id},
        {"artist_name": "Mama Marjas", "day": "Friday", "start_time": "19:45", "duration_minutes": 75, "description": "Soul e reggae con voce potente dal cuore di Taranto.", "stage_name": "Palco Taranta Elettrica", "genre": "Soul/Reggae", "image_path": "images/performances/mama_marjas.jpg", "is_published": 1, "organizer_id": org2_id},
        {"artist_name": "Ghemon ", "day": "Friday", "start_time": "21:15", "duration_minutes": 75, "description": "Performance speciale con band locale di Lecce.", "stage_name": "Palco Ulivo Sonoro", "genre": "Hip-Hop/Fusion", "image_path": "images/performances/Ghemon.jpg", "is_published": 1, "organizer_id": org1_id},
        {"artist_name": "Domenico Modugno", "day": "Friday", "start_time": "20:00", "duration_minutes": 90, "description": "Omaggio al maestro", "stage_name": "Palco Sole & Sale", "genre": "Cantautorato", "image_path": "images/performances/DomenicoModugno.jpeg", "is_published": 0, "organizer_id": org1_id},
        {"artist_name": "Alborosie", "day": "Friday", "start_time": "22:45", "duration_minutes": 75, "description": "Star Internazionale del Reggae", "stage_name": "Palco Taranta Elettrica", "genre": "Reggae", "image_path": "images/performances/Alborosie.jpeg", "is_published": 1, "organizer_id": org2_id},
                # Sabato
        {"artist_name": "Boomdabash", "day": "Saturday", "start_time": "17:00", "duration_minutes": 90, "description": "Dancehall e pop salentino per scatenare il pubblico.", "stage_name": "Palco Sole & Sale", "genre": "Pop/Dancehall", "image_path": "images/performances/Boomdabash.jpg", "is_published": 1, "organizer_id": org2_id},
        {"artist_name": "La Municipàl", "day": "Saturday", "start_time": "18:45", "duration_minutes": 75, "description": "Indie pop raffinato e poetico dal Salento.", "stage_name": "Palco Taranta Elettrica", "genre": "Indie Pop", "image_path": "images/performances/LaMunicipal.jpg", "is_published": 1, "organizer_id": org1_id},
        {"artist_name": "Antonio Castrignanò", "day": "Saturday", "start_time": "20:15", "duration_minutes": 90, "description": "Il volto moderno della pizzica con energia e tradizione.", "stage_name": "Palco Ulivo Sonoro", "genre": "Pizzica", "image_path": "images/performances/AntonioCastrignano.jpg", "is_published": 1, "organizer_id": org2_id},
        {"artist_name": "Caparezza", "day": "Saturday", "start_time": "20:00", "duration_minutes": 90, "description": "Artista irriverente e pungente ", "stage_name": "Palco Sole & Sale", "genre": "Rap", "image_path": "images/performances/Caparezza.jpeg", "is_published": 0, "organizer_id": org1_id},
        {"artist_name": "Al Bano", "day": "Saturday", "start_time": "22:00", "duration_minutes": 75, "description": "Al Bano ci viene a trovare dopo il suo importantissimo tour in Russia", "stage_name": "Palco Taranta Elettrica", "genre": "Cantautorato", "image_path": "images/performances/Al Bano.jpeg", "is_published": 1, "organizer_id": org2_id},
        # Domenica
        {"artist_name": "Krikka Reggae", "day": "Sunday", "start_time": "16:00", "duration_minutes": 75, "description": "Reggae del sud Italia con testi sociali.", "stage_name": "Palco Sole & Sale", "genre": "Reggae", "image_path": "images/performances/KrikkaReggae.jpg", "is_published": 1, "organizer_id": org1_id},
        {"artist_name": "Camillo Pace", "day": "Sunday", "start_time": "17:30", "duration_minutes": 60, "description": "Cantautorato raffinato e poetico dalla provincia tarantina.", "stage_name": "Palco Taranta Elettrica", "genre": "Cantautorato", "image_path": "images/performances/CamilloPace.jpg", "is_published": 1, "organizer_id": org2_id},
        {"artist_name": "Officina Zoè", "day": "Sunday", "start_time": "19:00", "duration_minutes": 90, "description": "Storica formazione di pizzica salentina, autentica e potente.", "stage_name": "Palco Ulivo Sonoro", "genre": "Pizzica Tradizionale", "image_path": "images/performances/OfficinaZoe.jpg", "is_published": 1, "organizer_id": org1_id},
        {"artist_name": "Checco Zalone", "day": "Sunday", "start_time": "23:00", "duration_minutes": 90, "description": "Il comico Checco Zalone ci delizia con le sue canzoni ironiche ", "stage_name": "Palco Sole & Sale", "genre": "Cantautorato/Comico", "image_path": "images/performances/CheccoZalone.jpg", "is_published": 0, "organizer_id": org1_id},
        {"artist_name": "Renzo Arbore", "day": "Sunday", "start_time": "19:45", "duration_minutes": 75, "description": "Intermezzo nostalgico con il carissimo Renzo Arbore", "stage_name": "Palco Taranta Elettrica", "genre": "Cantautorato", "image_path": "images/performances/RenzoArbore.jpg", "is_published": 1, "organizer_id": org2_id},
    ]

    for perf_data in performances_data:
        existing_perf = conn.execute("SELECT id FROM PERFORMANCE WHERE artist_name = ?", (perf_data["artist_name"],)).fetchone()
        if existing_perf:
            print(f"Performance by {perf_data['artist_name']} already exists.")
        else:
            perf_id = add_performance(**perf_data)
            print(f"Added performance {perf_data['artist_name']} with ID {perf_id}")

    print("\nSeeding tickets...")
    # Ticket data: (user_email, ticket_type, valid_days_list)
    tickets_to_add = [
        (user_ids["participant1@example.com"], "daily", ["Friday"]),
        (user_ids["participant2@example.com"], "2-day", ["Saturday", "Sunday"]),
        (user_ids["participant3@example.com"], "full_pass", ["Friday", "Saturday", "Sunday"]),
    ]
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for user_id_val, ticket_type, valid_days in tickets_to_add:
        existing_ticket = conn.execute("SELECT id FROM BIGLIETTI WHERE user_id = ?", (user_id_val,)).fetchone()
        if existing_ticket:
            print(f"Ticket for user ID {user_id_val} already exists.")
        else:
            # Check daily limits before adding ticket
            can_add_ticket = True
            for day in valid_days:
                if get_daily_attendance(day) >= Config.MAX_DAILY_ATTENDEES:
                    can_add_ticket = False
                    print(f"Cannot add ticket for user {user_id_val} - day {day} is full.")
                    break
            
            if can_add_ticket:
                ticket_id = add_ticket(user_id_val, ticket_type, valid_days, current_time)
                if ticket_id:
                    print(f"Added {ticket_type} ticket for user ID {user_id_val} (Ticket ID: {ticket_id}) for days: {', '.join(valid_days)}")
                else:
                    print(f"Failed to add ticket for user ID {user_id_val}")

    conn.close()
    print("\nSeed data process complete.")
    print("Remember to provide these credentials for testing:")
    for u in users_data:
        print(f"Email: {u['email']}, Password: {u['password']}, Role: {u['role']}")

if __name__ == "__main__":
    seed()
