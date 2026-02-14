# SmileScale CRM - Telepítési Checklist ✅

## Előkészületek

### Google Sheets
- [ ] Service Account létrehozva Google Cloud Console-ban
- [ ] JSON kulcs letöltve
- [ ] Config Sheet létrehozva (13 oszlop: A-M)
- [ ] Config Sheet publikálva CSV-ként
- [ ] Leads Sheet létrehozva (9 oszlop: A-I)
- [ ] Patients Sheet létrehozva (opcionális, 9 oszlop: A-I)
- [ ] Treatments Sheet létrehozva (opcionális, 9 oszlop: A-I)
- [ ] Service account email megosztva minden Sheet-en (Editor jog)
- [ ] Spreadsheet ID-k kimásolva

### Facebook
- [ ] Facebook App létrehozva
- [ ] Messenger Product hozzáadva
- [ ] Page Access Token generálva
- [ ] Token bemásolva Config Sheet-be

### Render.com
- [ ] GitHub repository létrehozva
- [ ] Kód push-olva GitHub-ra
- [ ] Render Web Service létrehozva
- [ ] Environment variables beállítva:
  - [ ] `GOOGLE_CREDENTIALS`
  - [ ] `SPREADSHEET_ID`
  - [ ] `LEADS_SPREADSHEET_ID`
  - [ ] `PATIENTS_SPREADSHEET_ID` (opcionális)
  - [ ] `TREATMENTS_SPREADSHEET_ID` (opcionális)
  - [ ] `SECRET_KEY`

## Konfiguráció

### Config Sheet Kitöltése
- [ ] `page_id`: Facebook oldal ID
- [ ] `company_name`: Cég neve
- [ ] `access_token`: Page Access Token
- [ ] `admin_password`: Dashboard jelszó
- [ ] `welcome_text`: Üdvözlő szöveg
- [ ] `button1_text`: 1. gomb szövege
- [ ] `button1_link`: 1. gomb válasza
- [ ] `button2_text`: 2. gomb szövege
- [ ] `button2_link`: 2. gomb válasza
- [ ] `button3_text`: 3. gomb szövege
- [ ] `button3_link`: 3. gomb válasza
- [ ] `admin_psid`: Üresen hagyva (bot tölti ki)
- [ ] `dashboard`: 1 (aktív előfizetés)

### Facebook Webhook
- [ ] Callback URL beállítva: `https://your-app.onrender.com/webhook`
- [ ] Verify Token: `smilescale_token_2026`
- [ ] Subscription Fields: `messages`, `messaging_postbacks`
- [ ] Page subscribe-olva

## Tesztelés

### Messenger Bot
- [ ] Get Started gomb működik
- [ ] Welcome text + gombok megjelennek
- [ ] Időpontfoglalás gomb működik
- [ ] Név bekérés működik
- [ ] Telefon bekérés működik
- [ ] Panasz bekérés működik
- [ ] Lead mentődik Leads Sheet-be
- [ ] Admin értesítés érkezik (ha admin_psid be van állítva)
- [ ] Megerősítő üzenet megjelenik
- [ ] 2. és 3. gomb működik (szöveges válasz)

### Admin Regisztráció
- [ ] Admin jelszó beírása Messenger-ben
- [ ] "Jelszó elfogadva" üzenet
- [ ] Admin PSID mentődik Config Sheet L oszlopba
- [ ] Admin értesítések érkeznek új leadekről

### Dashboard Login
- [ ] Login oldal elérhető: `https://your-app.onrender.com/login`
- [ ] Bejelentkezés page_id + admin_password-del
- [ ] Dashboard előfizetés ellenőrzés működik (M oszlop)
- [ ] Sikeres login után Dashboard megjelenik

### Dashboard Funkciók
- [ ] Statisztikák helyesen jelennek meg:
  - [ ] Összes beteg
  - [ ] Függőben lévő foglalások
  - [ ] Mai időpontok
  - [ ] Heti leadek
- [ ] Legutóbbi 5 foglalás megjelenik
- [ ] "Összes foglalás megtekintése" link működik

