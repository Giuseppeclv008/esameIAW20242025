
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, g
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import re # Importa il modulo per le espressioni regolari

# Import configurations and DB functions
from festival_config import Config
import festival_dao as db

# Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)

# Initialize DB with the name from config
db.init_db(app.config['DATABASE'])


# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to 'login' view if @login_required is hit
login_manager.login_message_category = "info"
login_manager.login_message = "Please log in to access this page."


class User(UserMixin):
    def __init__(self, id, email, nickname, role, password_hash=None):
        self.id = id
        self.email = email
        self.nickname = nickname
        self.role = role
        self._password_hash = password_hash # Store hash for internal use 

 
    def get_id(self):
        return str(self.id)

 
    def check_password(self, password):
        user_data = db.get_user_by_id(self.id) 
        if user_data:
            return check_password_hash(user_data['password_hash'], password) # confronta la password inserita con quella salvata nel DB
        return False

@login_manager.user_loader
def load_user(user_id):
    user_data = db.get_user_by_id(int(user_id))
    if user_data:
        return User(id=user_data['id'], email=user_data['email'], nickname=user_data['nickname'], role=user_data['role'])
    return None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.context_processor
def inject_global_vars(): # prendo le variabli globali da festival_config.py, comuni a tutti i template
    # Controlla se l'utente ha già un biglietto
    user_has_ticket = False
    if current_user.is_authenticated and current_user.role == 'participant':
        if db.get_ticket_by_user_id(current_user.id):
            user_has_ticket = True
            
    return dict(
        FESTIVAL_DAYS=Config.FESTIVAL_DAYS,
        FESTIVAL_STAGES=Config.FESTIVAL_STAGES,
        TICKET_TYPES_CONFIG=Config.TICKET_TYPES,
        now=datetime.now().year,
        g_user_has_ticket=user_has_ticket 
    )


