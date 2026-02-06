import os
import csv
import json
import requests
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from flask import Flask, request, jsonify
from io import StringIO

app = Flask(__name__)

# Admin felhasználók tárolása (PSID alapján, page_id szerint csoportosítva)
admin_users = {}

# Felhasználói állapotok tárolása (időpontfoglaláshoz)
user_states = {}

# CSV URL a Google Sheets-ből
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO13uEpQukHL1hTzxeZUjGYPaUPQ7XaKTjVWnbhlh2KnvOztWLASO6Jmu8782-4vx0Dco64xEVi2pO/pub?output=csv"

# Verify token
VERIFY_TOKEN = "smilescale_token_2026"

# Google Sheets setup
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS')

def get_sheets_client():
    """
    Google Sheets API kliens létrehozása.
    """
    try:
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"❌ Hiba a Google Sheets kliens létrehozásakor: {e}")
        return None

def update_admin_psid(page_id, admin_psid):
    """
    Admin PSID visszaírása a Google Sheets táblázatba.
    """
    try:
        client = get_sheets_client()
        if not client:
            return False
        
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        # Keressük meg a page_id-t tartalmazó sort
        cell = sheet.find(page_id)
        if cell:
            row = cell.row
            # admin_psid a D oszlopba (4. oszlop)
            sheet.update_cell(row, 4, admin_psid)
            print(f"✅ Admin PSID frissítve a táblázatban: {page_id} -> {admin_psid}")
            return True
        else:
            print(f"❌ Nem található page_id a táblázatban: {page_id}")
            return False
    except Exception as e:
        print(f"❌ Hiba az admin PSID frissítésekor: {e}")
        return False

def load_page_data():
    """
    Letölti és feldolgozza a CSV fájlt a Google Sheets-ből.
    Visszaad egy szótárat: {page_id: {"access_token": "...", "admin_password": "...", "admin_psid": "...", stb.}}
    """
    try:
        print("📥 CSV letöltése a Google Sheets-ből...")
        response = requests.get(CSV_URL, timeout=10)
        response.raise_for_status()
        
        # UTF-8 encoding beállítása
        response.encoding = 'utf-8'
        
        csv_content = StringIO(response.text)
        reader = csv.DictReader(csv_content)
        
        page_data = {}
        for row in reader:
            page_id = str(row.get('page_id', '')).strip()
            access_token = str(row.get('access_token', '')).strip()
            admin_password = str(row.get('admin_password', '')).strip()
            admin_psid = str(row.get('admin_psid', '')).strip()
            admin_phone = str(row.get('admin_phone', '')).strip()
            welcome_text = str(row.get('welcome_text', '')).strip()
            
            # Gombok adatai
            button1_text = str(row.get('button1_text', '')).strip()
            button1_link = str(row.get('button1_link', '')).strip()
            button2_text = str(row.get('button2_text', '')).strip()
            button2_link = str(row.get('button2_link', '')).strip()
            button3_text = str(row.get('button3_text', '')).strip()
            button3_link = str(row.get('button3_link', '')).strip()
            
            if page_id and access_token:
                page_data[page_id] = {
                    "access_token": access_token,
                    "admin_password": admin_password,
                    "admin_psid": admin_psid,
                    "admin_phone": admin_phone,
                    "welcome_text": welcome_text,
                    "button1_text": button1_text,
                    "button1_link": button1_link,
                    "button2_text": button2_text,
                    "button2_link": button2_link,
                    "button3_text": button3_text,
                    "button3_link": button3_link
                }
                button_count = len([b for b in [button1_text, button2_text, button3_text] if b])
                print(f"✅ Oldal betöltve: {page_id} (gombok: {button_count}, admin: {'✓' if admin_psid else '✗'})")
                
                # Admin betöltése memóriába
                if admin_psid:
                    if page_id not in admin_users:
                        admin_users[page_id] = set()
                    admin_users[page_id].add(admin_psid)
        
        print(f"✅ CSV sikeresen betöltve! Összesen {len(page_data)} oldal.")
        return page_data
    
    except Exception as e:
        print(f"❌ Hiba a CSV letöltése során: {e}")
        return {}

