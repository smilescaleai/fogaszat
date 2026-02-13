# 🚀 SmileScale Telepítési Útmutató

## 📋 Mit csináltam?

✅ Teljes működő rendszer:
- Login oldal (page_id + admin_password)
- Dashboard (leadek listázása)
- Bot testreszabás oldal
- Automatikus lead mentés Google Sheets-be
- Messenger bot időpontfoglalás (3 kérdés: név, telefon, megjegyzés)

## 🔧 MIT KELL CSINÁLNOD?

### 1️⃣ Google Sheets Leads Tábla Létrehozása

**a) Hozz létre új Google Sheets táblát:**
- Név: "SmileScale Leads"
- URL: https://docs.google.com/spreadsheets/

**b) Első sor (fejléc):**
```
lead_id | beerkezett | page_id | company_name | name | phone | psid | veglegesitett_idopont | megjegyzes
```

**c) Másold ki a SPREADSHEET_ID-t:**
- URL: `https://docs.google.com/spreadsheets/d/`**`1An18Nwpt1k1Y3GmYQj8BNNO7bfvEA5LcxkW`**`/edit`
- Ez a vastag rész a SPREADSHEET_ID!

**d) Adj hozzáférést a service account-nak:**
- Kattints: Share (Megosztás)
- Add hozzá ezt az email címet (a JSON-ből):
  - Nyisd meg a Render → Environment → `GOOGLE_CREDENTIALS`
  - Keresd meg: `"client_email": "...@....iam.gserviceaccount.com"`
  - Másold ki ezt az email címet
  - Sheets-ben: Share → Add people → Paste email → Editor jogosultság → Send

### 2️⃣ Render.com Environment Variables

Menj: Render Dashboard → SmileScale service → Environment

**Adj hozzá ÚJ változót:**
```
LEADS_SPREADSHEET_ID = 1An18Nwpt1k1Y3GmYQj8BNNO7bfvEA5LcxkW
```
(A te Leads tábla ID-ja!)

**Ellenőrizd hogy megvan:**
```
SPREADSHEET_ID = (meglévő config tábla ID)
GOOGLE_CREDENTIALS = {...json...}
SECRET_KEY = smilescale_secret_key_2026
```

### 3️⃣ Config Tábla Frissítése

**Adj hozzá új oszlopot a végére:**
- Oszlop neve: `company_name`
- Példa érték: `Dr. Kovács Fogászat`

**Teljes oszlopsor (12 oszlop):**
```
page_id | access_token | admin_password | admin_psid | welcome_text | 
button1_text | button1_link | button2_text | button2_link | 
button3_text | button3_link | company_name
```

### 4️⃣ Deploy

**a) Git push:**
```bash
git add .
git commit -m "Full dashboard + lead management"
git push
```

**b) Render automatikusan deploy-ol!**

**c) Várj 2-3 percet**

### 5️⃣ Tesztelés

**a) Dashboard login:**
- URL: `https://fogaszat.onrender.com/login`
- Page ID: (a te page_id-d)
- Jelszó: (admin_password a táblából)

**b) Messenger bot teszt:**
- Küldj üzenetet a Facebook oldalnak
- Kattints: "Időpont foglalás" gombra
- Töltsd ki: Név, Telefon, Megjegyzés
- Ellenőrizd: Leads táblában megjelenik!

**c) Dashboard ellenőrzés:**
- Nézd meg a leadeket
- Kattints: "Bot Testreszabás" → látod a beállításokat

## 📊 Táblák Struktúrája

### Config Tábla (12 oszlop):
1. page_id
2. access_token
3. admin_password
4. admin_psid
5. welcome_text
6. button1_text
7. button1_link
8. button2_text
9. button2_link
10. button3_text
11. button3_link
12. **company_name** ← ÚJ!

### Leads Tábla (9 oszlop):
1. lead_id (auto)
2. beerkezett (auto)
3. page_id (auto)
4. company_name (auto)
5. name (bot kérdezi)
6. phone (bot kérdezi)
7. psid (auto)
8. veglegesitett_idopont (admin tölti ki)
9. megjegyzes (bot kérdezi)

## 🎯 Messenger Bot Flow

1. User: Kattint "Időpont foglalás" gombra
2. Bot: "Kérem, írja be a nevét! 😊"
3. User: "Nagy Péter"
4. Bot: "Telefonszám:"
5. User: "+36301234567"
6. Bot: "Milyen kezelés érdekli?"
7. User: "Implantátum"
8. Bot: "Köszönjük! Hamarosan felvesszük Önnel a kapcsolatot!"
9. **Lead mentve a Sheets-be!**
10. **Admin kap értesítést Messengerben!**

## ⚠️ Hibaelhárítás

**Ha nem működik a login:**
- Ellenőrizd: page_id és admin_password egyezik a táblával
- Ellenőrizd: SECRET_KEY be van állítva Render-en

**Ha nem jelennek meg a leadek:**
- Ellenőrizd: LEADS_SPREADSHEET_ID helyes
- Ellenőrizd: Service account email hozzáadva a Leads táblához (Editor jog)
- Nézd meg: Render Logs → van-e hiba

**Ha a bot nem válaszol:**
- Ellenőrizd: Webhook működik (Facebook Developer Console)
- Ellenőrizd: CSV URL elérhető
- Nézd meg: Render Logs

## 🎉 Kész!

Most már működik:
✅ Login rendszer
✅ Dashboard leadekkel
✅ Bot testreszabás nézet
✅ Automatikus lead mentés
✅ Admin értesítések

**Következő lépés:** Teszteld végig és élvezd! 🦷