# --- Routes ---
@app.route('/')
def home():
    day_filter = request.args.get('day')
    stage_filter = request.args.get('stage')
    genre_filter = request.args.get('genre')
    
    # Tutti vedono solo le performance pubblicate sulla home
    if current_user.is_authenticated and current_user.role == 'organizer':
        # Gli organizzatori vedono tutte le performance, pubblicate e non
        performances = db.get_all_performances(
            published_only=False, 
            day_filter=day_filter,
            stage_filter=stage_filter,
            genre_filter=genre_filter
        )
    else:
        performances = db.get_all_performances(
            published_only=True, 
            day_filter=day_filter,
            stage_filter=stage_filter,
            genre_filter=genre_filter
        )
        
    return render_template('home_festival.html', 
                           performances=performances, 
                           selected_day=day_filter,
                           selected_stage=stage_filter,
                           selected_genre=genre_filter)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        nickname = request.form.get('nickname')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')

        # Basic Validation
        if not all([email, nickname, password, confirm_password, role]):
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))
        
        if len(nickname) < 3 or len(nickname) > 20:
            flash("Nickname must be between 3 and 20 characters.", "danger")
            return redirect(url_for('register'))

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            flash("Invalid email format.", "danger")
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register'))
        if role not in ['participant', 'organizer']:
            flash("Invalid role selected.", "danger")
            return redirect(url_for('register'))
        
        existing_user = db.get_user_by_email(email)
        if existing_user:
            flash("Email address already registered.", "warning")
            return redirect(url_for('register'))
        
        existing_user = db.get_user_by_nickname(nickname)
        if db.get_user_by_nickname(nickname):
            flash("Nickname already taken. Please choose another.", "warning")
            return redirect(url_for('register'))
        
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        user_id = db.add_user(email, nickname, password_hash, role)
        
        if user_id:
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Registration failed. Please try again.", "danger")
            return redirect(url_for('register'))
            
    return render_template('register_festival.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next') # Prendi l'URL 'next', nel caso in cui arrivassi da una pagina che passa next, 
                                        # come nel caso in cui un utente non regitstrato cerca di comprare dal pulsante 
    if current_user.is_authenticated:
        return redirect(url_for('home')) 
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user_data = db.get_user_by_email(email)
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user_obj = User(id=user_data['id'], email=user_data['email'], nickname=user_data['nickname'], role=user_data['role'])
            login_user(user_obj, remember=remember)
            flash(f"Welcome back, {user_obj.nickname}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash("Invalid email or password.", "danger")
            
    return render_template('login_festival.html', next =next_url)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    user_ticket = None
    all_festival_performances = [] # Per la visione completa del festival da parte dell'organizzatore

    if current_user.role == 'participant':
        user_ticket_data = db.get_ticket_by_user_id(current_user.id)
        if user_ticket_data:
            user_ticket = dict(user_ticket_data)
            user_ticket['valid_days_list'] = user_ticket['valid_days'].split(',')
            # La prima get cerca di prendere il nome del tipo di biglietto, se per caso il valore trovato non è 
            # presente nel dizionario Config.TICKET_TYPES, allora viene usato  ritornato il secondo argomento della get, 
            # un dizionario vuoto, che previene un KeyError.
            # la seconda get serve a prendere il nome del tipo di biglietto dal dzionario ritornato
            # se ancora non è presente, allora viene usato 'Unknown Ticket' come valore di ritorno per segnalare che non è stato trovato il biglietto .
            user_ticket['ticket_type_name'] = Config.TICKET_TYPES.get(user_ticket['ticket_type'], {}).get('name', 'Unknown Ticket')
    elif current_user.role == 'organizer':
        print(current_user.id)
        # L'organizzatore vede le sue bozze E tutte le performance pubblicate da chiunque
        all_festival_performances = db.get_all_performances()

    return render_template('profile_festival.html', 
                           user_ticket=user_ticket, 
                           performances=all_festival_performances) 
    
@app.route('/performance/<int:perf_id>')
def performance_detail(perf_id):
    performance = db.get_performance_by_id(perf_id)
    if not performance:
        abort(404)
    # Only show if published, or if current user is the organizer of this performance (even if unpublished)
    if not performance['is_published'] and ( not current_user.is_authenticated or current_user.role != 'organizer'):
         abort(404) 
    
    
    can_buy_ticket = False
    if current_user.is_authenticated and current_user.role == 'participant':
        if not db.get_ticket_by_user_id(current_user.id):
            can_buy_ticket = True

    return render_template('performance_detail.html', performance=performance, can_buy_ticket=can_buy_ticket)


@app.route('/manage_performance', methods=['GET', 'POST'])
@app.route('/manage_performance/<int:perf_id>', methods=['GET', 'POST'])
@login_required
def manage_performance(perf_id=None):
    if current_user.role != 'organizer':
        flash("You are not authorized to manage performances.", "danger")
        return redirect(url_for('home'))

    performance_to_edit = None 
    if perf_id: # Se stiamo modificando - se ho una perfromance da poter editare mi viene ritornato un perf_id
                # Se perf_id è presente, cerco la performance da modificare
                # Se non esiste, ritorna un errore 404
        performance_to_edit = db.get_performance_by_id(perf_id)
        if not performance_to_edit:
            flash("Performance not found.", "danger")
            return redirect(url_for('profile'))
        # Un organizzatore può modificare SOLO le SUE performance e SOLO se NON PUBBLICATE
        if performance_to_edit['organizer_id'] != current_user.id:
            flash("You can only edit performances you created.", "danger")
            return redirect(url_for('profile'))
        if performance_to_edit['is_published']:
            flash("Published performances cannot be edited. Contact an administrator if changes are critical.", "warning")
            return redirect(url_for('performance_detail', perf_id=perf_id))

    if request.method == 'POST':
        
        artist_name = request.form.get('artist_name')
        day = request.form.get('day')
        start_time = request.form.get('start_time')
        duration_minutes = request.form.get('duration_minutes')
        description = request.form.get('description')
        stage_name = request.form.get('stage_name')
        genre = request.form.get('genre')

        # funzione per gestire errori nell'inserimento dei dati 
        def handle_validation_failure(message, is_editing_from_page=False): 
            flash(message, "danger")
            # Se l'utente stava sulla pagina /manage_performance (sta modificando da lì o creando da lì)
            if is_editing_from_page or (not perf_id and request.referrer and url_for('manage_performance') in request.referrer.split('?')[0]):
                 return render_template('manage_performance.html', 
                                        performance=performance_to_edit if perf_id else request.form, 
                                        perf_id=perf_id)
            else:   # request.referrer viene usato per prendere l'URL dell apagina sulla quale si trovava prima l'utente
                return redirect(request.referrer or url_for('profile'))

        if not all([artist_name, day, start_time, duration_minutes, description, stage_name, genre]):
            return handle_validation_failure("All performance fields are required.", is_editing_from_page=(perf_id is not None))

        # Validazione aggiuntiva dei valori
        if day not in Config.FESTIVAL_DAYS:
            return handle_validation_failure(f"Invalid day selected: {day}. Must be one of {', '.join(Config.FESTIVAL_DAYS)}.", is_editing_from_page=(perf_id is not None))
        if stage_name not in Config.FESTIVAL_STAGES:
            return handle_validation_failure(f"Invalid stage selected: {stage_name}. Must be one of {', '.join(Config.FESTIVAL_STAGES)}.", is_editing_from_page=(perf_id is not None))
        
        if not (3 <= len(artist_name) <= 100): # controllo lunghezza
            return handle_validation_failure("Artist name must be between 3 and 100 characters.", is_editing_from_page=(perf_id is not None))
        if not (10 <= len(description) <= 500): # controllo lunghezza
            return handle_validation_failure("Description must be between 10 and 500 characters.", is_editing_from_page=(perf_id is not None))


        try:
            duration_int = int(duration_minutes)
            if duration_int <= 0:
                raise ValueError("Duration must be positive.")
            datetime.strptime(start_time, "%H:%M")
        except ValueError as e:
            return handle_validation_failure(f"Invalid duration or start time: {e}", is_editing_from_page=(perf_id is not None))



        image_file = request.files.get('image')
        # Se viene modificata l'immagine, prende la nuova immagine da salvare, se non vi è una nuova immagine, usa il apth della vecchia
        image_path_to_save = performance_to_edit['image_path'] if performance_to_edit else None 
        
        if not perf_id and not image_file:
            return handle_validation_failure("Promotional image is required for new performances.", is_editing_from_page=False)

        if image_file and image_file.filename != '':
            if allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                unique_filename = str(int(datetime.now().timestamp())) + "_" + filename
                # Salva l'immagine nella cartella configurata
                # Usa il percorso completo per salvare l'immagine
                full_image_save_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], unique_filename)
                # se non esiste la cartella, la crea
                os.makedirs(os.path.join(app.root_path, app.config['UPLOAD_FOLDER']), exist_ok=True)
                image_file.save(full_image_save_path)
                # utilizzato os.path.join perchè il percorso file può essere diverso su sistemi operativi diversi
                # rimosso "static/" dal percorso per salvare l'immagine nel DB perchè per richiamare le immagini facciamo già riferimento all acartella static
                image_path_to_save = os.path.join(app.config['UPLOAD_FOLDER'].replace("static/", ""), unique_filename)
            else:
                return handle_validation_failure("Invalid image file type.", is_editing_from_page=(perf_id is not None))
        elif not perf_id and not image_path_to_save: # Immagine richiesta per nuova performance
             return handle_validation_failure("Promotional image is required and was not processed correctly.", is_editing_from_page=False)

        if perf_id: # Se la performance esiste già, stiamo modificando
            success = db.update_performance(
                perf_id, artist_name, day, start_time, duration_int,
                description, stage_name, genre, 
                image_path=image_path_to_save if (image_file and image_file.filename != '') else None # Passa None se non si aggiorna l'immagine
            )
            if success:
                flash("Performance updated successfully!", "success")
            else:
                # Controlla se l'errore è dovuto a nome artista duplicato
                existing_artist_perf = db.conn.execute("SELECT id FROM PERFORMANCE WHERE artist_name = ? AND id != ?", (artist_name, perf_id)).fetchone()
                if existing_artist_perf:
                     flash("Failed to update performance. An artist with this name already exists in the festival.", "danger")
                else:
                     flash("Failed to update performance or no changes were made.", "danger")
            return redirect(url_for('profile'))
        else: # Adding new performance
            if not image_path_to_save:
                return handle_validation_failure("Promotional image is required and was not processed correctly.", is_editing_from_page=False)

            new_perf_id = db.add_performance(
                artist_name, day, start_time, duration_int, description,
                stage_name, genre, image_path_to_save, current_user.id, is_published=0
            )
            if new_perf_id: # mi ritorna l'id della nuova performance -> viene preso come true
                flash("Performance draft created successfully!", "success")
            else:
                # Errore più probabile qui è duplicato nome artista (gestito da UNIQUE in DB)
                flash("Failed to create performance. An artist with this name may already exist in the festival.", "danger")
            return redirect(request.referrer or url_for('profile')) 
            
   
    return render_template('manage_performance.html', performance=performance_to_edit, perf_id=perf_id)


