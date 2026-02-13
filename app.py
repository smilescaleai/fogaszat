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

# CSV URL-ek a Google Sheets-ből
CONFIG_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO13uEpQukHL1hTzxeZUjGYPaUPQ7XaKTjVWnbhlh2KnvOztWLASO6Jmu8782-4vx0Dco64xEVi2pO/pub?output=csv"
LEADS_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSX4G6fWjzosvSlrgi3P93tKWRpwJFUsGUE6DadAIVtHiGy3W8Tbo3mwMj0S5JxOJ2jxb3XsnKkMuz2/pub?output=csv"

# Verify token
VERIFY_TOKEN = "smilescale_token_2026"

# Google Sheets setup
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
LEADS_SPREADSHEET_ID = os.environ.get('LEADS_SPREADSHEET_ID')
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS')

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

def generate_lead_id():
    """Egyedi Lead ID generálása"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"LEAD-{timestamp}"

def save_lead(page_id, page_info, user_data):
    """Lead mentése Google Form-on keresztül (automatikus Sheets írás)"""
    try:
        lead_id = generate_lead_id()
        timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        
        # Google Form URL (később beállítod)
        form_url = os.environ.get('GOOGLE_FORM_URL', '')
        
        if form_url:
            # Form submission
            form_data = {
                'entry.1': lead_id,
                'entry.2': timestamp,
                'entry.3': page_id,
                'entry.4': page_info.get('company_name', ''),
                'entry.5': user_data.get('name', ''),
                'entry.6': user_data.get('phone', ''),
                'entry.7': user_data.get('psid', ''),
                'entry.8': '',  # veglegesitett_idopont
                'entry.9': user_data.get('notes', '')
            }
            
            try:
                response = requests.post(form_url, data=form_data, timeout=5)
                print(f"✅ Lead mentve Form-on keresztül: {lead_id}")
                return True
            except Exception as e:
                print(f"⚠️ Form hiba: {e}")
        
        # Fallback: Sheets API
        client = get_sheets_client()
        if client:
            sheet = client.open_by_key(LEADS_SPREADSHEET_ID).sheet1
            
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
            
            sheet.append_row(row)
            print(f"✅ Lead mentve Sheets API-val: {lead_id}")
            return True
        
        print(f"⚠️ Lead csak logban: {lead_id} - {user_data.get('name')}")
        return True
        
    except Exception as e:
        print(f"❌ Lead mentési hiba: {e}")
        return False

def update_admin_psid(page_id, admin_psid):
    """Admin PSID visszaírása a Google Sheets táblázatba."""
    try:
        client = get_sheets_client()
        if not client:
            return False
        
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        cell = sheet.find(page_id)
        if cell:
            row = cell.row
            sheet.update_cell(row, 4, admin_psid)
            
            global cached_page_data
            if page_id in cached_page_data:
                cached_page_data[page_id]['admin_psid'] = admin_psid
            
            return True
        return False
    except Exception as e:
        print(f"❌ Hiba az admin PSID frissítésekor: {e}")
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
            access_token = str(row.get('access_token', '')).strip()
            admin_password = str(row.get('admin_password', '')).strip()
            admin_psid = str(row.get('admin_psid', '')).strip()
            welcome_text = str(row.get('welcome_text', '')).strip()
            company_name = str(row.get('company_name', '')).strip()
            
            button1_text = str(row.get('button1_text', '')).strip()
            button1_link = str(row.get('button1_link', '')).strip()
            button2_text = str(row.get('button2_text', '')).strip()
            button2_link = str(row.get('button2_link', '')).strip()
            button3_text = str(row.get('button3_text', '')).strip()
            button3_link = str(row.get('button3_link', '')).strip()
            
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
                    "button3_link": button3_link if button3_link else ''
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
    
    # Leadek betöltése CSV-ből
    try:
        print("📥 Leads CSV letöltése...")
        response = requests.get(LEADS_CSV_URL, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        csv_content = StringIO(response.text)
        reader = csv.DictReader(csv_content)
        
        all_leads = list(reader)
        leads = [l for l in all_leads if l.get('page_id') == page_id]
        print(f"✅ Leads CSV betöltve! {len(leads)} lead ehhez az oldalhoz.")
    except Exception as e:
        print(f"❌ Leads CSV hiba: {e}")
        leads = []
    
    return render_template('dashboard.html', page_info=page_data[page_id], leads=leads, page_id=page_id)

@app.route('/bot-settings')
def bot_settings():
    if 'page_id' not in session:
        return redirect(url_for('login'))
    
    page_id = session['page_id']
    page_data = load_page_data()
    
    if page_id not in page_data:
        return redirect(url_for('login'))
    
    return render_template('bot_settings.html', page_info=page_data[page_id], page_id=page_id)

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

