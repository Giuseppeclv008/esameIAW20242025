
import secrets




class Config:
    # Generate a random hex string of 24 bytes (48 hex characters)
    SECRET_KEY =  secrets.token_hex(24)
    DATABASE = 'festival.db'
    UPLOAD_FOLDER = 'static/images/performances'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_DAILY_ATTENDEES = 200
    FESTIVAL_DAYS = ["Friday", "Saturday", "Sunday"]
    FESTIVAL_STAGES = ["Palco Sole & Sale", "Palco Taranta Elettrica", "Palco Ulivo Sonoro"]
    TICKET_TYPES = {
        "daily": {"name": "Biglietto Giornaliero", "days_covered": 1},
        "2-day": {"name": "Pass 2 Giorni", "days_covered": 2},
        "full_pass": {"name": "Full Pass", "days_covered": 3}
    }