@app.route('/performance/<int:perf_id>/publish', methods=['POST'])
@login_required
def publish_performance(perf_id):
    if current_user.role != 'organizer':
        abort(404)
    
    performance = db.get_performance_by_id(perf_id)
    if not performance or performance['organizer_id'] != current_user.id:
        flash("Performance not found or you are not authorized.", "danger")
        return redirect(url_for('profile'))

    if performance['is_published']:
        flash("Performance is already published.", "info")
    else:
        success = db.update_performance(perf_id, artist_name=None, day=None, start_time=None, duration_minutes=None, description=None, stage_name=None, genre=None, is_published=1)
        if success:
            flash("Performance published successfully!", "success")
        else:
            flash("Failed to publish performance. Could overlap an existing performance.", "danger")
    return redirect(url_for('profile'))



@app.route('/buy_ticket', methods=['GET', 'POST'])
@login_required
def buy_ticket():
    
    if current_user.role != 'participant':
        flash("Only participants can buy tickets.", "warning")
        return redirect(url_for('home'))

    if db.get_ticket_by_user_id(current_user.id):
        flash("You have already purchased a ticket for this festival.", "info")
        return redirect(url_for('profile'))

    # Oggetto per ripopolare il form in caso di GET o errore POST
    current_form_values = request.form if request.method == 'POST' else {}

    if request.method == 'POST':
        ticket_type = request.form.get('ticket_type')
        # Input specifici per tipo di biglietto
        selected_day_for_daily = request.form.get('days_daily')    # Radio button, un solo valore
        selected_days_for_2day = request.form.getlist('days_2day') # Checkbox, lista di valori
        
        # Nuovi campi per il checkout
        card_holder = request.form.get('card_holder')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        cvv = request.form.get('cvv')
        billing_email = request.form.get('billing_email')
        terms_accepted = request.form.get('terms_accepted')

        # Funzione helper per re-renderizzare con errore e valori del form
        def render_with_error_and_form_values(message):
            flash(message, "danger")
            return render_template('ticket_purchase.html',
                                   TICKET_TYPES_CONFIG=Config.TICKET_TYPES,
                                   FESTIVAL_DAYS=Config.FESTIVAL_DAYS,
                                   form_values=request.form) # Passa i valori correnti del form

        # Validazione dei campi di pagamento
        if not all([card_holder, card_number, expiry_date, cvv, billing_email]):
            return render_with_error_and_form_values("All payment fields are required.")
        
        if not terms_accepted:
            return render_with_error_and_form_values("You must accept the Terms & Conditions to proceed.")
        
        # Validazioni base sui dati della carta (fittizie ma realistiche)
        if len(card_holder.strip()) < 2:
            return render_with_error_and_form_values("Please enter a valid cardholder name.")
        
        # Rimuovi spazi dal numero della carta per la validazione
        card_number_clean = card_number.replace(' ', '')
        if not card_number_clean.isdigit() or len(card_number_clean) < 13 or len(card_number_clean) > 19:
            return render_with_error_and_form_values("Please enter a valid card number.")
        
        # Validazione formato data scadenza (MM/YY)
       
        expiry_match = re.match(r'^(0[1-9]|1[0-2])\/(\d{2})$', expiry_date)
        if not expiry_match:
            return render_with_error_and_form_values("Please enter expiry date in MM/YY format.")
        
        # Controllo che la data di scadenza non sia passata
        try:
            expiry_month = int(expiry_match.group(1))
            expiry_year_short = int(expiry_match.group(2))
            # Assumiamo che YY si riferisca al secolo corrente (20YY)
            current_year_full = datetime.now().year
            current_month = datetime.now().month
            expiry_year_full = 2000 + expiry_year_short

            if expiry_year_full < current_year_full or (expiry_year_full == current_year_full and expiry_month < current_month):
                return render_with_error_and_form_values("The expiry date entered is in the past. Please use a valid card.")
        except ValueError:
             # Questo non dovrebbe accadere se il regex match ha successo, ma è una buona pratica
            return render_with_error_and_form_values("Invalid expiry date format.")
        
        # Validazione CVV
        if not cvv.isdigit() or len(cvv) < 3 or len(cvv) > 4:
            return render_with_error_and_form_values("Please enter a valid CVV (3-4 digits).")
        
        # Validazione email di fatturazione
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, billing_email):
            return render_with_error_and_form_values("Please enter a valid billing email address.")

        # Resto della validazione del biglietto (codice esistente)
        if not ticket_type or ticket_type not in Config.TICKET_TYPES:
            return render_with_error_and_form_values("Invalid ticket type selected.")

        ticket_config = Config.TICKET_TYPES[ticket_type]
        valid_days_for_ticket = []

        if ticket_type == "daily":
            if not selected_day_for_daily or selected_day_for_daily not in Config.FESTIVAL_DAYS:
                return render_with_error_and_form_values("Please select exactly one valid day for a Daily Ticket.")
            valid_days_for_ticket = [selected_day_for_daily]
        elif ticket_type == "2-day":
            if not selected_days_for_2day or len(selected_days_for_2day) != 2:
                return render_with_error_and_form_values("Please select exactly two days for a 2-Day Pass.")
            
            # Controlla che i giorni selezionati siano validi giorni del festival
            for day_val in selected_days_for_2day:
                if day_val not in Config.FESTIVAL_DAYS:
                    return render_with_error_and_form_values(f"Invalid day selected for 2-Day Pass: {day_val}.")

            # Controlla la consecutività
            day_indices = sorted([Config.FESTIVAL_DAYS.index(d) for d in selected_days_for_2day])
            if day_indices[1] - day_indices[0] != 1:
                return render_with_error_and_form_values("For a 2-Day Pass, selected days must be consecutive.")
            valid_days_for_ticket = [Config.FESTIVAL_DAYS[i] for i in day_indices] # Mantiene l'ordine corretto
        elif ticket_type == "full_pass":
            valid_days_for_ticket = Config.FESTIVAL_DAYS

        # Controlla i limiti di partecipazione giornaliera
        for day_check in valid_days_for_ticket:
            if db.get_daily_attendance(day_check) >= Config.MAX_DAILY_ATTENDEES:
                flash(f"Sorry, tickets for {day_check} are sold out.", "warning") # Usa 'warning' per sold out
                return render_template('ticket_purchase.html', # Ripassa i valori del form
                                   TICKET_TYPES_CONFIG=Config.TICKET_TYPES,
                                   FESTIVAL_DAYS=Config.FESTIVAL_DAYS,
                                   form_values=request.form)
        
        # Simulazione processo di pagamento (fittizio)
        flash("Payment processed successfully! (Demo mode - no real charge)", "info")
        
        purchase_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ticket_id = db.add_ticket(current_user.id, ticket_type, valid_days_for_ticket, purchase_date_str)

        if ticket_id:
            flash(f"{ticket_config['name']} purchased successfully!", "success")
            return redirect(url_for('profile'))
        else:
            # Questo caso potrebbe verificarsi se db.add_ticket fallisce per l'unicità dell'user_id,
            # ma dovrebbe essere già gestito dal controllo all'inizio della funzione.
            return render_with_error_and_form_values("Failed to purchase ticket. Please try again.")

    # Per la richiesta GET (primo caricamento della pagina)
    return render_template('ticket_purchase.html',
                           TICKET_TYPES_CONFIG=Config.TICKET_TYPES,
                           FESTIVAL_DAYS=Config.FESTIVAL_DAYS,
                           form_values=current_form_values) # current_form_values è {} per GETw


