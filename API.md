# SmileScale CRM - API Dokumentáció

## Végpontok

### 1. Nyilvános Végpontok

#### `GET /`
- **Leírás**: Szerver státusz ellenőrzés
- **Válasz**: `"SmileScale Server Active"`
- **Használat**: Healthcheck

#### `GET /webhook`
- **Leírás**: Facebook webhook verification
- **Paraméterek**:
  - `hub.mode`: "subscribe"
  - `hub.verify_token`: "smilescale_token_2026"
  - `hub.challenge`: visszaküldendő érték
- **Válasz**: Challenge string vagy 403

#### `POST /webhook`
- **Leírás**: Facebook Messenger üzenetek fogadása
- **Body**: Facebook webhook payload
- **Funkciók**:
  - Get Started gomb kezelés
  - Időpontfoglalás folyamat
  - Gomb kattintások kezelése
  - Admin regisztráció
  - Lead mentés Sheets-be

### 2. Autentikált Végpontok (Session szükséges)

#### `GET /login`
- **Leírás**: Bejelentkezési oldal
- **Válasz**: Login form HTML

#### `POST /login`
- **Leírás**: Bejelentkezés
- **Body**:
  - `page_id`: Facebook oldal ID
  - `password`: Admin jelszó
- **Válasz**: Redirect `/dashboard` vagy hiba
- **Ellenőrzések**:
  - Page ID + jelszó egyezés
  - Dashboard előfizetés (M oszlop = 1)

#### `GET /dashboard`
- **Leírás**: Dashboard statisztikákkal
- **Session**: `page_id` szükséges
- **Adatok**:
  - Összes beteg
  - Függőben lévő foglalások
  - Mai időpontok
  - Heti leadek
  - 5 legutóbbi foglalás

#### `GET /foglalasok`
- **Leírás**: Összes foglalás listája
- **Session**: `page_id` szükséges
- **Funkciók**:
  - Keresés név/telefon alapján
  - Időpont beállítás modal
  - Auto-refresh (30 sec)

#### `GET /betegek`
- **Leírás**: Beteg adatbázis
- **Session**: `page_id` szükséges
- **Funkciók**:
  - Egyedi betegek listája
  - Keresés
  - Manuális beteg hozzáadás

#### `GET /naptar`
- **Leírás**: Naptár nézet
- **Session**: `page_id` szükséges
- **Query paraméterek**:
  - `month`: Hónap offset (0 = aktuális, -1 = előző, +1 = következő)
- **Funkciók**:
  - Havi naptár
  - Időpontok megjelenítése
  - Navigáció

#### `GET /beteg/<lead_id>`
- **Leírás**: Beteg részletek
- **Session**: `page_id` szükséges
- **Paraméterek**:
  - `lead_id`: Beteg azonosító
- **Adatok**:
  - Beteg alapadatok
  - Időpontok
  - Kezelési történet

#### `GET /bot-settings`
- **Leírás**: Bot beállítások oldal
- **Session**: `page_id` szükséges

#### `POST /bot-settings`
- **Leírás**: Bot beállítások mentése
- **Session**: `page_id` szükséges
- **Body**:
  - `welcome_text`: Üdvözlő szöveg
  - `button1_text`, `button1_link`: 1. gomb
  - `button2_text`, `button2_link`: 2. gomb
  - `button3_text`, `button3_link`: 3. gomb
- **Mentés**: Google Sheets Config lap (E-K oszlopok)

#### `POST /update-lead`
- **Leírás**: Időpont beállítása
- **Session**: `page_id` szükséges
- **Body**:
  - `lead_id`: Lead azonosító
  - `idopont`: Formátum: "2026.02.14 15:30"
- **Mentés**: Leads sheet H oszlop (veglegesitett_idopont)
- **Válasz**: `{"success": true}` vagy hiba

#### `POST /add-patient`
- **Leírás**: Új beteg hozzáadása
- **Session**: `page_id` szükséges
- **Body**:
  - `nev`: Név (kötelező)
  - `telefon`: Telefonszám (kötelező)
  - `email`: Email (opcionális)
  - `cim`: Cím (opcionális)
  - `szuletesi_datum`: Születési dátum (opcionális)
  - `megjegyzesek`: Megjegyzések (opcionális)
- **Mentés**: Patients sheet vagy Leads sheet
- **Válasz**: `{"success": true}` vagy hiba

#### `POST /add-treatment`
- **Leírás**: Új kezelés hozzáadása
- **Session**: `page_id` szükséges
- **Body**:
  - `beteg_id`: Beteg azonosító (kötelező)
  - `tipus`: Kezelés típusa (kötelező)
  - `datum`: Dátum (kötelező)
  - `leiras`: Leírás (opcionális)
  - `ar`: Ár Ft-ban (opcionális)
  - `fizetve`: Checkbox (1 vagy üres)
