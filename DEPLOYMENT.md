# SmileScale CRM - Telepítési Útmutató 🚀

## Gyors Áttekintés

Ez a teljes CRM rendszer tartalmazza:
- ✅ Messenger bot időpontfoglalással
- ✅ Dashboard statisztikákkal
- ✅ Foglalások kezelése
- ✅ Beteg adatbázis
- ✅ Naptár nézet
- ✅ Kezelési történet
- ✅ Bot testreszabás

## 1. Google Sheets Beállítás

### A. Service Account Létrehozása

1. Menj a Google Cloud Console-ra: https://console.cloud.google.com/
2. Hozz létre új projektet vagy válassz egy meglévőt
3. Engedélyezd a Google Sheets API-t
4. Hozz létre Service Account-ot:
   - IAM & Admin → Service Accounts → Create Service Account
   - Név: `smilescale` (vagy bármi)
   - Role: `Editor`
   - Create Key → JSON → Letöltés

### B. Sheets Létrehozása

**Config Sheet (CSV export):**
- Oszlopok: page_id, company_name, access_token, admin_password, welcome_text, button1_text, button1_link, button2_text, button2_link, button3_text, button3_link, admin_psid, dashboard
- File → Share → Publish to web → CSV
- Másold ki a CSV URL-t

**Leads Sheet:**
- Oszlopok: lead_id, beerkezett, page_id, company_name, name, phone, psid, veglegesitett_idopont, megjegyzes
- Share → Add a service account email-t (Editor jog)
- Másold ki a Spreadsheet ID-t az URL-ből

**Patients Sheet (opcionális):**
- Oszlopok: beteg_id, page_id, nev, telefon, email, cim, szuletesi_datum, megjegyzesek, letrehozva
- Tab neve: `Patients`
- Share → Add a service account email-t

**Treatments Sheet (opcionális):**
- Oszlopok: kezeles_id, page_id, beteg_id, tipus, datum, leiras, ar, fizetve, letrehozva
- Tab neve: `Treatments`
- Share → Add a service account email-t

## 2. Render.com Telepítés

### A. GitHub Repository

1. Push-old a kódot GitHub-ra
2. Fájlok: `app.py`, `requirements.txt`, `Procfile`, `templates/`

### B. Render Web Service

1. New → Web Service
2. Connect GitHub repository
3. Settings:
   - Name: `smilescale-crm`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

### C. Environment Variables

```bash
GOOGLE_CREDENTIALS = {teljes JSON tartalom a letöltött fájlból}
SPREADSHEET_ID = {Config sheets ID}
LEADS_SPREADSHEET_ID = {Leads sheets ID}
PATIENTS_SPREADSHEET_ID = {Patients sheets ID - opcionális}
TREATMENTS_SPREADSHEET_ID = {Treatments sheets ID - opcionális}
SECRET_KEY = {random string, pl: smilescale_secret_key_2026}
```

**Fontos:** A `GOOGLE_CREDENTIALS` a teljes JSON tartalom legyen, pl:
```json
{
  "type": "service_account",
  "project_id": "...",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "smilescale@....iam.gserviceaccount.com",
  ...
}
```

## 3. Facebook Messenger Setup

### A. Facebook App Létrehozása

1. https://developers.facebook.com/
2. My Apps → Create App → Business
3. Add Product → Messenger

### B. Page Access Token

1. Messenger Settings → Access Tokens
2. Add or Remove Pages → Válaszd ki az oldalt
3. Generate Token → Másold ki
4. Írd be a Config Sheets-be az `access_token` oszlopba

### C. Webhook Beállítás

1. Messenger Settings → Webhooks → Add Callback URL
2. Callback URL: `https://your-app.onrender.com/webhook`
3. Verify Token: `smilescale_token_2026`
4. Subscription Fields: `messages`, `messaging_postbacks`
5. Subscribe to Page

### D. Get Started Gomb

- Automatikusan beállítódik a szerver indulásakor
- Nincs szükség manuális beállításra

## 4. Config Sheet Kitöltése

Példa sor:

| page_id | company_name | access_token | admin_password | welcome_text | button1_text | button1_link | button2_text | button2_link | button3_text | button3_link | admin_psid | dashboard |
|---------|--------------|--------------|----------------|--------------|--------------|--------------|--------------|--------------|--------------|--------------|------------|-----------|
| 123456789 | SmileScale | EAAxxxxx... | admin123 | Üdvözlünk! 🦷 | 📅 Időpont | Köszönjük! | 💰 Árlista | Áraink... | ℹ️ Info | Címünk... | | 1 |

## 5. Tesztelés

### A. Messenger Bot

1. Menj a Facebook oldaladra
2. Kattints a "Send Message" gombra
3. Teszteld a Get Started gombot
4. Teszteld az időpontfoglalást
5. Írd be az admin jelszót → Admin PSID mentődik

### B. Dashboard

1. Menj a `https://your-app.onrender.com/login`
2. Jelentkezz be: page_id + admin_password
3. Nézd meg a statisztikákat
4. Teszteld a foglalások kezelését
5. Adj hozzá manuálisan egy beteget
6. Nézd meg a naptárt

## 6. Hibaelhárítás

### "Hibás page_id vagy jelszó"
- Ellenőrizd a Config Sheet-et
- Ellenőrizd, hogy a `dashboard` oszlop = 1

### "Dashboard szolgáltatás eléréséhez..."
- A `dashboard` oszlop értéke 0
- Állítsd át 1-re az előfizetés aktiválásához

### Bot nem válaszol
- Ellenőrizd a Webhook beállítást
- Nézd meg a Render logs-ot
- Ellenőrizd az access_token-t

### Leads nem mentődnek
- Ellenőrizd a service account jogosultságokat
- Nézd meg a Render logs-ot
- Ellenőrizd a LEADS_SPREADSHEET_ID-t

### Admin PSID nem mentődik
- Ellenőrizd, hogy a Config Sheet-ben van-e L oszlop (admin_psid)
- Nézd meg a Render logs-ot
- Próbáld újra beírni az admin jelszót

## 7. Karbantartás

### Logs Ellenőrzése
- Render Dashboard → Logs
- Keress rá: `❌` (hibák), `✅` (sikerek)

### Sheets Backup
- File → Make a copy
- Hetente mentsd le

### Bot Üzenetek Frissítése
- Dashboard → Bot Beállítások
- Szerkeszd az üzeneteket
- Mentés → 1-2 perc múlva érvénybe lép

## 8. Árazás & Előfizetés

- **Bot + Ads**: 100.000 Ft/hó
- **Dashboard**: +50.000 Ft/hó
- **Összesen**: 150.000 Ft/hó
- **Próbaidő**: 2 hét ingyenes

Dashboard aktiválás: `dashboard` oszlop = 1

---

**Kérdések?** Írj nekünk! 🚀
