import os
import re
import requests
from datetime import datetime
from flask import Flask, request
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URI = os.environ.get('MONGO_URI')
client = pymongo.MongoClient(MONGO_URI)
VERIFY_TOKEN = 'smilescale_token_2026'
MESSENGER_API = 'https://graph.facebook.com/v18.0/me/messages'

# MongoDB kapcsolat
try:
    client = MongoClient(MONGO_URI)
    db = client.smilescale
    print("✅ MongoDB kapcsolat sikeres")
except Exception as e:
    print(f"❌ MongoDB hiba: {e}")
    db = None

# Állapotkezelés (memória - egyszerű verzió)
user_states = {}

def send_message(token, recipient_id, text):
    """Üzenet küldés Messengeren"""
    try:
        response = requests.post(
            f"{MESSENGER_API}?access_token={token}",
            json={'recipient': {'id': recipient_id}, 'message': {'text': text}},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def get_page_config(page_id):
    """Oldal konfiguráció lekérése DB-ből"""
    try:
        return db.pages.find_one({'page_id': page_id})
    except:
        return None

def save_admin(page_id, admin_psid):
    """Admin PSID mentése"""
    try:
        db.pages.update_one(
            {'page_id': page_id},
            {'$set': {'admin_psid': admin_psid, 'admin_updated_at': datetime.utcnow()}}
        )
        return True
    except:
        return False

def save_lead(page_id, name, phone, psid):
    """Lead mentése DB-be"""
    try:
        db.leads.insert_one({
            'page_id': page_id,
            'name': name,
            'phone': phone,
            'psid': psid,
            'created_at': datetime.utcnow()
        })
        return True
    except:
        return False

def detect_phone(text):
    """Telefonszám detektálás"""
    match = re.search(r'(\+?[0-9\s-]{7,20})', text)
    return match.group(1).strip() if match else None

@app.route('/webhook', methods=['GET'])
def verify():
    """Webhook verifikáció"""
    if request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge'), 200
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
            continue  # Ismeretlen oldal - ignoráljuk
        
        token = config.get('page_access_token')
        
        for event in entry.get('messaging', []):
            sender_id = event.get('sender', {}).get('id')
            message = event.get('message', {})
            text = message.get('text', '').strip()
            
            if not text:
                continue
            
            # AUTH parancs kezelése
            if text.upper().startswith('AUTH '):
                password = text[5:].strip()
                if password == config.get('admin_password'):
                    save_admin(page_id, sender_id)
                    send_message(token, sender_id, '✅ Sikeres azonosítás! Mostantól te kapod a leadeket ezen az oldalon.')
                    print(f"🔑 Új admin: {page_id} -> {sender_id}")
                else:
                    send_message(token, sender_id, '❌ Hibás jelszó!')
                continue
            
            # Állapot inicializálás
            if sender_id not in user_states:
                user_states[sender_id] = {'page_id': page_id, 'state': 'start', 'data': {}}
            
            state = user_states[sender_id]
            
            # Kezdő állapot - welcome text
            if state['state'] == 'start':
                welcome = config.get('welcome_text', 'Üdv! Kérlek add meg a neved:')
                send_message(token, sender_id, welcome)
                state['state'] = 'waiting_name'
            
            # Név bekérés
            elif state['state'] == 'waiting_name':
                state['data']['name'] = text
                send_message(token, sender_id, f'Köszönöm, {text}! Add meg a telefonszámodat:')
                state['state'] = 'waiting_phone'
            
            # Telefonszám bekérés
            elif state['state'] == 'waiting_phone':
                phone = detect_phone(text)
                if phone:
                    name = state['data'].get('name', 'Ismeretlen')
                    
                    # Lead mentése
                    save_lead(page_id, name, phone, sender_id)
                    
                    # Visszajelzés páciensnek
                    send_message(token, sender_id, f'✅ Köszönjük, {name}! Hamarosan felvesszük veled a kapcsolatot.')
                    
                    # Admin értesítése
                    admin_psid = config.get('admin_psid')
                    if admin_psid:
                        send_message(token, admin_psid, f'🔔 ÚJ PÁCIENS!\n\n👤 Név: {name}\n📞 Tel: {phone}\n🆔 PSID: {sender_id}')
                        print(f"✅ Admin értesítve: {page_id}")
                    
                    # Állapot törlése
                    del user_states[sender_id]
                else:
                    send_message(token, sender_id, '❌ Kérlek adj meg egy érvényes telefonszámot!')
    
    return 'ok', 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'db': 'connected' if db else 'disconnected'}, 200

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Smilescale Multi-Tenant Bot")
    print("=" * 60)
    print(f"🔐 Verify Token: {VERIFY_TOKEN}")
    print(f"🗄️  MongoDB: {'✅ Connected' if db else '❌ Disconnected'}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)