- **Mentés**: Treatments sheet
- **Válasz**: `{"success": true}` vagy hiba

#### `GET /logout`
- **Leírás**: Kijelentkezés
- **Válasz**: Redirect `/login`

## Adatfolyamatok

### Időpontfoglalás Flow

```
User → Messenger → Facebook → /webhook (POST)
  ↓
Bot kérdések (név, telefon, panasz)
  ↓
save_lead() → Leads Sheet (Sheets API)
  ↓
Admin értesítés (Messenger)
  ↓
Megerősítés usernek
```

### Dashboard Login Flow

```
User → /login (GET) → Login form
  ↓
User → /login (POST) → page_id + password
  ↓
load_page_data() → Config CSV
  ↓
Ellenőrzés: jelszó + dashboard előfizetés
  ↓
Session['page_id'] = page_id
  ↓
Redirect → /dashboard
```

### Időpont Beállítás Flow

```
User → /foglalasok → Kattintás sorra
  ↓
Modal megnyílik (JavaScript)
  ↓
User → Dátum/idő választás → Submit
  ↓
/update-lead (POST) → Sheets API
  ↓
Leads sheet H oszlop frissül
  ↓
Page reload → Frissített adat
```

### Beteg Hozzáadás Flow

```
User → /betegek → "Új beteg" gomb
  ↓
Modal megnyílik (JavaScript)
  ↓
User → Űrlap kitöltés → Submit
  ↓
/add-patient (POST) → Sheets API
  ↓
Patients sheet vagy Leads sheet
  ↓
Page reload → Új beteg a listában
```

## Google Sheets Műveletek

### Config Betöltés (CSV)
- **Funkció**: `load_page_data()`
- **Forrás**: CSV URL (nyilvános)
- **Cache**: `cached_page_data` dictionary
- **Frissítés**: Szerver restart vagy cache clear

### Leads Műveletek (Sheets API)
- **Mentés**: `save_lead()` → append_row()
- **Olvasás**: `get_all_records()` → filter by page_id
- **Frissítés**: `update_cell()` → veglegesitett_idopont

### Bot Beállítások Mentés (Sheets API)
- **Funkció**: `/bot-settings` POST
- **Művelet**: `find()` page_id → `update_cell()` E-K oszlopok
- **Cache clear**: `cached_page_data = {}`

### Admin PSID Mentés (Sheets API)
- **Funkció**: `update_admin_psid()`
- **Művelet**: `find()` page_id → `update_cell()` L oszlop (12)
- **Cache frissítés**: `cached_page_data[page_id]['admin_psid'] = admin_psid`

## Hibakezelés

### Általános Hibák
- **401 Unauthorized**: Session hiányzik → Redirect `/login`
- **404 Not Found**: Beteg/lead nem található
- **500 Internal Server Error**: Sheets API hiba, traceback a logs-ban

### Sheets API Hibák
- **Permission Denied**: Service account nincs megosztva
- **Spreadsheet Not Found**: Rossz Spreadsheet ID
- **Worksheet Not Found**: Rossz tab név (pl. "Patients")

### Facebook API Hibák
- **Invalid Access Token**: Lejárt vagy rossz token
- **Rate Limit**: Túl sok üzenet rövid időn belül
- **Webhook Verification Failed**: Rossz verify token

## Biztonsági Megfontolások

### Session Kezelés
- Flask session cookie
- `SECRET_KEY` environment variable
- HttpOnly cookie (XSS védelem)

### Adatvédelem
- Config: CSV (nyilvános, de nem érzékeny)
- Leads/Patients/Treatments: Sheets API (biztonságos)
- PII (név, telefon, email): Csak Sheets API-n keresztül

### Előfizetés Ellenőrzés
- Login-nál: `dashboard` oszlop = 1
- Ha 0: Hibaüzenet, nincs hozzáférés

### CSRF Védelem
- Flask session alapú
- Same-origin policy

## Teljesítmény

### Cache Stratégia
- Config: `cached_page_data` (szerver restart-ig)
- Leads: Minden kérésnél friss adat (Sheets API)

### Auto-Refresh
- Foglalások: 30 sec (ha modal nincs nyitva)
- Dashboard: Manuális refresh

### Rate Limiting
- Facebook: ~100 üzenet/sec/page
- Sheets API: 100 kérés/100 sec/user

---

**Verzió**: 2.0  
**Utolsó frissítés**: 2026.02.14
