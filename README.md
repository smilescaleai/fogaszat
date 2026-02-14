# SmileScale CRM - Teljes Fogászati Rendszer 🦷

## Funkciók

### 🤖 Messenger Bot
✅ **Get Started gomb** - Első üzenetként welcome text + gombok  
✅ **Időpontfoglalás** - Név, telefon, panasz bekérése lépésről lépésre  
✅ **Testreszabható gombok** - 3 gomb szöveges válaszokkal  
✅ **Admin rendszer** - Google Sheets API-val admin_psid visszaírás  
✅ **Multi-page** - Több Facebook oldal kezelése  
✅ **UTF-8 encoding** - Magyar ékezetek támogatása  

### 📊 Dashboard & CRM
✅ **Dashboard** - Statisztikák, legutóbbi foglalások  
✅ **Foglalások** - Összes időpontfoglalás kezelése, időpont beállítás  
✅ **Betegek** - Beteg adatbázis, manuális beteg hozzáadás  
✅ **Naptár** - Időpontok naptár nézetben, hónap navigáció  
✅ **Bot Beállítások** - Bot üzenetek és gombok szerkesztése  
✅ **Kezelési történet** - Betegenkénti kezelések, árak, fizetési státusz  
✅ **Előfizetés kezelés** - Dashboard hozzáférés vezérlése  

## Google Sheets Struktúra

### ⚡ AUTOMATIKUS SPREADSHEET LÉTREHOZÁS!

A rendszer **automatikusan létrehozza** minden ügyfélnek a saját Spreadsheet-jét!

### Config lap (CSV - nyilvános) - EGYETLEN MANUÁLIS TÁBLÁZAT

| Oszlop | Leírás | Példa |
|--------|--------|-------|
| A - `page_id` | Facebook oldal ID | `123456789012345` |
| B - `company_name` | Cég neve | `SmileScale Fogászat` |
| C - `access_token` | Facebook Page Access Token | `EAAxxxxx...` |
| D - `admin_password` | Dashboard jelszó | `titkos123` |
| E - `welcome_text` | Üdvözlő szöveg | `Üdvözlünk! 🦷` |
| F - `button1_text` | 1. gomb felirata | `📅 Időpontfoglalás` |
| G - `button1_link` | Megerősítő üzenet | `Köszönjük!` |
| H - `button2_text` | 2. gomb felirata | `💰 Árlista` |
| I - `button2_link` | Árlista szövege | `Áraink...` |
| J - `button3_text` | 3. gomb felirata | `ℹ️ Információ` |
| K - `button3_link` | Info szöveg | `Címünk...` |
| L - `admin_psid` | Admin Messenger ID (bot tölti) | *(üres)* |
| M - `dashboard` | Dashboard előfizetés (1=aktív, 0=inaktív) | `1` |
| N - `spreadsheet_id` | Ügyfél Spreadsheet ID (program tölti) | *(üres)* |

### Ügyfél-specifikus Spreadsheet-ek (AUTOMATIKUSAN LÉTREJÖNNEK!)

Minden ügyfélnek automatikusan létrejön egy `{company_name} - CRM` nevű Spreadsheet 3 lappal:

**1. Leads lap** (Bot foglalások)

| Oszlop | Leírás |
|--------|--------|
| A - `lead_id` | Egyedi azonosító (LEAD-20260214-123456) |
| B - `beerkezett` | Időbélyeg (2026.02.14 12:34:56) |
| C - `page_id` | Facebook oldal ID |
| D - `company_name` | Cég neve |
| E - `name` | Beteg neve |
| F - `phone` | Telefonszám |
| G - `psid` | Messenger PSID |
| H - `veglegesitett_idopont` | Végleges időpont |
| I - `megjegyzes` | Panasz/megjegyzés |

**2. Patients lap** (Manuális betegek)

| Oszlop | Leírás |
|--------|--------|
| A - `beteg_id` | Egyedi azonosító |
| B - `page_id` | Facebook oldal ID |
| C - `nev` | Beteg neve |
| D - `telefon` | Telefonszám |
| E - `email` | Email cím |
| F - `cim` | Lakcím |
| G - `szuletesi_datum` | Születési dátum |
| H - `megjegyzesek` | Megjegyzések |
| I - `letrehozva` | Létrehozás dátuma |

**3. Treatments lap** (Kezelési történet)

| Oszlop | Leírás |
|--------|--------|
| A - `kezeles_id` | Egyedi azonosító |
| B - `page_id` | Facebook oldal ID |
| C - `beteg_id` | Beteg azonosító |
| D - `tipus` | Kezelés típusa |
| E - `datum` | Kezelés dátuma |
| F - `leiras` | Részletes leírás |
| G - `ar` | Ár (Ft) |
| H - `fizetve` | Fizetési státusz (1=fizetve, 0=függőben) |
| I - `letrehozva` | Rögzítés dátuma |

## CRM Funkciók Részletesen

### 📊 Dashboard
- **Statisztikák**: Összes beteg, függőben lévő foglalások, mai időpontok, heti leadek
- **Legutóbbi foglalások**: 5 legfrissebb foglalás gyors áttekintése
- **Sidebar navigáció**: Gyors váltás az oldalak között

### 📋 Foglalások
- **Összes foglalás listája**: Beérkezési idő, név, telefon, időpont, megjegyzés
- **Keresés**: Név vagy telefon alapján
- **Időpont beállítás**: Kattintással modal ablak, dátum/idő választó
- **Auto-refresh**: 30 másodpercenként frissül (ha nincs nyitva modal)
- **Beteg részletek**: Gyors link a beteg profiljához