### Foglalások Oldal
- [ ] Összes foglalás megjelenik
- [ ] Keresés működik (név/telefon)
- [ ] Sorra kattintva modal megnyílik
- [ ] Időpont választó működik
- [ ] Mentés után időpont frissül Sheets-ben
- [ ] Auto-refresh működik (30 sec)
- [ ] "Részletek" gomb működik

### Betegek Oldal
- [ ] Betegek listája megjelenik
- [ ] Keresés működik
- [ ] "Új beteg" gomb működik
- [ ] Modal megnyílik
- [ ] Beteg hozzáadása működik
- [ ] Új beteg megjelenik a listában
- [ ] "Részletek" gomb működik

### Naptár Oldal
- [ ] Aktuális hónap megjelenik
- [ ] Napok helyesen jelennek meg
- [ ] Időpontok megjelennek a megfelelő napokon
- [ ] "Előző hónap" gomb működik
- [ ] "Következő hónap" gomb működik
- [ ] "Ma" gomb működik
- [ ] Időpontra kattintva beteg részletek megnyílnak

### Beteg Részletek Oldal
- [ ] Beteg alapadatok megjelennek
- [ ] Időpontok listája megjelenik
- [ ] Kezelési történet megjelenik (ha van)
- [ ] "Új kezelés" gomb működik
- [ ] Kezelés hozzáadása működik
- [ ] Új kezelés megjelenik a listában
- [ ] Fizetési státusz helyesen jelenik meg

### Bot Beállítások Oldal
- [ ] Aktuális beállítások megjelennek
- [ ] Welcome text szerkeszthető
- [ ] Gombok szerkeszthetők
- [ ] Mentés működik
- [ ] Változások mentődnek Sheets-be
- [ ] Sikeres mentés üzenet megjelenik
- [ ] Változások 1-2 perc múlva érvénybe lépnek

### Sidebar Navigáció
- [ ] Dashboard link működik
- [ ] Foglalások link működik
- [ ] Betegek link működik
- [ ] Naptár link működik
- [ ] Bot Beállítások link működik
- [ ] Kilépés link működik
- [ ] Aktív oldal kiemelve

## Hibaelhárítás

### Ha a bot nem válaszol
- [ ] Ellenőrizd a Render logs-ot
- [ ] Ellenőrizd a webhook beállítást
- [ ] Ellenőrizd az access_token-t
- [ ] Ellenőrizd a Config Sheet-et

### Ha a Dashboard nem elérhető
- [ ] Ellenőrizd a `dashboard` oszlopot (M) = 1
- [ ] Ellenőrizd a page_id-t és jelszót
- [ ] Ellenőrizd a Render logs-ot

### Ha a Leads nem mentődnek
- [ ] Ellenőrizd a service account jogosultságokat
- [ ] Ellenőrizd a LEADS_SPREADSHEET_ID-t
- [ ] Ellenőrizd a Sheets oszlopokat (9 oszlop kell)
- [ ] Nézd meg a Render logs-ot

### Ha az Admin PSID nem mentődik
- [ ] Ellenőrizd, hogy van-e L oszlop (admin_psid)
- [ ] Ellenőrizd a service account jogosultságokat
- [ ] Próbáld újra beírni az admin jelszót
- [ ] Nézd meg a Render logs-ot

## Éles Indítás

### Előfizetés Aktiválás
- [ ] `dashboard` oszlop = 1 (aktív előfizetés)
- [ ] Ügyfél értesítése a Dashboard URL-ről
- [ ] Ügyfél értesítése a login adatokról

### Dokumentáció Átadása
- [ ] README.md
- [ ] DEPLOYMENT.md
- [ ] API.md
- [ ] CHECKLIST.md (ez a fájl)

### Monitoring
- [ ] Render logs figyelése
- [ ] Sheets backup beállítása (hetente)
- [ ] Ügyfél support elérhetőség

## Karbantartás

### Heti Feladatok
- [ ] Render logs ellenőrzése
- [ ] Sheets backup készítése
- [ ] Ügyfél elégedettség felmérése

### Havi Feladatok
- [ ] Statisztikák áttekintése
- [ ] Rendszer teljesítmény ellenőrzése
- [ ] Új funkciók tervezése

---

**Verzió**: 2.0  
**Utolsó frissítés**: 2026.02.14  
**Státusz**: ✅ Teljes CRM rendszer kész!
