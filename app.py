import os
import re
import csv
from datetime import datetime
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Konfiguráció - Cseréld ki a saját értékeidre
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN', 'YOUR_PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = 'f4fF3a4K9G55sF'
ADMIN_PSID = os.environ.get('ADMIN_PSID', 'YOUR_ADMIN_PSID')  # Doki Facebook PSID

# Állapotkezelés - memóriában (production-ben Redis/DB ajánlott)
user_states = {}

# Facebook Messenger API URL
MESSENGER_API_URL = f'https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}'

def send_message(recipient_id, message_text):
    """Egyszerű szöveges üzenet küldése"""
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    response = requests.post(MESSENGER_API_URL, json=payload)
    return response.json()

def send_buttons(recipient_id, text, buttons):
    """Gombok küldése"""
    payload = {
        'recipient': {'id': recipient_id},
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'button',
                    'text': text,
                    'buttons': buttons
                }
            }
        }
    }
    response = requests.post(MESSENGER_API_URL, json=payload)
    return response.json()

def send_main_menu(recipient_id):
    """Főmenü gombok küldése"""
    buttons = [
        {'type': 'postback', 'title': '💰 Árak', 'payload': 'PRICES'},
        {'type': 'postback', 'title': '📍 Helyszín', 'payload': 'LOCATION'},
        {'type': 'postback', 'title': '📅 Időpontkérés', 'payload': 'APPOINTMENT'}
    ]
    send_buttons(recipient_id, 'Miben segíthetek?', buttons)

def validate_phone(phone):
    """Telefonszám validálás (magyar formátum)"""
    # Elfogadja: +36301234567, 06301234567, 0630-123-4567, stb.
    pattern = r'^(\+36|06)?[-\s]?[0-9]{1,2}[-\s]?[0-9]{3}[-\s]?[0-9]{3,4}$'
    return re.match(pattern, phone.strip())

def save_lead(psid, name, phone):
    """Lead mentése CSV fájlba"""
    file_exists = os.path.isfile('leads.csv')
    
    with open('leads.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Dátum', 'PSID', 'Név', 'Telefonszám'])
        writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), psid, name, phone])

def get_user_profile(psid):
    """Felhasználó nevének lekérése Facebook API-ból"""
    url = f'https://graph.facebook.com/v18.0/{psid}?fields=first_name,last_name&access_token={PAGE_ACCESS_TOKEN}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return f"{data.get('first_name', '')} {data.get('last_name', '')}"
    return 'Ismeretlen'

def notify_admin(patient_name, phone):
    """Doki értesítése új időpontról"""
    message = f"🔔 Új időpontkérés!\n\n👤 Név: {patient_name}\n📞 Telefon: {phone}"
    send_message(ADMIN_PSID, message)

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Webhook verifikáció"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print('Webhook verified!')
        return challenge, 200
    else:
        return 'Verification failed', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook üzenetek kezelése"""
    data = request.get_json()
    
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                sender_id = messaging_event['sender']['id']
                
                # Postback kezelése (gombok)
                if messaging_event.get('postback'):
                    handle_postback(sender_id, messaging_event['postback'])
                
                # Szöveges üzenet kezelése
                elif messaging_event.get('message'):
                    handle_message(sender_id, messaging_event['message'])
    
    return 'ok', 200

def handle_postback(sender_id, postback):
    """Gomb kattintások kezelése"""
    payload = postback.get('payload')
    
    if payload == 'PRICES':
        send_message(sender_id, '💰 Áraink:\n\n• Konzultáció: 15.000 Ft\n• Kezelés: 25.000 Ft\n• Csomag (5 alkalom): 100.000 Ft')
        send_main_menu(sender_id)
    
    elif payload == 'LOCATION':
        send_message(sender_id, '📍 Helyszín:\n\n1234 Budapest, Példa utca 12.\n\nNyitvatartás:\nH-P: 9:00-18:00\nSzo: 9:00-13:00')
        send_main_menu(sender_id)
    
    elif payload == 'APPOINTMENT':
        user_states[sender_id] = 'waiting_for_phone'
        send_message(sender_id, '📅 Időpontfoglalás\n\nKérlek add meg a telefonszámodat, és hamarosan felvesszük veled a kapcsolatot!')

def handle_message(sender_id, message):
    """Szöveges üzenetek kezelése"""
    text = message.get('text', '').strip()
    
    # Ha időpontkérés módban van
    if user_states.get(sender_id) == 'waiting_for_phone':
        if validate_phone(text):
            # Telefonszám elfogadva
            user_name = get_user_profile(sender_id)
            save_lead(sender_id, user_name, text)
            notify_admin(user_name, text)
            
            send_message(sender_id, '✅ Köszönjük! Telefonszámod rögzítettük.\n\nHamarosan felvesszük veled a kapcsolatot az időpont egyeztetéséhez.')
            user_states[sender_id] = None
            send_main_menu(sender_id)
        else:
            # Hibás formátum
            send_message(sender_id, '❌ Kérlek adj meg egy érvényes telefonszámot!\n\nPélda: +36301234567 vagy 06301234567')
    else:
        # Alapértelmezett válasz
        send_message(sender_id, f'Üdv! 👋\n\n{text}')
        send_main_menu(sender_id)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