### 👥 Betegek
- **Beteg adatbázis**: Egyedi betegek (név+telefon alapján)
- **Manuális hozzáadás**: Új beteg felvétele űrlapon keresztül
- **Keresés**: Beteg keresése név, telefon, email alapján
- **Utolsó látogatás**: Automatikus követés
- **Beteg profil**: Részletes nézet kattintással

### 📅 Naptár
- **Havi nézet**: Teljes hónap naptár formátumban
- **Időpontok megjelenítése**: Napi időpontok a naptárban
- **Navigáció**: Előző/következő hónap, vissza a mai napra
- **Kattintható időpontok**: Beteg részletekhez vezet

### 👤 Beteg Részletek
- **Alapadatok**: Név, telefon, email, cím, születési dátum
- **Időpontok**: Összes időpont a beteggel
- **Kezelési történet**: Dátumozott kezelések, árak, fizetési státusz
- **Új kezelés hozzáadása**: Modal ablakban űrlap
- **Szerkesztés**: Beteg adatok módosítása

### ⚙️ Bot Beállítások
- **Üdvözlő szöveg**: Testreszabható welcome message
- **3 gomb**: Szöveg és válasz szerkesztése
- **Azonnali mentés**: Google Sheets-be írás
- **Cache frissítés**: Változások 1-2 percen belül érvénybe lépnek

## Működés

### 1. Messenger Bot Flow
1. **Get Started** → Welcome text + 3 gomb
2. **Időpontfoglalás gomb** → Név → Telefon → Panasz → Mentés Sheets-be → Admin értesítés
3. **Egyéb gombok** → Szöveges válasz (testreszabható)

### 2. Dashboard Login
- **Page ID** + **Admin Password** (Config táblából)
- **Előfizetés ellenőrzés**: M oszlop (dashboard) = 1
- **Session kezelés**: Bejelentkezve marad

### 3. Időpont Beállítás
1. Foglalások oldalon kattintás a sorra
2. Modal ablak megnyílik
3. Dátum/idő választó
4. Mentés → Sheets frissül
5. Auto-refresh (ha modal nincs nyitva)

### 4. Manuális Beteg Hozzáadás
1. Betegek oldal → "Új beteg" gomb
2. Űrlap kitöltése (név, telefon kötelező)
3. Mentés → Sheets-be írás (Patients vagy Leads)
4. Automatikus megjelenés a listában

### 5. Kezelés Rögzítés
1. Beteg részletek → "Új kezelés" gomb
2. Típus, dátum, leírás, ár, fizetési státusz
3. Mentés → Treatments sheet-be
4. Megjelenik a kezelési történetben

## Setup

### 1. Google Sheets API

**A. Google Cloud Console:**
1. Új projekt: https://console.cloud.google.com/
2. Google Sheets API engedélyezése
3. Service Account létrehozása (Role: Editor)
4. JSON kulcs letöltése

**B. Sheets megosztás:**
1. JSON-ből másold ki a `client_email`-t (pl. `smilescale@...iam.gserviceaccount.com`)
2. Minden Sheets → Share → Illeszd be az email-t (Editor jog)

**C. Spreadsheet ID-k:**
- Config: CSV URL-ből (már be van állítva a kódban)
- Leads: URL-ből `https://docs.google.com/spreadsheets/d/[EZ_AZ_ID]/edit`
- Patients (opcionális): Külön sheet ugyanazzal a service account-tal
- Treatments (opcionális): Külön sheet ugyanazzal a service account-tal

### 2. Render.com Environment Variables

```bash
GOOGLE_CREDENTIALS = {teljes JSON tartalom}
SPREADSHEET_ID = {Config sheets ID}
SECRET_KEY = {random string session-höz}
```

**Ennyi!** A többi Spreadsheet automatikusan létrejön!

### 3. Facebook Setup

**A. Webhook URL:** `https://your-app.onrender.com/webhook`  
**B. Verify Token:** `smilescale_token_2026`  
**C. Webhook Events:** `messages`, `messaging_postbacks`

**D. Get Started gomb:**
- Automatikusan beállítódik szerver induláskor minden page_id-hoz

## Árazási Modell

- **Bot + Ads kezelés**: 100.000 Ft/hó
- **Dashboard hozzáférés**: +50.000 Ft/hó (összesen 150.000 Ft/hó)
- **2 hét próbaidő**: Ingyenes tesztelés

## Fájlok

- `app.py` - Flask webhook szerver + CRM backend
- `templates/base.html` - Alap template sidebar-ral
- `templates/dashboard_new.html` - Dashboard statisztikákkal
- `templates/foglalasok.html` - Foglalások lista + időpont beállítás
- `templates/betegek.html` - Beteg adatbázis + manuális hozzáadás
- `templates/naptar.html` - Naptár nézet
- `templates/beteg_reszletek.html` - Beteg profil + kezelési történet
- `templates/bot_settings.html` - Bot testreszabás
- `requirements.txt` - Python függőségek
- `Procfile` - Render indítási konfiguráció

## Biztonság

- **Config**: CSV (nyilvános, de nem érzékeny adatok)
- **Leads/Patients/Treatments**: Sheets API (biztonságos, PII védelem)
- **Session**: Flask session cookie-val
- **Előfizetés**: Dashboard oszlop ellenőrzés login-nál

## Logolás (Render konzol)

- 📥 Config CSV letöltés
- 📄 Melyik oldalra érkezett üzenet
- 💬 Üzenet tartalma
- 📝 Időpontfoglalás lépései
- 👑 Admin regisztrációk
- ✅ Admin PSID visszaírás
- 💾 Lead/beteg/kezelés mentések
- ❌ Hibák részletes traceback-kel

---

**Készítette**: SmileScale Team 🚀  
**Verzió**: 2.0 - Teljes CRM rendszer  
**Dátum**: 2026.02.14