@app.route('/handle_buy_ticket_action') # Questa route è usata per gestire il caso in cui l'utente non è loggato e clicca su "Buy Ticket"
                                        # Utile perchè nel caso cercassi di entrare nella pagina /buy_ticket senza essere loggato,
                                        # verrebbe reindirizzato alla pagina di registrazione/login ma non avrei il redirect alla pagina /buy_ticket 
def handle_buy_ticket_action():
    if current_user.is_authenticated:
        # Se l'utente è autenticato, reindirizza alla pagina di acquisto biglietti
        return redirect(url_for('buy_ticket', next=url_for('buy_ticket')))
    elif current_user.is_anonymous:
        flash("Please register or log in to purchase a ticket", "info")
        return redirect(url_for('register', next=url_for('buy_ticket')))






@app.route('/organizer/stats')
@login_required
def organizer_stats():
    if current_user.role != 'organizer':
        abort(404)
    
    ticket_type_filter_value = request.args.get('ticket_type_filter')
    attendance_data = db.get_all_daily_attendance()
    
    all_tickets_details = db.get_all_ticket_details(ticket_type_filter=ticket_type_filter_value) 
    
  
    processed_tickets = []
    for ticket in all_tickets_details:
        ticket_dict = dict(ticket) # Converte sqlite3.Row in un dizionario
        ticket_dict['valid_days_list'] = ticket_dict['valid_days'].split(',')
        ticket_dict['ticket_type_name'] = Config.TICKET_TYPES.get(ticket_dict['ticket_type'], {}).get('name', ticket_dict['ticket_type'])
        processed_tickets.append(ticket_dict)

    return render_template(
        'organizer_stats.html',
        attendance_data=attendance_data,
        max_attendees=Config.MAX_DAILY_ATTENDEES,
        tickets_details=processed_tickets, # Passa i dettagli dei biglietti al template
        selected_ticket_type=ticket_type_filter_value # Per ripopolare il filtro
        )

@app.route('/performance/<int:perf_id>/delete', methods=['POST'])
@login_required
def delete_performance_route(perf_id):
    if current_user.role != 'organizer':
        flash("You are not authorized for this action.", "danger")
        return redirect(url_for('home'))

    result = db.delete_performance(perf_id, current_user.id)

    if result == "success":
        flash("Performance deleted successfully.", "success")
    elif result == "not_found":
        flash("Performance not found or already deleted.", "warning")
    elif result == "unauthorized":
        flash("You are not authorized to delete this performance.", "danger")
    elif result == "db_error":
        flash("A database error occurred while trying to delete the performance.", "danger")
    
    return redirect(url_for('profile'))




@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    
    app.run(debug=True)
