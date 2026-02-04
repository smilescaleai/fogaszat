import os
import requests
import pandas as pd
from flask import Flask, request, jsonify
from io import StringIO

app = Flask(__name__)

# Admin felhasználók tárolása (PSID alapján, page_id szerint csoportosítva)
admin_users = {}

# CSV URL a Google Sheets-ből
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO13uEpQukHL1hTzxeZUjGYPaUPQ7XaKTjVWnbhlh2KnvOztWLASO6Jmu8782-4vx0Dco64xEVi2pO/pub?output=csv"

# Verify token
VERIFY_TOKEN = "smilescale_token_2026"

def load_page_data():
    """
    Letölti és feldolgozza a CSV fájlt a Google Sheets-ből pandas használatával.
    Visszaad egy szótárat: {page_id: {"access_token": "...", "admin_password": "...", "welcome_text": "...", stb.}}
    """
    try:
        print("📥 CSV letöltése a Google Sheets-ből...")
        response = requests.get(CSV_URL, timeout=10)
        response.raise_for_status()
        
        # Pandas DataFrame létrehozása
        df = pd.read_csv(StringIO(response.text))
        
        # Oszlopnevek tisztítása (whitespace eltávolítása)
        df.columns = df.columns.str.strip()
        
        page_data = {}
        for _, row in df.iterrows():
            page_id = str(row.get('page_id', '')).strip()
            access_token = str(row.get('access_token', '')).strip()
            admin_password = str(row.get('admin_password', '')).strip()
            welcome_text = str(row.get('welcome_text', '')).strip()
            
            # Gombok adatai
            button1_text = str(row.get('button1_text', '')).strip()
            button1_link = str(row.get('button1_link', '')).strip()
            button2_text = str(row.get('button2_text', '')).strip()
            button2_link = str(row.get('button2_link', '')).strip()
            button3_text = str(row.get('button3_text', '')).strip()
            button3_link = str(row.get('button3_link', '')).strip()
            
            # NaN értékek kezelése
            if page_id and page_id != 'nan' and access_token and access_token != 'nan':
                page_data[page_id] = {
                    "access_token": access_token,
                    "admin_password": admin_password if admin_password != 'nan' else '',
                    "welcome_text": welcome_text if welcome_text != 'nan' else '',
                    "button1_text": button1_text if button1_text != 'nan' else '',
                    "button1_link": button1_link if button1_link != 'nan' else '',
                    "button2_text": button2_text if button2_text != 'nan' else '',
                    "button2_link": button2_link if button2_link != 'nan' else '',
                    "button3_text": button3_text if button3_text != 'nan' else '',
                    "button3_link": button3_link if button3_link != 'nan' else ''
                }
                button_count = len([b for b in [button1_text, button2_text, button3_text] if b and b != 'nan'])
                print(f"✅ Oldal betöltve: {page_id} (gombok: {button_count})")
        
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

@app.route('/', methods=['GET'])
def verify():
    """
    Facebook Webhook hitelesítés (GET kérés).
    FIX: Ha nincs hub.verify_token paraméter, egyszerű OK választ ad.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    # Ha nincsenek webhook paraméterek, egyszerű health check
    if not token and not mode and not challenge:
        print("✅ Health check kérés - SmileScale Server OK")
        return "SmileScale Server OK", 200
    
    print(f"🔐 Webhook hitelesítési kérés: mode={mode}, token={token}")
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("✅ Webhook hitelesítés sikeres!")
        return challenge, 200
    else:
        print("❌ Webhook hitelesítés sikertelen!")
        return 'Forbidden', 403

@app.route('/', methods=['POST'])
def webhook():
    """
    Facebook Webhook eseménykezelés (POST kérés).
    """
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
                    
                    # Admin regisztráció ellenőrzése
                    if message_text == admin_password and admin_password:
                        # Admin hozzáadása
                        if page_id not in admin_users:
                            admin_users[page_id] = set()
                        admin_users[page_id].add(sender_id)
                        
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
                        
                        # 1. gomb
                        if page_info.get('button1_text') and page_info.get('button1_link'):
                            buttons.append({
                                "type": "web_url",
                                "url": page_info['button1_link'],
                                "title": page_info['button1_text']
                            })
                        
                        # 2. gomb
                        if page_info.get('button2_text') and page_info.get('button2_link'):
                            buttons.append({
                                "type": "web_url",
                                "url": page_info['button2_link'],
                                "title": page_info['button2_text']
                            })
                        
                        # 3. gomb
                        if page_info.get('button3_text') and page_info.get('button3_link'):
                            buttons.append({
                                "type": "web_url",
                                "url": page_info['button3_link'],
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
    
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 SmileScale Webhook szerver indítása a {port} porton...")
    app.run(host='0.0.0.0', port=port, debug=False)
