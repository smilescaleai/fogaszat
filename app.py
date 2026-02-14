import os
import csv
import json
import requests
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from io import StringIO

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smilescale_secret_key_2026')

# Version: 2.1 - Auto Spreadsheet Creation

# Admin felhasználók tárolása (PSID alapján, page_id szerint csoportosítva)
admin_users = {}

# Felhasználói állapotok tárolása (időpontfoglaláshoz)
user_states = {}

# Get Started gomb beállítva (page_id szerint)
get_started_setup = set()

# Szerver indulás flag
server_started = False

# Cached page data (egyszer betöltve)
cached_page_data = {}

# CSV URL a Google Sheets-ből (csak Config-hoz)
CONFIG_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO13uEpQukHL1hTzxeZUjGYPaUPQ7XaKTjVWnbhlh2KnvOztWLASO6Jmu8782-4vx0Dco64xEVi2pO/pub?output=csv"

# Verify token
VERIFY_TOKEN = "smilescale_token_2026"

# Google Sheets setup
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')  # Config Sheet (CSV)
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS')

# Ügyfél-specifikus Spreadsheet-ek cache-elése
client_spreadsheets = {}

def get_sheets_client():
    """Google Sheets API kliens létrehozása."""
    try:
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"❌ Hiba a Google Sheets kliens létrehozásakor: {e}")
        return None

