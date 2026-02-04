import os
import csv
import requests
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
    Letölti és feldolgozza a CSV fájlt a Google Sheets-ből.
    Visszaad egy szótárat: {page_id: {"access_token": "...", "admin_password": "..."}}
    """
    try:
        print("📥 CSV letöltése a Google Sheets-ből...")
        response = requests.get(CSV_URL, timeout=10)
        response.raise_for_status()
        
        csv_content = StringIO(response.text)
        reader = csv.DictReader(csv_content)
        
        page_data = {}
        for row in reader:
            page_id = row.get('page_id', '').strip()
            access_token = row.get('access_token', '').strip()
            admin_password = row.get('admin_password', '').strip()
            
            if page_id and access_token:
                page_data[page_id] = {
                    "access_token": access_token,
                    "admin_password": admin_password
                }
                print(f"✅ Oldal betöltve: {page_id}")
        
        print(f"✅ CSV sikeresen betöltve! Összesen {len(page_data)} oldal.")
        return page_data
    
    except Exception as e:
        print(f"❌ Hiba a CSV letöltése során: {e}")
        return {}

def send_message(page_id, recipient_id, message_text, access_token):
    """
    Üzenet küldése a Facebook Messenger API-n keresztül.
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
        print(f"📤 Üzenet küldése a felhasználónak (PSID: {recipient_id})...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"✅ Üzenet sikeresen elküldve! Válasz: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Hiba az üzenet küldése során: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"❌ API válasz: {e.response.text}")
        return False

@app.route('/', methods=['GET'])
def verify():
    """
    Facebook Webhook hitelesítés (GET kérés).
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    print(f"🔐 Hitelesítési kérés érkezett: mode={mode}, token={token}")
    
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
                
                access_token = page_data[page_id]['access_token']
                admin_password = page_data[page_id]['admin_password']
                
                print(f"✅ Access token megtalálva a {page_id} oldalhoz!")
                
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
                    
                    # Ellenőrizzük, hogy admin-e a felhasználó
                    elif page_id in admin_users and sender_id in admin_users[page_id]:
                        print(f"👑 Admin felhasználó üzenete!")
                        response_text = f"Admin mód aktív: {message_text}"
                    
                    else:
                        print(f"👤 Normál felhasználó üzenete.")
                        response_text = "A SmileScale AI rendszere aktív ezen az oldalon! 🦷"
                    
                    # Válasz küldése
                    send_message(page_id, sender_id, response_text, access_token)
    
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 SmileScale Webhook szerver indítása a {port} porton...")
    app.run(host='0.0.0.0', port=port, debug=False)
