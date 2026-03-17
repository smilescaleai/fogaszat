# SmileScale Landing Page System

## 🚀 Gyors Indítás

### 1. Config Táblázat
- Töröld: `page_id`, `access_token`, `admin_psid`, `dashboard`
- Add hozzá: `company_slug` (első oszlop)
- Publikáld CSV-ként

### 2. Environment Változók
Ugyanazok, mint az eredeti rendszerben:
- `SECRET_KEY`
- `SPREADSHEET_ID`
- `LEADS_SPREADSHEET_ID`
- `GOOGLE_CREDENTIALS`

### 3. Deploy
```bash
cd landing
pip install -r requirements.txt
python app.py
```

## 📖 Dokumentáció
Részletes dokumentáció: `../landingdokumentacio/`

## 🌐 Használat
- Landing page: `https://yourdomain.com/smilescale`
- Admin login: `https://yourdomain.com/login`
