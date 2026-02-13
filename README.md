# SmileScale Facebook Messenger Bot 🦷

## Funkciók

✅ **Get Started gomb** - Első üzenetként welcome text + gombok  
✅ **Időpontfoglalás** - Név, telefon, panasz bekérése lépésről lépésre  
✅ **Árlista** - Szöveges válasz a táblázatból  
✅ **Sürgős eset** - Telefonhívás indítás (tel: link)  
✅ **Admin rendszer** - Google Sheets API-val admin_psid visszaírás  
✅ **Multi-page** - Több Facebook oldal kezelése  
✅ **UTF-8 encoding** - Magyar ékezetek támogatása  

## Google Sheets Struktúra

### Config lap (Sheet1)

| Oszlop | Leírás | Példa |
|--------|--------|-------|
| `page_id` | Facebook oldal ID | `123456789012345` |
| `access_token` | Facebook Page Access Token | `EAAxxxxx...` |
| `admin_password` | Admin jelszó | `titkos123` |
| `admin_psid` | Admin Messenger ID (bot tölti ki) | *(üres)* |
| `admin_phone` | Telefonszám sürgős esethez | `+36301234567` |
| `welcome_text` | Üdvözlő szöveg | `Üdvözlünk a SmileScale-nél! 🦷` |
| `button1_text` | 1. gomb felirata | `📅 Időpontfoglalás` |
| `button1_link` | Megerősítő üzenet foglalás után | `Köszönjük! Hamarosan felvesszük Önnel a kapcsolatot!` |
| `button2_text` | 2. gomb felirata | `💰 Árlista` |
| `button2_link` | Árlista szövege | `Az áraink 10.000 Ft-tól indulnak...` |
| `button3_text` | 3. gomb felirata | `🚨 Sürgős eset` |
| `button3_link` | *(nem használt)* | - |

## Működés

### 1. Get Started gomb
- Első üzenetként megjelenik
- Rákattintva: welcome text + 3 gomb

### 2. Időpontfoglalás (1. gomb)
1. **Név bekérése**: "Kérem, írja be a nevét!"
2. **Telefonszám bekérése**: "Köszönöm! Kérem, írja be a telefonszámát!"
3. **Panasz bekérése**: "Köszönöm! Miben segíthetünk?"
4. **Admin értesítés** (Messenger):
   ```
   🦷 ÚJ IDŐPONTFOGLALÁS
   
   👤 Név: Kovács János
   📞 Telefon: +36301234567
   💬 Panasz: Fogfájás
   
   🕐 2026.02.05 18:45
   ```
5. **Megerősítés** a usernek (button1_link)

### 3. Árlista (2. gomb)
- Szöveges válasz (button2_link tartalmát küldi)

### 4. Sürgős eset (3. gomb)
- `tel:` link az admin_phone-nal
- Mobilon megnyomva → tárcsázás indul

### 5. Admin regisztráció
- Messenger-ben beírni: `admin_password` (pl. `titkos123`)
- Bot visszaírja az admin_psid-t a táblázatba
- Restart után is megmarad

## Setup

### 1. Google Sheets API

**A. Google Cloud Console:**
1. Új projekt: https://console.cloud.google.com/
2. Google Sheets API engedélyezése
3. Service Account létrehozása (Role: Editor)
4. JSON kulcs letöltése

**B. Sheets megosztás:**
1. JSON-ből másold ki a `client_email`-t
2. Sheets → Share → Illeszd be az email-t (Editor jog)

**C. Spreadsheet ID:**
- URL-ből: `https://docs.google.com/spreadsheets/d/[EZ_AZ_ID]/edit`

### 2. Render.com Environment Variables

```
GOOGLE_CREDENTIALS = {teljes JSON tartalom}
SPREADSHEET_ID = {a sheets ID}
```

### 3. Facebook Setup

**A. Webhook URL:** `https://your-app.onrender.com/webhook`  
**B. Verify Token:** `smilescale_token_2026`  
**C. Webhook Events:** `messages`, `messaging_postbacks`

**D. Get Started gomb beállítása:**
```bash
curl -X POST "https://graph.facebook.com/v18.0/me/messenger_profile?access_token=YOUR_PAGE_ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "get_started": {
    "payload": "GET_STARTED"
  }
}'
```

## Fájlok

- `app.py` - Flask webhook szerver
- `requirements.txt` - flask, requests, gunicorn, gspread, google-auth
- `Procfile` - Render indítási konfiguráció

## Logolás (Render konzol)

- 📥 CSV letöltés
- 📄 Melyik oldalra érkezett üzenet
- 💬 Üzenet tartalma
- 📝 Időpontfoglalás lépései
- 👑 Admin regisztrációk
- ✅ Admin PSID visszaírás

---

**Készítette**: Opus & Kiro 🚀