def send_text_message(recipient_id, message_text, access_token):
    """
    Egyszerű szöveges üzenet küldése (adminoknak).
    """
    url = f"https://graph.facebook.com/v18.0/me/messages"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "access_token": access_token
    }
    
    try:
        print(f"📤 Szöveges üzenet küldése (PSID: {recipient_id})...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"✅ Üzenet sikeresen elküldve!")
        return True
    except Exception as e:
        print(f"❌ Hiba az üzenet küldése során: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"❌ API válasz: {e.response.text}")
        return False

def send_generic_template(recipient_id, welcome_text, buttons, access_token):
    """
    Generic Template küldése gombokkal (normál felhasználóknak).
    """
    url = f"https://graph.facebook.com/v18.0/me/messages"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Generic Template struktúra
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": welcome_text,
                            "buttons": buttons
                        }
                    ]
                }
            }
        },
        "access_token": access_token
    }
    
    try:
        print(f"📤 Generic Template küldése gombokkal (PSID: {recipient_id})...")
        print(f"🎯 Gombok száma: {len(buttons)}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"✅ Template sikeresen elküldve!")
        return True
    except Exception as e:
        print(f"❌ Hiba a template küldése során: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"❌ API válasz: {e.response.text}")
        return False

@app.route('/')
def home():
    """
    Főoldal - egyszerű ellenőrző.
    """
    return "SmileScale Server Active", 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """
    Facebook Webhook - GET: hitelesítés, POST: üzenetkezelés.
    """
    # GET kérés - Facebook hitelesítés
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        print(f"🔐 Webhook hitelesítési kérés: mode={mode}, token={token}")
        
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("✅ Webhook hitelesítés sikeres!")
            return challenge, 200
        else:
            print("❌ Webhook hitelesítés sikertelen!")
            return 'Forbidden', 403
    
    # POST kérés - Üzenetkezelés
    data = request.get_json()
    print(f"📨 Webhook esemény érkezett: {data}")
    
    # CSV adatok betöltése minden kérésnél
    page_data = load_page_data()
    
    if not page_data:
        print("❌ Nem sikerült betölteni az oldal adatokat!")
        return jsonify({"status": "error", "message": "CSV betöltési hiba"}), 500
    
    # Esemény feldolgozása
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                sender_id = messaging_event['sender']['id']
                recipient_id = messaging_event['recipient']['id']
                
                # A recipient_id a page_id
                page_id = recipient_id
                
                print(f"👤 Üzenet küldője (PSID): {sender_id}")
                print(f"📄 Oldal ID (page_id): {page_id}")
                
                # Ellenőrizzük, hogy van-e access token ehhez az oldalhoz
                if page_id not in page_data:
                    print(f"❌ Nem található access token a {page_id} oldalhoz!")
                    continue
                
                page_info = page_data[page_id]
                access_token = page_info['access_token']
                admin_password = page_info['admin_password']
                
                print(f"✅ Üzenet érkezett a következő oldalra: {page_id}")
                
                # Üzenet feldolgozása
                if messaging_event.get('message'):
                    message_text = messaging_event['message'].get('text', '')
                    message_id = messaging_event['message'].get('mid', 'N/A')
                    
                    print(f"💬 Beérkező üzenet ID: {message_id}")
                    print(f"💬 Üzenet szövege: {message_text}")
                    
                    # Ellenőrizzük, hogy van-e aktív állapot (időpontfoglalás folyamatban)
                    if sender_id in user_states:
                        state = user_states[sender_id]['state']
                        
                        if state == 'waiting_name':
                            # Név mentése
                            user_states[sender_id]['name'] = message_text
                            user_states[sender_id]['state'] = 'waiting_phone'
                            print(f"📝 Név mentve: {message_text}")
                            send_text_message(sender_id, "Köszönöm! Kérem, írja be a telefonszámát!", access_token)
                        
                        elif state == 'waiting_phone':
                            # Telefonszám mentése
                            user_states[sender_id]['phone'] = message_text
                            user_states[sender_id]['state'] = 'waiting_complaint'
                            print(f"📞 Telefonszám mentve: {message_text}")
                            send_text_message(sender_id, "Köszönöm! Miben segíthetünk? (pl. fogfájás, tisztítás, ellenőrzés)", access_token)
                        
                        elif state == 'waiting_complaint':
                            # Panasz mentése és feldolgozás
                            complaint = message_text
                            name = user_states[sender_id]['name']
                            phone = user_states[sender_id]['phone']
                            
                            print(f"💬 Panasz mentve: {complaint}")
                            print(f"✅ Időpontfoglalás teljes: {name}, {phone}, {complaint}")
                            
                            # Admin értesítése
                            if page_info.get('admin_psid'):
                                admin_psid = page_info['admin_psid']
                                timestamp = datetime.now().strftime("%Y.%m.%d %H:%M")
                                admin_message = f"🦷 ÚJ IDŐPONTFOGLALÁS\n\n👤 Név: {name}\n📞 Telefon: {phone}\n💬 Panasz: {complaint}\n\n🕐 {timestamp}"
                                send_text_message(admin_psid, admin_message, access_token)
                                print(f"✅ Admin értesítve: {admin_psid}")
                            
                            # Megerősítő üzenet a usernek
                            confirmation = page_info.get('button1_link', 'Köszönjük! Hamarosan felvesszük Önnel a kapcsolatot!')
                            send_text_message(sender_id, confirmation, access_token)
                            
                            # Állapot törlése
                            del user_states[sender_id]
                        
                        continue
                    
                    # Admin regisztráció ellenőrzése
                    if message_text == admin_password and admin_password:
                        # Admin hozzáadása
                        if page_id not in admin_users:
                            admin_users[page_id] = set()
                        admin_users[page_id].add(sender_id)
                        
                        # Admin PSID visszaírása a táblázatba
                        update_admin_psid(page_id, sender_id)
                        
                        print(f"👑 Új admin regisztrálva! PSID: {sender_id}, Oldal: {page_id}")
                        response_text = f"Admin mód aktív: {message_text}"
                        send_text_message(sender_id, response_text, access_token)
                    
                    # Ellenőrizzük, hogy admin-e a felhasználó
                    elif page_id in admin_users and sender_id in admin_users[page_id]:
                        print(f"👑 Admin felhasználó üzenete!")
                        response_text = f"Admin mód aktív: {message_text}"
                        send_text_message(sender_id, response_text, access_token)
                    
                    else:
                        print(f"👤 Normál felhasználó üzenete - Generic Template küldése...")
                        
                        # Gombok összeállítása a CSV adatokból
                        buttons = []
                        
                        # 1. gomb - Időpontfoglalás (postback)
                        if page_info.get('button1_text'):
                            buttons.append({
                                "type": "postback",
                                "title": page_info['button1_text'],
                                "payload": "APPOINTMENT"
                            })
                        
                        # 2. gomb - Árlista (postback)
                        if page_info.get('button2_text') and page_info.get('button2_link'):
                            buttons.append({
                                "type": "postback",
                                "title": page_info['button2_text'],
                                "payload": f"TEXT:{page_info['button2_link']}"
                            })
                        
                        # 3. gomb - Sürgős eset (web_url - tárcsázás)
                        if page_info.get('button3_text') and page_info.get('admin_phone'):
                            buttons.append({
                                "type": "web_url",
                                "url": f"tel:{page_info['admin_phone']}",
                                "title": page_info['button3_text']
                            })
                        
                        # Welcome text
                        welcome_text = page_info.get('welcome_text', 'A SmileScale AI rendszere aktív ezen az oldalon! 🦷')
                        
                        # Ha vannak gombok, Generic Template-et küldünk
                        if buttons:
                            send_generic_template(sender_id, welcome_text, buttons, access_token)
                        else:
                            # Ha nincsenek gombok, egyszerű szöveget küldünk
                            print("⚠️ Nincsenek gombok definiálva, szöveges üzenet küldése...")
                            send_text_message(sender_id, welcome_text, access_token)
                
                # Postback feldolgozása (gomb megnyomása)
                if messaging_event.get('postback'):
                    payload = messaging_event['postback'].get('payload', '')
                    postback_title = messaging_event['postback'].get('title', '')
                    
                    print(f"🔘 Postback érkezett: {postback_title}")
                    print(f"📦 Payload: {payload}")
                    
                    # Get Started gomb
                    if payload == 'GET_STARTED':
                        print(f"🎉 Get Started gomb megnyomva!")
                        
                        # Gombok összeállítása
                        buttons = []
                        
                        if page_info.get('button1_text'):
                            buttons.append({
                                "type": "postback",
                                "title": page_info['button1_text'],
                                "payload": "APPOINTMENT"
                            })
                        
                        if page_info.get('button2_text') and page_info.get('button2_link'):
                            buttons.append({
                                "type": "postback",
                                "title": page_info['button2_text'],
                                "payload": f"TEXT:{page_info['button2_link']}"
                            })
                        
                        if page_info.get('button3_text') and page_info.get('admin_phone'):
                            buttons.append({
                                "type": "web_url",
                                "url": f"tel:{page_info['admin_phone']}",
                                "title": page_info['button3_text']
                            })
                        
                        welcome_text = page_info.get('welcome_text', 'A SmileScale AI rendszere aktív ezen az oldalon! 🦷')
                        
                        if buttons:
                            send_generic_template(sender_id, welcome_text, buttons, access_token)
                        else:
                            send_text_message(sender_id, welcome_text, access_token)
                    
                    # Időpontfoglalás indítása
                    elif payload == 'APPOINTMENT':
                        print(f"📅 Időpontfoglalás indítása: {sender_id}")
                        user_states[sender_id] = {
                            'state': 'waiting_name',
                            'page_id': page_id
                        }
                        send_text_message(sender_id, "Kérem, írja be a nevét!", access_token)
                    
                    # Szöveges válasz (árlista, stb.)
                    elif payload.startswith('TEXT:'):
                        response_text = payload[5:]  # "TEXT:" eltávolítása
                        print(f"📝 Szöveges válasz küldése: {response_text[:50]}...")
                        
                        # Admin ellenőrzés
                        if page_id in admin_users and sender_id in admin_users[page_id]:
                            send_text_message(sender_id, f"Admin mód aktív: {response_text}", access_token)
                        else:
                            send_text_message(sender_id, response_text, access_token)
                    
                    # Egyéb postback (régi kompatibilitás)
                    else:
                        if page_id in admin_users and sender_id in admin_users[page_id]:
                            response_text = f"Admin mód aktív: {payload}"
                            send_text_message(sender_id, response_text, access_token)
                        else:
                            send_text_message(sender_id, payload, access_token)
                
                # Messaging optin (első üzenet küldése gomb megnyomása)
                if messaging_event.get('optin'):
                    print(f"🎉 Új felhasználó - Üzenet küldése gomb megnyomva!")
                    
                    # Gombok összeállítása
                    buttons = []
                    
                    if page_info.get('button1_text'):
                        buttons.append({
                            "type": "postback",
                            "title": page_info['button1_text'],
                            "payload": "APPOINTMENT"
                        })
                    
                    if page_info.get('button2_text') and page_info.get('button2_link'):
                        buttons.append({
                            "type": "postback",
                            "title": page_info['button2_text'],
                            "payload": f"TEXT:{page_info['button2_link']}"
                        })
                    
                    if page_info.get('button3_text') and page_info.get('admin_phone'):
                        buttons.append({
                            "type": "web_url",
                            "url": f"tel:{page_info['admin_phone']}",
                            "title": page_info['button3_text']
                        })
                    
                    welcome_text = page_info.get('welcome_text', 'A SmileScale AI rendszere aktív ezen az oldalon! 🦷')
                    
                    if buttons:
                        send_generic_template(sender_id, welcome_text, buttons, access_token)
                    else:
                        send_text_message(sender_id, welcome_text, access_token)
    
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 SmileScale Webhook szerver indítása a {port} porton...")
    app.run(host='0.0.0.0', port=port, debug=False)
