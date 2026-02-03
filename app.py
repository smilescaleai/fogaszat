import os
import re
import requests
from datetime import datetime
from flask import Flask, request
from pymongo import MongoClient

app = Flask(__name__)

# Konfiguráció
MONGO_URI = os.environ.get('MONGO_URI')
VERIFY_TOKEN = 'smilescale_token_2026'
GRAPH_API = 'https://graph.facebook.com/v18.0/me/messages'

# MongoDB kapcsolat DNS hibák ellen
try:
    client = MongoClient(
        MONGO_URI,
        connectTimeoutMS=30000,
        socketTimeoutMS=None,
        connect=False
    )
    db = client.smilescale
    print("✅ MongoDB kapcsolat inicializálva")
except Exception as e:
    print(f"❌ MongoDB hiba: {e}")
    db = None

def send_message(token, recipient_id, text):
    """Üzenet küldés Facebook Messengeren"""
    try:
        response = requests.post(
            f"{GRAPH_API}?access_token={token}",
            json={'recipient': {'id': recipient_id}, 'message': {'text': text}},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ Üzenetküldési hiba: {e}")
        return False

def get_page_config(page_id):
    """Oldal konfiguráció lekérése DB-ből"""
    try:
        return db.pages.find_one({'page_id': page_id})
    except Exception as e:
        print(f"⚠️ DB lekérési hiba: {e}")
        return None

def save_admin(page_id, admin_psid):
    """Admin PSID mentése DB-be"""
    try:
        db.pages.update_one(
            {'page_id': page_id},
            {'$set': {'admin_psid': admin_psid}}
        )
        return True
    except Exception as e:
        print(f"⚠️ Admin mentési hiba: {e}")
        return False

def save_lead(page_id, phone):
    """Lead mentése DB-be"""
    try:
        db.leads.insert_one({
            'page_id': page_id,
            'phone': phone,
            'timestamp': datetime.utcnow()
        })
        return True
    except Exception as e:
        print(f"⚠️ Lead mentési hiba: {e}")
        return False

def detect_phone(text):
    """Magyar telefonszám detektálás"""
    pattern = r'(\+?36|06)[\s\-]?[20|30|70]\d{7}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Webhook verifikáció"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print('✅ Webhook verified')
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook üzenetkezelés"""
    data = request.get_json()
    
    if not data or data.get('object') != 'page':
        return 'ok', 200
    
    for entry in data.get('entry', []):
        page_id = entry.get('id')
        
        # Oldal konfiguráció lekérése
        config = get_page_config(page_id)
        if not config:
            print(f"⚠️ Ismeretlen oldal: {page_id}")
            continue
        
        token = config.get('page_access_token')
        
        for event in entry.get('messaging', []):
            sender_id = event.get('sender', {}).get('id')
            message = event.get('message', {})
            text = message.get('text', '').strip()
            
            if not text:
                continue
            
            # ================================================================
            # ADMIN AZONOSÍTÁS: AUTH [jelszó]
            # ================================================================
            if text.upper().startswith('AUTH '):
                password = text[5:].strip()
                
                if password == config.get('admin_password'):
                    save_admin(page_id, sender_id)
                    send_message(token, sender_id, '✅ Sikeres azonosítás! Mostantól te kapod a leadeket ezen az oldalon.')
                    print(f"🔑 Új admin: {page_id} -> {sender_id}")
                else:
                    send_message(token, sender_id, '❌ Hibás jelszó!')
                continue
            
            # ================================================================
            # TELEFONSZÁM DETEKTÁLÁS ÉS LEAD GENERÁLÁS
            # ================================================================
            phone = detect_phone(text)
            if phone:
                # Lead mentése
                save_lead(page_id, phone)
                print(f"📞 Új lead: {page_id} -> {phone}")
                
                # Admin értesítése
                admin_psid = config.get('admin_psid')
                if admin_psid:
                    send_message(token, admin_psid, f'🔔 ÚJ PÁCIENS! Telefonszám: {phone}')
                    print(f"✅ Admin értesítve: {admin_psid}")
                
                # Visszajelzés a páciensnek
                send_message(token, sender_id, '✅ Köszönjük! Hamarosan felvesszük veled a kapcsolatot.')
                continue
            
            # ================================================================
            # AUTOMATA VÁLASZ: welcome_text
            # ================================================================
            welcome_text = config.get('welcome_text', 'Üdvözöllek! Írj egy telefonszámot és felvesszük veled a kapcsolatot.')
            send_message(token, sender_id, welcome_text)
    
    return 'ok', 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    db_status = 'connected' if db else 'disconnected'
    return {'status': 'ok', 'database': db_status}, 200

if __name__ == '__main__':
    print("=" * 70)
    print("🦷 SmileScale Fogászati Bot")
    print("=" * 70)
    print(f"🔐 Verify Token: {VERIFY_TOKEN}")
    print(f"🗄️  MongoDB: {'✅ Connected' if db else '❌ Disconnected'}")
    print("=" * 70)
    app.run(host='0.0.0.0', port=5000)