def get_or_create_client_spreadsheet(page_id, company_name):
    """
    Ügyfél-specifikus Spreadsheet lekérése vagy létrehozása.
    Ha még nincs, létrehoz egy új Spreadsheet-et a company_name-mel,
    és benne 3 lapot: Leads, Patients, Treatments.
    """
    global client_spreadsheets
    
    # Cache ellenőrzés
    if page_id in client_spreadsheets:
        return client_spreadsheets[page_id]
    
    try:
        client = get_sheets_client()
        if not client:
            return None
        
        # Próbáljuk megkeresni a meglévő Spreadsheet-et
        # A Config Sheet-ben tároljuk a spreadsheet_id-t (új N oszlop)
        config_sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        cell = config_sheet.find(page_id)
        
        if cell:
            row = cell.row
            # N oszlop (14) = spreadsheet_id
            try:
                existing_id = config_sheet.cell(row, 14).value
                if existing_id:
                    print(f"✅ Meglévő Spreadsheet: {existing_id}")
                    spreadsheet = client.open_by_key(existing_id)
                    client_spreadsheets[page_id] = spreadsheet
                    return spreadsheet
            except:
                pass
        
        # Ha nincs még, létrehozunk egy újat
        print(f"🆕 Új Spreadsheet létrehozása: {company_name}")
        spreadsheet = client.create(f"{company_name} - CRM")
        
        # Alapértelmezett Sheet1 átnevezése Leads-re
        sheet1 = spreadsheet.sheet1
        sheet1.update_title("Leads")
        
        # Leads fejléc
        sheet1.append_row([
            'lead_id', 'beerkezett', 'page_id', 'company_name', 
            'name', 'phone', 'psid', 'veglegesitett_idopont', 'megjegyzes'
        ])
        
        # Patients lap létrehozása
        patients_sheet = spreadsheet.add_worksheet(title="Patients", rows=1000, cols=10)
        patients_sheet.append_row([
            'beteg_id', 'page_id', 'nev', 'telefon', 'email', 
            'cim', 'szuletesi_datum', 'megjegyzesek', 'letrehozva'
        ])
        
        # Treatments lap létrehozása
        treatments_sheet = spreadsheet.add_worksheet(title="Treatments", rows=1000, cols=10)
        treatments_sheet.append_row([
            'kezeles_id', 'page_id', 'beteg_id', 'tipus', 'datum', 
            'leiras', 'ar', 'fizetve', 'letrehozva'
        ])
        
        # Spreadsheet ID visszaírása a Config Sheet-be (N oszlop)
        if cell:
            config_sheet.update_cell(row, 14, spreadsheet.id)
            print(f"✅ Spreadsheet ID mentve: {spreadsheet.id}")
        
        # Cache-elés
        client_spreadsheets[page_id] = spreadsheet
        
        print(f"✅ Spreadsheet létrehozva: {spreadsheet.url}")
        return spreadsheet
        
    except Exception as e:
        print(f"❌ Spreadsheet létrehozási hiba: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_lead_id():
    """Egyedi Lead ID generálása"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"LEAD-{timestamp}"

def save_lead(page_id, page_info, user_data):
    """Lead mentése Google Sheets táblába"""
    try:
        lead_id = generate_lead_id()
        timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        
        print(f"💾 Lead mentés: {user_data.get('name')}")
        
        # Ügyfél Spreadsheet lekérése/létrehozása
        company_name = page_info.get('company_name', f'Ügyfél-{page_id[:6]}')
        spreadsheet = get_or_create_client_spreadsheet(page_id, company_name)
        
        if not spreadsheet:
            print("❌ Spreadsheet hiba!")
            return False
        
        # Leads lap
        sheet = spreadsheet.worksheet("Leads")
        
        # 9 oszlop
        row = [
            lead_id,
            timestamp,
            page_id,
            page_info.get('company_name', ''),
            user_data.get('name', ''),
            user_data.get('phone', ''),
            user_data.get('psid', ''),
            '',
            user_data.get('notes', '')
        ]
        
        print(f"📝 Sor írása: {row[:5]}...")
        sheet.append_row(row)
        print(f"✅ Lead mentve: {lead_id}")
        return True
        
    except Exception as e:
        print(f"❌ Lead mentési hiba: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_admin_psid(page_id, admin_psid):
    """Admin PSID visszaírása a Google Sheets táblázatba."""
    try:
        print(f"🔧 Admin PSID mentés: page_id={page_id}, psid={admin_psid}")
        
        client = get_sheets_client()
        if not client:
            print("❌ Kliens hiba!")
            return False
        
        print(f"🔍 Tábla megnyitása: {SPREADSHEET_ID}")
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        print(f"🔍 Page ID keresése: {page_id}")
        cell = sheet.find(page_id)
        if cell:
            row = cell.row
            print(f"🔍 Sor találva: {row}, L oszlop (12.) frissítése")
            # L oszlop (12.) = admin_psid
            sheet.update_cell(row, 12, admin_psid)
            print(f"✅ Admin PSID mentve!")
            
            global cached_page_data
            if page_id in cached_page_data:
                cached_page_data[page_id]['admin_psid'] = admin_psid
            
            return True
        
        print(f"❌ Page ID nem található!")
        return False
    except Exception as e:
        print(f"❌ Hiba az admin PSID frissítésekor: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_get_started_button(page_id, access_token):
    """Get Started gomb beállítása (csak egyszer oldalanként)."""
    if page_id in get_started_setup:
        return True
    
    try:
        url = f"https://graph.facebook.com/v18.0/me/messenger_profile?access_token={access_token}"
        payload = {"get_started": {"payload": "GET_STARTED"}}
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code in [200, 400]:
            get_started_setup.add(page_id)
            return True
        
        response.raise_for_status()
        get_started_setup.add(page_id)
        return True
    except Exception as e:
        print(f"⚠️ Get Started gomb hiba: {e}")
        get_started_setup.add(page_id)
        return False

def load_page_data():
    """Letölti és feldolgozza a Config CSV fájlt a Google Sheets-ből."""
    try:
        print("📥 Config CSV letöltése...")
        response = requests.get(CONFIG_CSV_URL, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        csv_content = StringIO(response.text)
        reader = csv.DictReader(csv_content)
        
        page_data = {}
        for row in reader:
            page_id = str(row.get('page_id', '')).strip()
            company_name = str(row.get('company_name', '')).strip()
            access_token = str(row.get('access_token', '')).strip()
            admin_password = str(row.get('admin_password', '')).strip()
            welcome_text = str(row.get('welcome_text', '')).strip()
            
            button1_text = str(row.get('button1_text', '')).strip()
            button1_link = str(row.get('button1_link', '')).strip()
            button2_text = str(row.get('button2_text', '')).strip()
            button2_link = str(row.get('button2_link', '')).strip()
            button3_text = str(row.get('button3_text', '')).strip()
            button3_link = str(row.get('button3_link', '')).strip()
            admin_psid = str(row.get('admin_psid', '')).strip()
            dashboard = str(row.get('dashboard', '0')).strip()  # ÚJ!
            
            if page_id and access_token:
                page_data[page_id] = {
                    "access_token": access_token,
                    "admin_password": admin_password if admin_password else '',
                    "admin_psid": admin_psid if admin_psid else '',
                    "welcome_text": welcome_text if welcome_text else 'Üdvözöljük! 🦷',
                    "company_name": company_name if company_name else f"Fogászat {page_id[:4]}",
                    "button1_text": button1_text if button1_text else '',
                    "button1_link": button1_link if button1_link else '',
                    "button2_text": button2_text if button2_text else '',
                    "button2_link": button2_link if button2_link else '',
                    "button3_text": button3_text if button3_text else '',
                    "button3_link": button3_link if button3_link else '',
                    "dashboard": dashboard  # ÚJ!
                }
                
                if admin_psid:
                    if page_id not in admin_users:
                        admin_users[page_id] = set()
                    admin_users[page_id].add(admin_psid)
        
        print(f"✅ Config CSV betöltve! {len(page_data)} oldal.")
        return page_data
    except Exception as e:
        print(f"❌ Config CSV hiba: {e}")
        return {}

def send_text_message(recipient_id, message_text, access_token):
    """Egyszerű szöveges üzenet küldése."""
    url = f"https://graph.facebook.com/v18.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "access_token": access_token
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Üzenet hiba: {e}")
        return False

def send_generic_template(recipient_id, welcome_text, buttons, access_token):
    """Generic Template küldése gombokkal."""
    url = f"https://graph.facebook.com/v18.0/me/messages"
    
    validated_buttons = []
    for btn in buttons[:3]:
        if btn.get('type') == 'postback':
            validated_buttons.append({
                "type": "postback",
                "title": btn['title'][:20],
                "payload": btn['payload']
            })
        elif btn.get('type') == 'web_url' and btn.get('url'):
            validated_buttons.append({
                "type": "web_url",
                "url": btn['url'],
                "title": btn['title'][:20]
            })
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [{
                        "title": welcome_text[:80],
                        "subtitle": "Válasszon az alábbiak közül:",
                        "buttons": validated_buttons
                    }]
                }
            }
        },
        "access_token": access_token
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Template hiba: {e}")
        return False

@app.route('/')
def home():
    return "SmileScale Server Active", 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Facebook Webhook"""
    global server_started, cached_page_data
    
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return 'Forbidden', 403
    
    data = request.get_json()
    
    # Config CSV betöltés (cache, csak egyszer)
    if not cached_page_data:
        cached_page_data = load_page_data()
    
    if not cached_page_data:
        return jsonify({"status": "error"}), 500
    
    page_data = cached_page_data
    
    if not server_started:
        for page_id, page_info in page_data.items():
            setup_get_started_button(page_id, page_info['access_token'])
        server_started = True
    
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                sender_id = messaging_event['sender']['id']
                recipient_id = messaging_event['recipient']['id']
                page_id = recipient_id
                
                if page_id not in page_data:
                    continue
                
                page_info = page_data[page_id]
                access_token = page_info['access_token']
                admin_password = page_info['admin_password']
                
                if messaging_event.get('message'):
                    message_text = messaging_event['message'].get('text', '')
                    
                    # Admin regisztráció
                    if message_text == admin_password and admin_password:
                        if page_id not in admin_users:
                            admin_users[page_id] = set()
                        admin_users[page_id].add(sender_id)
                        update_admin_psid(page_id, sender_id)
                        send_text_message(sender_id, "✅ Jelszó elfogadva! Mostantól Ön kapja az időpontfoglalásokat.", access_token)
                        continue
                    
                    # Időpontfoglalás folyamat
                    if sender_id in user_states:
                        state = user_states[sender_id]['state']
                        
                        if state == 'waiting_name':
                            user_states[sender_id]['name'] = message_text
                            user_states[sender_id]['state'] = 'waiting_phone'
                            send_text_message(sender_id, "Telefonszám:", access_token)
                        
                        elif state == 'waiting_phone':
                            user_states[sender_id]['phone'] = message_text
                            user_states[sender_id]['state'] = 'waiting_service'
                            send_text_message(sender_id, "Milyen kezelés érdekli? (pl. tisztítás, tömés, implantátum)", access_token)
                        
                        elif state == 'waiting_service':
                            user_states[sender_id]['notes'] = message_text
                            
                            # Lead mentése
                            user_data = {
                                'name': user_states[sender_id]['name'],
                                'phone': user_states[sender_id]['phone'],
                                'notes': message_text,
                                'psid': sender_id
                            }
                            
                            print(f"📋 ÚJ LEAD: {user_data['name']} | {user_data['phone']} | {user_data['notes']}")
                            
                            # MENTÉS A SHEETS-BE
                            save_lead(page_id, page_info, user_data)
                            
                            confirmation = page_info.get('button1_link', 'Köszönjük! Hamarosan felvesszük Önnel a kapcsolatot!')
                            send_text_message(sender_id, confirmation, access_token)
                            
                            # Admin értesítés
                            if page_info.get('admin_psid'):
                                admin_message = f"🦷 ÚJ IDŐPONTFOGLALÁS\n\n👤 {user_data['name']}\n📞 {user_data['phone']}\n💬 {user_data['notes']}\n\n🕐 {datetime.now().strftime('%Y.%m.%d %H:%M')}"
                                send_text_message(page_info['admin_psid'], admin_message, access_token)
                            
                            del user_states[sender_id]
                        
                        continue
                    
                    # Welcome template
                    buttons = []
                    if page_info.get('button1_text'):
                        buttons.append({"type": "postback", "title": page_info['button1_text'][:20], "payload": "APPOINTMENT"})
                    if page_info.get('button2_text') and page_info.get('button2_link'):
                        buttons.append({"type": "postback", "title": page_info['button2_text'][:20], "payload": f"TEXT:{page_info['button2_link']}"})
                    if page_info.get('button3_text') and page_info.get('button3_link'):
                        buttons.append({"type": "postback", "title": page_info['button3_text'][:20], "payload": f"TEXT:{page_info['button3_link']}"})
                    
                    if buttons:
                        send_generic_template(sender_id, page_info.get('welcome_text', 'Üdvözöljük! 🦷'), buttons, access_token)
                    else:
                        send_text_message(sender_id, page_info.get('welcome_text', 'Üdvözöljük! 🦷'), access_token)
                
                if messaging_event.get('postback'):
                    payload = messaging_event['postback'].get('payload', '')
                    
                    if payload == 'GET_STARTED':
                        buttons = []
                        if page_info.get('button1_text'):
                            buttons.append({"type": "postback", "title": page_info['button1_text'][:20], "payload": "APPOINTMENT"})
                        if page_info.get('button2_text') and page_info.get('button2_link'):
                            buttons.append({"type": "postback", "title": page_info['button2_text'][:20], "payload": f"TEXT:{page_info['button2_link']}"})
                        if page_info.get('button3_text') and page_info.get('button3_link'):
                            buttons.append({"type": "postback", "title": page_info['button3_text'][:20], "payload": f"TEXT:{page_info['button3_link']}"})
                        
                        if buttons:
                            send_generic_template(sender_id, page_info.get('welcome_text', 'Üdvözöljük! 🦷'), buttons, access_token)
                        else:
                            send_text_message(sender_id, page_info.get('welcome_text', 'Üdvözöljük! 🦷'), access_token)
                    
                    elif payload == 'APPOINTMENT':
                        user_states[sender_id] = {'state': 'waiting_name', 'page_id': page_id}
                        send_text_message(sender_id, "Kérem, írja be a nevét! 😊", access_token)
                    
                    elif payload.startswith('TEXT:'):
                        response_text = payload[5:]
                        send_text_message(sender_id, response_text, access_token)
    
    return jsonify({"status": "ok"}), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        page_id = request.form.get('page_id')
        password = request.form.get('password')
        
        page_data = load_page_data()
        if page_id in page_data and page_data[page_id]['admin_password'] == password:
            # Ellenőrizzük az előfizetést
            if page_data[page_id].get('dashboard', '0') != '1':
                return render_template('login.html', error='📊 A Dashboard szolgáltatás eléréséhez kérjük, vegye fel velünk a kapcsolatot az előfizetés aktiválásához!')
            
            session['page_id'] = page_id
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Hibás page_id vagy jelszó!')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'page_id' not in session:
        return redirect(url_for('login'))
    
    page_id = session['page_id']
    page_data = load_page_data()
    
    if page_id not in page_data:
        return redirect(url_for('login'))
    
    # Leadek betöltése
    try:
        company_name = page_data[page_id].get('company_name', f'Ügyfél-{page_id[:6]}')
        spreadsheet = get_or_create_client_spreadsheet(page_id, company_name)
        
        if not spreadsheet:
            leads = []
            total_leads = 0
            pending_appointments = 0
            today_appointments = 0
            this_week_leads = 0
        else:
            sheet = spreadsheet.worksheet("Leads")
            all_leads = sheet.get_all_records()
            leads = [l for l in all_leads if str(l.get('page_id')) == str(page_id)]
            
            # Statisztikák
            total_leads = len(leads)
            pending_appointments = len([l for l in leads if not l.get('veglegesitett_idopont')])
            today = datetime.now().strftime('%Y.%m.%d')
            today_appointments = len([l for l in leads if l.get('veglegesitett_idopont', '').startswith(today)])
            
            # Ezen a héten érkezett
            from datetime import timedelta
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y.%m.%d')
            this_week_leads = len([l for l in leads if l.get('beerkezett', '') >= week_ago])
        
    except Exception as e:
        print(f"❌ Dashboard hiba: {e}")
        import traceback
        traceback.print_exc()
        leads = []
        total_leads = 0
        pending_appointments = 0
        today_appointments = 0
        this_week_leads = 0
    
    return render_template('dashboard_new.html', 
                         page_info=page_data[page_id], 
                         recent_leads=leads,
                         total_leads=total_leads,
                         pending_appointments=pending_appointments,
                         today_appointments=today_appointments,
                         this_week_leads=this_week_leads,
                         page_id=page_id)

@app.route('/foglalasok')
def foglalasok():
    if 'page_id' not in session:
        return redirect(url_for('login'))
    
    page_id = session['page_id']
    page_data = load_page_data()
    
    if page_id not in page_data:
        return redirect(url_for('login'))
    
    # Leadek betöltése
    try:
        company_name = page_data[page_id].get('company_name', f'Ügyfél-{page_id[:6]}')
        spreadsheet = get_or_create_client_spreadsheet(page_id, company_name)
        
        if spreadsheet:
            sheet = spreadsheet.worksheet("Leads")
            all_leads = sheet.get_all_records()
            leads = [l for l in all_leads if str(l.get('page_id')) == str(page_id)]
        else:
            leads = []
    except Exception as e:
        print(f"❌ Foglalások hiba: {e}")
        import traceback
        traceback.print_exc()
        leads = []
    
    return render_template('foglalasok.html', page_info=page_data[page_id], leads=leads, page_id=page_id)

@app.route('/betegek')
def betegek():
    if 'page_id' not in session:
        return redirect(url_for('login'))
    
    page_id = session['page_id']
    page_data = load_page_data()
    
    if page_id not in page_data:
        return redirect(url_for('login'))
    
    # Betegek betöltése
    try:
        company_name = page_data[page_id].get('company_name', f'Ügyfél-{page_id[:6]}')
        spreadsheet = get_or_create_client_spreadsheet(page_id, company_name)
        
        if not spreadsheet:
            patients = []
        else:
            # Patients lap
            patients_sheet = spreadsheet.worksheet("Patients")
            all_patients = patients_sheet.get_all_records()
            patients = [p for p in all_patients if str(p.get('page_id')) == str(page_id)]
            
            # Ha nincs beteg, akkor Leads-ből generálunk egyedi betegeket
            if not patients:
                leads_sheet = spreadsheet.worksheet("Leads")
                all_leads = leads_sheet.get_all_records()
                page_leads = [l for l in all_leads if str(l.get('page_id')) == str(page_id)]
                
                patients_dict = {}
                for lead in page_leads:
                    key = f"{lead.get('name')}_{lead.get('phone')}"
                    if key not in patients_dict:
                        patients_dict[key] = {
                            'beteg_id': lead.get('lead_id'),
                            'nev': lead.get('name'),
                            'telefon': lead.get('phone'),
                            'email': '',
                            'utolso_latogatas': lead.get('veglegesitett_idopont', ''),
                            'letrehozva': lead.get('beerkezett', '')
                        }
                
                patients = list(patients_dict.values())
        
    except Exception as e:
        print(f"❌ Betegek hiba: {e}")
        import traceback
        traceback.print_exc()
        patients = []
    
    return render_template('betegek.html', page_info=page_data[page_id], patients=patients, page_id=page_id)

@app.route('/naptar')
def naptar():
    if 'page_id' not in session:
        return redirect(url_for('login'))
    
    page_id = session['page_id']
    page_data = load_page_data()
    
    if page_id not in page_data:
        return redirect(url_for('login'))
    
    # Hónap paraméter (opcionális)
    month_offset = int(request.args.get('month', 0))
    
    # Naptár adatok
    try:
        company_name = page_data[page_id].get('company_name', f'Ügyfél-{page_id[:6]}')
        spreadsheet = get_or_create_client_spreadsheet(page_id, company_name)
        
        if not spreadsheet:
            calendar_days = []
            current_month = ''
            current_year = ''
        else:
            sheet = spreadsheet.worksheet("Leads")
            all_leads = sheet.get_all_records()
            leads = [l for l in all_leads if str(l.get('page_id')) == str(page_id) and l.get('veglegesitett_idopont')]
            
            # Aktuális hónap számítása
            from datetime import timedelta
            from calendar import monthrange
            
            today = datetime.now()
            target_date = today.replace(day=1) + timedelta(days=32*month_offset)
            target_date = target_date.replace(day=1)
            
            current_month = target_date.strftime('%B')
            current_year = target_date.year
            
            # Hónap napjainak száma
            days_in_month = monthrange(target_date.year, target_date.month)[1]
            first_weekday = target_date.weekday()  # 0=hétfő
            
            # Naptár napok generálása
            calendar_days = []
            
            # Üres napok a hónap elején
            for i in range(first_weekday):
                calendar_days.append({'day': '', 'is_today': False, 'appointments': []})
            
            # Hónap napjai
            for day in range(1, days_in_month + 1):
                day_date = target_date.replace(day=day)
                day_str = day_date.strftime('%Y.%m.%d')
                
                # Időpontok ezen a napon
                day_appointments = []
                for lead in leads:
                    apt_date = lead.get('veglegesitett_idopont', '').split(' ')[0] if lead.get('veglegesitett_idopont') else ''
                    if apt_date == day_str:
                        time_part = lead.get('veglegesitett_idopont', '').split(' ')[1] if ' ' in lead.get('veglegesitett_idopont', '') else ''
                        day_appointments.append({
                            'lead_id': lead.get('lead_id'),
                            'name': lead.get('name'),
                            'time': time_part
                        })
                
                is_today = (day_date.date() == today.date())
                calendar_days.append({
                    'day': day,
                    'is_today': is_today,
                    'appointments': day_appointments
                })
        
    except Exception as e:
        print(f"❌ Naptár hiba: {e}")
        import traceback
        traceback.print_exc()
        calendar_days = []
        current_month = ''
        current_year = ''
        month_offset = 0
    
    return render_template('naptar.html', 
                         page_info=page_data[page_id], 
                         calendar_days=calendar_days,
                         current_month=current_month,
                         current_year=current_year,
                         month_offset=month_offset,
                         page_id=page_id)

@app.route('/beteg/<lead_id>')
def beteg_reszletek(lead_id):
    if 'page_id' not in session:
        return redirect(url_for('login'))
    
    page_id = session['page_id']
    page_data = load_page_data()
    
    if page_id not in page_data:
        return redirect(url_for('login'))
    
    # Beteg adatok
    try:
        company_name = page_data[page_id].get('company_name', f'Ügyfél-{page_id[:6]}')
        spreadsheet = get_or_create_client_spreadsheet(page_id, company_name)
        
        if not spreadsheet:
            return "Hiba történt", 500
        
        sheet = spreadsheet.worksheet("Leads")
        all_leads = sheet.get_all_records()
        
        # Keressük meg a beteget
        patient = None
        for lead in all_leads:
            if lead.get('lead_id') == lead_id:
                patient = {
                    'beteg_id': lead.get('lead_id'),
                    'nev': lead.get('name'),
                    'telefon': lead.get('phone'),
                    'email': '',
                    'cim': '',
                    'szuletesi_datum': '',
                    'megjegyzesek': lead.get('megjegyzes', ''),
                    'letrehozva': lead.get('beerkezett', '')
                }
                break
        
        if not patient:
            return "Beteg nem található", 404
        
        # Időpontok
        appointments = [l for l in all_leads if l.get('phone') == patient['telefon']]
        
        # Kezelések betöltése
        treatments = []
        try:
            treatments_sheet = spreadsheet.worksheet('Treatments')
            all_treatments = treatments_sheet.get_all_records()
            treatments = [t for t in all_treatments if t.get('beteg_id') == lead_id and str(t.get('page_id')) == str(page_id)]
        except Exception as te:
            print(f"⚠️ Kezelések betöltési hiba: {te}")
            treatments = []
        
    except Exception as e:
        print(f"❌ Beteg részletek hiba: {e}")
        import traceback
        traceback.print_exc()
        return "Hiba történt", 500
    
    return render_template('beteg_reszletek.html', 
                         page_info=page_data[page_id], 
                         patient=patient,
                         appointments=appointments,
                         treatments=treatments,
                         page_id=page_id)

@app.route('/add-patient', methods=['POST'])
def add_patient():
    if 'page_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    page_id = session['page_id']
    page_data = load_page_data()
    
    try:
        # Beteg ID generálása
        beteg_id = f"BETEG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        
        # Adatok
        nev = request.form.get('nev', '')
        telefon = request.form.get('telefon', '')
        email = request.form.get('email', '')
        cim = request.form.get('cim', '')
        szuletesi_datum = request.form.get('szuletesi_datum', '')
        megjegyzesek = request.form.get('megjegyzesek', '')
        
        # Ügyfél Spreadsheet
        company_name = page_data.get(page_id, {}).get('company_name', f'Ügyfél-{page_id[:6]}')
        spreadsheet = get_or_create_client_spreadsheet(page_id, company_name)
        
        if not spreadsheet:
            return jsonify({"success": False, "error": "Spreadsheet hiba"}), 500
        
        # Patients lap
        sheet = spreadsheet.worksheet("Patients")
        
        # Sor hozzáadása: beteg_id, page_id, nev, telefon, email, cim, szuletesi_datum, megjegyzesek, letrehozva
        row = [beteg_id, page_id, nev, telefon, email, cim, szuletesi_datum, megjegyzesek, timestamp]
        sheet.append_row(row)
        
        print(f"✅ Beteg hozzáadva: {nev}")
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"❌ Beteg hozzáadási hiba: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/add-treatment', methods=['POST'])
def add_treatment():
    if 'page_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    page_id = session['page_id']
    page_data = load_page_data()
    
    try:
        # Kezelés ID generálása
        kezeles_id = f"KEZELES-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        
        # Adatok
        beteg_id = request.form.get('beteg_id', '')
        tipus = request.form.get('tipus', '')
        datum = request.form.get('datum', '')
        leiras = request.form.get('leiras', '')
        ar = request.form.get('ar', '')
        fizetve = '1' if request.form.get('fizetve') else '0'
        
        # Ügyfél Spreadsheet
        company_name = page_data.get(page_id, {}).get('company_name', f'Ügyfél-{page_id[:6]}')
        spreadsheet = get_or_create_client_spreadsheet(page_id, company_name)
        
        if not spreadsheet:
            return jsonify({"success": False, "error": "Spreadsheet hiba"}), 500
        
        # Treatments lap
        sheet = spreadsheet.worksheet("Treatments")
        
        # Sor hozzáadása: kezeles_id, page_id, beteg_id, tipus, datum, leiras, ar, fizetve, letrehozva
        row = [kezeles_id, page_id, beteg_id, tipus, datum, leiras, ar, fizetve, timestamp]
        sheet.append_row(row)
        
        print(f"✅ Kezelés hozzáadva: {tipus}")
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"❌ Kezelés hozzáadási hiba: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/bot-settings', methods=['GET', 'POST'])
def bot_settings():
    if 'page_id' not in session:
        return redirect(url_for('login'))
    
    page_id = session['page_id']
    page_data = load_page_data()
    
    if page_id not in page_data:
        return redirect(url_for('login'))
    
    success = False
    
    if request.method == 'POST':
        # Bot beállítások mentése a Config Sheets-be
        try:
            creds_dict = json.loads(GOOGLE_CREDENTIALS)
            creds = Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/drive.file'
                ]
            )
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SPREADSHEET_ID).sheet1
            
            # Keressük meg a page_id sorát
            cell = sheet.find(page_id)
            if cell:
                row = cell.row
                
                # Frissítjük az oszlopokat a VALÓDI sorrend szerint (1-gyel eltolva):
                # A=page_id(1), B=company_name(2), C=access_token(3), D=admin_password(4), E=welcome_text(5),
                # F=button1_text(6), G=button1_link(7), H=button2_text(8), I=button2_link(9), J=button3_text(10), K=button3_link(11), L=admin_psid(12)
                # DE a find() az A oszlopot találja (1), és onnan számol, szóval +1 kell mindenhova!
                sheet.update_cell(row, 5, request.form.get('welcome_text', ''))  # E (5)
                sheet.update_cell(row, 6, request.form.get('button1_text', ''))  # F (6)
                sheet.update_cell(row, 7, request.form.get('button1_link', ''))  # G (7)
                sheet.update_cell(row, 8, request.form.get('button2_text', ''))  # H (8)
                sheet.update_cell(row, 9, request.form.get('button2_link', ''))  # I (9)
                sheet.update_cell(row, 10, request.form.get('button3_text', ''))  # J (10)
                sheet.update_cell(row, 11, request.form.get('button3_link', ''))  # K (11)
                
                success = True
                
                # Cache frissítés
                global cached_page_data
                cached_page_data = {}
                
        except Exception as e:
            print(f"❌ Bot beállítások mentési hiba: {e}")
    
    # Friss adatok betöltése
    page_data = load_page_data()
    
    return render_template('bot_settings.html', page_info=page_data[page_id], page_id=page_id, success=success)

@app.route('/update-lead', methods=['POST'])
def update_lead():
    if 'page_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    page_id = session['page_id']
    page_data = load_page_data()
    
    try:
        lead_id = request.form.get('lead_id')
        idopont = request.form.get('idopont')
        
        # Ügyfél Spreadsheet
        company_name = page_data.get(page_id, {}).get('company_name', f'Ügyfél-{page_id[:6]}')
        spreadsheet = get_or_create_client_spreadsheet(page_id, company_name)
        
        if not spreadsheet:
            return jsonify({"success": False, "error": "Spreadsheet hiba"}), 500
        
        sheet = spreadsheet.worksheet("Leads")
        
        # Keressük meg a lead_id sorát
        cell = sheet.find(lead_id)
        if cell:
            row = cell.row
            # 8. oszlop: veglegesitett_idopont
            sheet.update_cell(row, 8, idopont)
            return jsonify({"success": True})
        
        return jsonify({"success": False, "error": "Lead not found"}), 404
        
    except Exception as e:
        print(f"❌ Lead frissítési hiba: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/logout')
def logout():
    session.pop('page_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 SmileScale indítása...")
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    print("🚀 SmileScale betöltve gunicorn-nal")

