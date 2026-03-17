import os
import csv
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from io import StringIO
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smilescale_landing_secret_2026')

# Version: 3.0 - Landing Page System (NO Facebook Messenger)

# Cached page data
cached_page_data = {}

# CSV URL a Google Sheets-ből (Config táblázat) - UGYANAZ MINT AZ EREDETI RENDSZERBEN
CONFIG_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRO13uEpQukHL1hTzxeZUjGYPaUPQ7XaKTjVWnbhlh2KnvOztWLASO6Jmu8782-4vx0Dco64xEVi2pO/pub?output=csv"

# Google Sheets setup
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')  # Config Sheet
MASTER_SPREADSHEET_ID = os.environ.get('LEADS_SPREADSHEET_ID')  # Master CRM Sheet
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS')

# Ügyfél lapok cache
client_worksheets = {}

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

def get_or_create_client_worksheet(company_slug, company_name, sheet_type="Leads"):
    """
    Ügyfél-specifikus worksheet (lap) lekérése vagy létrehozása a Master Spreadsheet-ben.
    Lap neve: {company_name}_{sheet_type} (pl: SmileScale_Leads)
    """
    global client_worksheets
    
    cache_key = f"{company_slug}_{sheet_type}"
    
    # Cache ellenőrzés
    if cache_key in client_worksheets:
        return client_worksheets[cache_key]
    
    try:
        client = get_sheets_client()
        if not client:
            return None
        
        # Master Spreadsheet megnyitása
        spreadsheet = client.open_by_key(MASTER_SPREADSHEET_ID)
        
        # Lap neve
        worksheet_name = f"{company_name}_{sheet_type}"
        
        # Próbáljuk megnyitni a meglévő lapot
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            print(f"✅ Meglévő lap: {worksheet_name}")
            client_worksheets[cache_key] = worksheet
            return worksheet
        except:
            pass
        
        # Ha nincs, létrehozzuk
        print(f"🆕 Új lap létrehozása: {worksheet_name}")
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)
        
        # Fejléc hozzáadása
        if sheet_type == "Leads":
            worksheet.append_row([
                'lead_id', 'beerkezett', 'company_slug', 'company_name', 
                'name', 'phone', 'email', 'veglegesitett_idopont', 'megjegyzes'
            ])
        elif sheet_type == "Patients":
            worksheet.append_row([
                'beteg_id', 'company_slug', 'nev', 'telefon', 'email', 
                'cim', 'szuletesi_datum', 'megjegyzesek', 'letrehozva'
            ])
        elif sheet_type == "Treatments":
            worksheet.append_row([
                'kezeles_id', 'company_slug', 'beteg_id', 'tipus', 'datum', 
                'leiras', 'ar', 'fizetve', 'letrehozva'
            ])
        
        print(f"✅ Lap létrehozva: {worksheet_name}")
        client_worksheets[cache_key] = worksheet
        return worksheet
        
    except Exception as e:
        print(f"❌ Worksheet létrehozási hiba: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_lead_id():
    """Egyedi Lead ID generálása"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"LEAD-{timestamp}"

def save_lead(company_slug, company_info, user_data):
    """Lead mentése Google Sheets táblába"""
    try:
        lead_id = generate_lead_id()
        timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        
        print(f"💾 Lead mentés: {user_data.get('name')}")
        
        # Ügyfél Leads lap lekérése/létrehozása
        company_name = company_info.get('company_name', company_slug)
        worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
        
        if not worksheet:
            print("❌ Worksheet hiba!")
            return False
        
        # 9 oszlop: lead_id, beerkezett, company_slug, company_name, name, phone, email, veglegesitett_idopont, megjegyzes
        row = [
            lead_id,
            timestamp,
            company_slug,
            company_info.get('company_name', ''),
            user_data.get('name', ''),
            user_data.get('phone', ''),
            user_data.get('email', ''),
            '',
            user_data.get('notes', '')
        ]
        
        print(f"📝 Sor írása: {row[:5]}...")
        worksheet.append_row(row)
        print(f"✅ Lead mentve: {lead_id}")
        return True
        
    except Exception as e:
        print(f"❌ Lead mentési hiba: {e}")
        import traceback
        traceback.print_exc()
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
            company_slug = str(row.get('company_slug', '')).strip().lower()
            company_name = str(row.get('company_name', '')).strip()
            admin_password = str(row.get('admin_password', '')).strip()
            welcome_text = str(row.get('welcome_text', '')).strip()
            
            button1_text = str(row.get('button1_text', '')).strip()
            button1_link = str(row.get('button1_link', '')).strip()
            button2_text = str(row.get('button2_text', '')).strip()
            button2_link = str(row.get('button2_link', '')).strip()
            button3_text = str(row.get('button3_text', '')).strip()
            button3_link = str(row.get('button3_link', '')).strip()
            
            if company_slug:
                page_data[company_slug] = {
                    "admin_password": admin_password if admin_password else '',
                    "welcome_text": welcome_text if welcome_text else 'Üdvözöljük! 🦷',
                    "company_name": company_name if company_name else company_slug.title(),
                    "button1_text": button1_text if button1_text else '',
                    "button1_link": button1_link if button1_link else '',
                    "button2_text": button2_text if button2_text else '',
                    "button2_link": button2_link if button2_link else '',
                    "button3_text": button3_text if button3_text else '',
                    "button3_link": button3_link if button3_link else ''
                }
        
        print(f"✅ Config CSV betöltve! {len(page_data)} oldal.")
        return page_data
    except Exception as e:
        print(f"❌ Config CSV hiba: {e}")
        return {}

@app.route('/')
def home():
    return "SmileScale Landing Page System Active", 200

@app.route('/<company_slug>')
def landing_page(company_slug):
    """Landing page egy adott céghez"""
    company_slug = company_slug.lower()
    
    # Friss adatok betöltése
    global cached_page_data
    if not cached_page_data:
        cached_page_data = load_page_data()
    
    if company_slug not in cached_page_data:
        return "Oldal nem található", 404
    
    company_info = cached_page_data[company_slug]
    
    return render_template('landing.html', 
                         company_info=company_info,
                         company_slug=company_slug)

@app.route('/<company_slug>/submit', methods=['POST'])
def submit_lead(company_slug):
    """Lead beküldése a landing page-ről"""
    company_slug = company_slug.lower()
    
    # Friss adatok betöltése
    global cached_page_data
    if not cached_page_data:
        cached_page_data = load_page_data()
    
    if company_slug not in cached_page_data:
        return jsonify({"success": False, "error": "Oldal nem található"}), 404
    
    company_info = cached_page_data[company_slug]
    
    try:
        user_data = {
            'name': request.form.get('name', ''),
            'phone': request.form.get('phone', ''),
            'email': request.form.get('email', ''),
            'notes': request.form.get('notes', '')
        }
        
        if not user_data['name'] or not user_data['phone']:
            return jsonify({"success": False, "error": "Név és telefon kötelező!"}), 400
        
        # Lead mentése
        success = save_lead(company_slug, company_info, user_data)
        
        if success:
            return jsonify({"success": True, "message": "Köszönjük! Hamarosan felvesszük Önnel a kapcsolatot!"})
        else:
            return jsonify({"success": False, "error": "Hiba történt a mentés során"}), 500
            
    except Exception as e:
        print(f"❌ Submit hiba: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ADMIN ROUTES (ugyanazok mint az eredeti rendszerben)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        company_slug = request.form.get('company_slug', '').lower()
        password = request.form.get('password')
        
        page_data = load_page_data()
        if company_slug in page_data and page_data[company_slug]['admin_password'] == password:
            session['company_slug'] = company_slug
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Hibás company slug vagy jelszó!')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'company_slug' not in session:
        return redirect(url_for('login'))
    
    company_slug = session['company_slug']
    
    # Mindig friss adatok
    global cached_page_data
    cached_page_data = {}
    page_data = load_page_data()
    
    if company_slug not in page_data:
        return redirect(url_for('login'))
    
    # Leadek betöltése
    try:
        company_name = page_data[company_slug].get('company_name', company_slug)
        worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
        
        if not worksheet:
            leads = []
            total_leads = 0
            pending_appointments = 0
            today_appointments = 0
            this_week_leads = 0
        else:
            all_leads = worksheet.get_all_records()
            leads = [l for l in all_leads if str(l.get('company_slug')) == str(company_slug)]
            
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
                         page_info=page_data[company_slug], 
                         recent_leads=leads,
                         total_leads=total_leads,
                         pending_appointments=pending_appointments,
                         today_appointments=today_appointments,
                         this_week_leads=this_week_leads,
                         company_slug=company_slug)

@app.route('/foglalasok')
def foglalasok():
    if 'company_slug' not in session:
        return redirect(url_for('login'))
    
    company_slug = session['company_slug']
    
    # Mindig friss adatok
    global cached_page_data
    cached_page_data = {}
    page_data = load_page_data()
    
    if company_slug not in page_data:
        return redirect(url_for('login'))
    
    # Leadek betöltése
    try:
        company_name = page_data[company_slug].get('company_name', company_slug)
        worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
        
        if worksheet:
            all_leads = worksheet.get_all_records()
            leads = [l for l in all_leads if str(l.get('company_slug')) == str(company_slug)]
        else:
            leads = []
    except Exception as e:
        print(f"❌ Foglalások hiba: {e}")
        import traceback
        traceback.print_exc()
        leads = []
    
    return render_template('foglalasok.html', page_info=page_data[company_slug], leads=leads, company_slug=company_slug)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 SmileScale Landing Page System indítása...")
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    print("🚀 SmileScale Landing Page System betöltve gunicorn-nal")


@app.route('/betegek')
def betegek():
    if 'company_slug' not in session:
        return redirect(url_for('login'))
    
    company_slug = session['company_slug']
    
    # Mindig friss adatok
    global cached_page_data
    cached_page_data = {}
    page_data = load_page_data()
    
    if company_slug not in page_data:
        return redirect(url_for('login'))
    
    # Betegek betöltése
    try:
        company_name = page_data[company_slug].get('company_name', company_slug)
        patients_worksheet = get_or_create_client_worksheet(company_slug, company_name, "Patients")
        
        if not patients_worksheet:
            patients = []
        else:
            all_patients = patients_worksheet.get_all_records()
            patients = [p for p in all_patients if str(p.get('company_slug')) == str(company_slug)]
            
            # Ha nincs beteg, akkor Leads-ből generálunk egyedi betegeket
            if not patients:
                leads_worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
                if leads_worksheet:
                    all_leads = leads_worksheet.get_all_records()
                    page_leads = [l for l in all_leads if str(l.get('company_slug')) == str(company_slug)]
                    
                    patients_dict = {}
                    for lead in page_leads:
                        key = f"{lead.get('name')}_{lead.get('phone')}"
                        if key not in patients_dict:
                            patients_dict[key] = {
                                'beteg_id': lead.get('lead_id'),
                                'nev': lead.get('name'),
                                'telefon': lead.get('phone'),
                                'email': lead.get('email', ''),
                                'utolso_latogatas': lead.get('veglegesitett_idopont', ''),
                                'letrehozva': lead.get('beerkezett', '')
                            }
                    
                    patients = list(patients_dict.values())
        
    except Exception as e:
        print(f"❌ Betegek hiba: {e}")
        import traceback
        traceback.print_exc()
        patients = []
    
    return render_template('betegek.html', page_info=page_data[company_slug], patients=patients, company_slug=company_slug)

@app.route('/naptar')
def naptar():
    if 'company_slug' not in session:
        return redirect(url_for('login'))
    
    company_slug = session['company_slug']
    
    # Mindig friss adatok
    global cached_page_data
    cached_page_data = {}
    page_data = load_page_data()
    
    if company_slug not in page_data:
        return redirect(url_for('login'))
    
    # Hét paraméter (opcionális)
    week_offset = int(request.args.get('week', 0))
    
    # Időpontok generálása (8:00 - 20:00, félóránként)
    time_slots = []
    for hour in range(8, 20):
        time_slots.append(f"{hour:02d}:00")
        time_slots.append(f"{hour:02d}:30")
    
    # Naptár adatok
    try:
        from datetime import timedelta
        
        company_name = page_data[company_slug].get('company_name', company_slug)
        
        # Betegek betöltése
        patients_worksheet = get_or_create_client_worksheet(company_slug, company_name, "Patients")
        if patients_worksheet:
            all_patients = patients_worksheet.get_all_records()
            patients = [p for p in all_patients if str(p.get('company_slug')) == str(company_slug)]
        else:
            patients = []
        
        # Ha nincs beteg, Leads-ből generálunk
        if not patients:
            leads_worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
            if leads_worksheet:
                all_leads = leads_worksheet.get_all_records()
                page_leads = [l for l in all_leads if str(l.get('company_slug')) == str(company_slug)]
                
                patients_dict = {}
                for lead in page_leads:
                    key = f"{lead.get('name')}_{lead.get('phone')}"
                    if key not in patients_dict:
                        patients_dict[key] = {
                            'beteg_id': lead.get('lead_id'),
                            'nev': lead.get('name'),
                            'telefon': lead.get('phone')
                        }
                
                patients = list(patients_dict.values())
        
        # Időpontok betöltése
        worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
        
        if not worksheet:
            week_days = []
            week_start = ''
            week_end = ''
        else:
            all_leads = worksheet.get_all_records()
            leads = [l for l in all_leads if str(l.get('company_slug')) == str(company_slug) and l.get('veglegesitett_idopont')]
            
            # Aktuális hét számítása
            today = datetime.now()
            week_start_date = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
            
            week_days = []
            day_names = ['Hétfő', 'Kedd', 'Szerda', 'Csütörtök', 'Péntek', 'Szombat', 'Vasárnap']
            
            for i in range(7):
                day_date = week_start_date + timedelta(days=i)
                day_str = day_date.strftime('%Y.%m.%d')
                
                # Időpontok ezen a napon
                day_appointments = []
                for lead in leads:
                    apt_datetime = lead.get('veglegesitett_idopont', '')
                    if apt_datetime:
                        parts = apt_datetime.split(' ')
                        if len(parts) >= 2:
                            apt_date = parts[0]
                            apt_time = parts[1]
                            if apt_date == day_str:
                                day_appointments.append({
                                    'lead_id': lead.get('lead_id'),
                                    'name': lead.get('name'),
                                    'time': apt_time
                                })
                
                is_today = (day_date.date() == today.date())
                week_days.append({
                    'day_name': day_names[i],
                    'day_number': day_date.day,
                    'date': day_str,
                    'is_today': is_today,
                    'appointments': day_appointments
                })
            
            week_start = week_start_date.strftime('%Y.%m.%d')
            week_end = (week_start_date + timedelta(days=6)).strftime('%Y.%m.%d')
        
    except Exception as e:
        print(f"❌ Naptár hiba: {e}")
        import traceback
        traceback.print_exc()
        week_days = []
        week_start = ''
        week_end = ''
        week_offset = 0
        patients = []
    
    return render_template('naptar.html', 
                         page_info=page_data[company_slug], 
                         week_days=week_days,
                         week_start=week_start,
                         week_end=week_end,
                         week_offset=week_offset,
                         time_slots=time_slots,
                         patients=patients,
                         company_slug=company_slug)

@app.route('/beteg/<lead_id>')
def beteg_reszletek(lead_id):
    if 'company_slug' not in session:
        return redirect(url_for('login'))
    
    company_slug = session['company_slug']
    
    # Mindig friss adatok
    global cached_page_data
    cached_page_data = {}
    page_data = load_page_data()
    
    if company_slug not in page_data:
        return redirect(url_for('login'))
    
    # Beteg adatok
    try:
        company_name = page_data[company_slug].get('company_name', company_slug)
        
        # Először próbáljuk a Patients lapból
        patient = None
        patients_worksheet = get_or_create_client_worksheet(company_slug, company_name, "Patients")
        if patients_worksheet:
            all_patients = patients_worksheet.get_all_records()
            for p in all_patients:
                if str(p.get('beteg_id')) == str(lead_id):
                    patient = {
                        'beteg_id': p.get('beteg_id'),
                        'nev': p.get('nev'),
                        'telefon': p.get('telefon'),
                        'email': p.get('email', ''),
                        'cim': p.get('cim', ''),
                        'szuletesi_datum': p.get('szuletesi_datum', ''),
                        'megjegyzesek': p.get('megjegyzesek', ''),
                        'letrehozva': p.get('letrehozva', '')
                    }
                    break
        
        # Ha nincs a Patients-ben, keressük a Leads-ben
        if not patient:
            leads_worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
            if not leads_worksheet:
                return "Hiba történt", 500
            
            all_leads = leads_worksheet.get_all_records()
            
            for lead in all_leads:
                if str(lead.get('lead_id')) == str(lead_id):
                    patient = {
                        'beteg_id': lead.get('lead_id'),
                        'nev': lead.get('name'),
                        'telefon': lead.get('phone'),
                        'email': lead.get('email', ''),
                        'cim': '',
                        'szuletesi_datum': '',
                        'megjegyzesek': lead.get('megjegyzes', ''),
                        'letrehozva': lead.get('beerkezett', '')
                    }
                    break
        
        if not patient:
            print(f"❌ Beteg nem található: {lead_id}")
            return "Beteg nem található", 404
        
        # Időpontok (Leads-ből)
        leads_worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
        if leads_worksheet:
            all_leads = leads_worksheet.get_all_records()
            appointments = [l for l in all_leads if str(l.get('phone')) == str(patient['telefon'])]
        else:
            appointments = []
        
        # Kezelések betöltése
        treatments = []
        try:
            treatments_sheet = get_or_create_client_worksheet(company_slug, company_name, "Treatments")
            if treatments_sheet:
                all_treatments = treatments_sheet.get_all_records()
                treatments = [t for t in all_treatments if str(t.get('beteg_id')) == str(lead_id) and str(t.get('company_slug')) == str(company_slug)]
        except Exception as te:
            print(f"⚠️ Kezelések betöltési hiba: {te}")
            treatments = []
        
    except Exception as e:
        print(f"❌ Beteg részletek hiba: {e}")
        import traceback
        traceback.print_exc()
        return "Hiba történt", 500
    
    return render_template('beteg_reszletek.html', 
                         page_info=page_data[company_slug], 
                         patient=patient,
                         appointments=appointments,
                         treatments=treatments,
                         company_slug=company_slug)

@app.route('/add-patient', methods=['POST'])
def add_patient():
    if 'company_slug' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    company_slug = session['company_slug']
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
        company_name = page_data.get(company_slug, {}).get('company_name', company_slug)
        
        # Patients lap
        sheet = get_or_create_client_worksheet(company_slug, company_name, "Patients")
        
        if not sheet:
            return jsonify({"success": False, "error": "Spreadsheet hiba"}), 500
        
        # Sor hozzáadása: beteg_id, company_slug, nev, telefon, email, cim, szuletesi_datum, megjegyzesek, letrehozva
        row = [beteg_id, company_slug, nev, telefon, email, cim, szuletesi_datum, megjegyzesek, timestamp]
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
    if 'company_slug' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    company_slug = session['company_slug']
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
        company_name = page_data.get(company_slug, {}).get('company_name', company_slug)
        
        # Treatments lap
        sheet = get_or_create_client_worksheet(company_slug, company_name, "Treatments")
        
        if not sheet:
            return jsonify({"success": False, "error": "Spreadsheet hiba"}), 500
        
        # Sor hozzáadása: kezeles_id, company_slug, beteg_id, tipus, datum, leiras, ar, fizetve, letrehozva
        row = [kezeles_id, company_slug, beteg_id, tipus, datum, leiras, ar, fizetve, timestamp]
        sheet.append_row(row)
        
        print(f"✅ Kezelés hozzáadva: {tipus}")
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"❌ Kezelés hozzáadási hiba: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/update-lead', methods=['POST'])
def update_lead():
    if 'company_slug' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    company_slug = session['company_slug']
    page_data = load_page_data()
    
    try:
        lead_id = request.form.get('lead_id')
        idopont = request.form.get('idopont')
        
        # Ügyfél Spreadsheet
        company_name = page_data.get(company_slug, {}).get('company_name', company_slug)
        worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
        
        if not worksheet:
            return jsonify({"success": False, "error": "Spreadsheet hiba"}), 500
        
        # Keressük meg a lead_id sorát
        cell = worksheet.find(lead_id)
        if cell:
            row = cell.row
            # 8. oszlop: veglegesitett_idopont
            worksheet.update_cell(row, 8, idopont)
            return jsonify({"success": True})
        
        return jsonify({"success": False, "error": "Lead not found"}), 404
        
    except Exception as e:
        print(f"❌ Lead frissítési hiba: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/add-appointment', methods=['POST'])
def add_appointment():
    if 'company_slug' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    company_slug = session['company_slug']
    page_data = load_page_data()
    
    try:
        date = request.form.get('date')
        time = request.form.get('time')
        patient_type = request.form.get('patient_type')
        megjegyzes = request.form.get('megjegyzes', '')
        
        company_name = page_data.get(company_slug, {}).get('company_name', company_slug)
        
        # Időpont formázása
        idopont = f"{date} {time}"
        
        if patient_type == 'existing':
            # Meglévő beteg
            beteg_id = request.form.get('beteg_id')
            
            if not beteg_id:
                return jsonify({"success": False, "error": "Válasszon beteget"}), 400
            
            # Beteg adatok lekérése
            patients_worksheet = get_or_create_client_worksheet(company_slug, company_name, "Patients")
            if patients_worksheet:
                all_patients = patients_worksheet.get_all_records()
                patient = next((p for p in all_patients if str(p.get('beteg_id')) == str(beteg_id)), None)
                
                if patient:
                    name = patient.get('nev')
                    phone = patient.get('telefon')
                    email = patient.get('email', '')
                else:
                    # Ha nincs Patients-ben, keressük Leads-ben
                    leads_worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
                    if leads_worksheet:
                        all_leads = leads_worksheet.get_all_records()
                        lead = next((l for l in all_leads if str(l.get('lead_id')) == str(beteg_id)), None)
                        if lead:
                            name = lead.get('name')
                            phone = lead.get('phone')
                            email = lead.get('email', '')
                        else:
                            return jsonify({"success": False, "error": "Beteg nem található"}), 404
                    else:
                        return jsonify({"success": False, "error": "Beteg nem található"}), 404
            else:
                return jsonify({"success": False, "error": "Beteg nem található"}), 404
            
        else:
            # Új beteg
            name = request.form.get('new_name')
            phone = request.form.get('new_phone')
            email = ''
            
            if not name or not phone:
                return jsonify({"success": False, "error": "Név és telefon kötelező"}), 400
        
        # Lead mentése
        lead_id = generate_lead_id()
        timestamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
        
        worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
        if not worksheet:
            return jsonify({"success": False, "error": "Spreadsheet hiba"}), 500
        
        # 9 oszlop: lead_id, beerkezett, company_slug, company_name, name, phone, email, veglegesitett_idopont, megjegyzes
        row = [
            lead_id,
            timestamp,
            company_slug,
            company_name,
            name,
            phone,
            email,
            idopont,
            megjegyzes
        ]
        
        worksheet.append_row(row)
        
        print(f"✅ Időpont hozzáadva: {name} - {idopont}")
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"❌ Időpont hozzáadási hiba: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/delete-lead', methods=['POST'])
def delete_lead():
    if 'company_slug' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    company_slug = session['company_slug']
    page_data = load_page_data()
    
    try:
        lead_id = request.form.get('lead_id')
        
        company_name = page_data.get(company_slug, {}).get('company_name', company_slug)
        worksheet = get_or_create_client_worksheet(company_slug, company_name, "Leads")
        
        if not worksheet:
            return jsonify({"success": False, "error": "Spreadsheet hiba"}), 500
        
        # Keressük meg a lead_id sorát
        cell = worksheet.find(lead_id)
        if cell:
            worksheet.delete_rows(cell.row)
            print(f"✅ Lead törölve: {lead_id}")
            return jsonify({"success": True})
        
        return jsonify({"success": False, "error": "Lead not found"}), 404
        
    except Exception as e:
        print(f"❌ Lead törlési hiba: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/delete-patient', methods=['POST'])
def delete_patient():
    if 'company_slug' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    company_slug = session['company_slug']
    page_data = load_page_data()
    
    try:
        beteg_id = request.form.get('beteg_id')
        
        company_name = page_data.get(company_slug, {}).get('company_name', company_slug)
        worksheet = get_or_create_client_worksheet(company_slug, company_name, "Patients")
        
        if not worksheet:
            return jsonify({"success": False, "error": "Spreadsheet hiba"}), 500
        
        # Keressük meg a beteg_id sorát
        cell = worksheet.find(beteg_id)
        if cell:
            worksheet.delete_rows(cell.row)
            print(f"✅ Beteg törölve: {beteg_id}")
            return jsonify({"success": True})
        
        return jsonify({"success": False, "error": "Patient not found"}), 404
        
    except Exception as e:
        print(f"❌ Beteg törlési hiba: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/delete-treatment', methods=['POST'])
def delete_treatment():
    if 'company_slug' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    company_slug = session['company_slug']
    page_data = load_page_data()
    
    try:
        kezeles_id = request.form.get('kezeles_id')
        
        company_name = page_data.get(company_slug, {}).get('company_name', company_slug)
        worksheet = get_or_create_client_worksheet(company_slug, company_name, "Treatments")
        
        if not worksheet:
            return jsonify({"success": False, "error": "Spreadsheet hiba"}), 500
        
        # Keressük meg a kezeles_id sorát
        cell = worksheet.find(kezeles_id)
        if cell:
            worksheet.delete_rows(cell.row)
            print(f"✅ Kezelés törölve: {kezeles_id}")
            return jsonify({"success": True})
        
        return jsonify({"success": False, "error": "Treatment not found"}), 404
        
    except Exception as e:
        print(f"❌ Kezelés törlési hiba: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/logout')
def logout():
    session.pop('company_slug', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 SmileScale Landing Page System indítása...")
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    print("🚀 SmileScale Landing Page System betöltve gunicorn-nal")
