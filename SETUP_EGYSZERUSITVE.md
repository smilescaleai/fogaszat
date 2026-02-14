# SmileScale CRM - Egyszerűsített Telepítés 🚀

## ✨ ÚJ FUNKCIÓ: Automatikus Spreadsheet Létrehozás!

A rendszer **automatikusan létrehozza** minden ügyfélnek a saját Spreadsheet-jét a company name-jével!

---

## Mit Kell Csinálnod?

### 1. Config Sheet (EGYETLEN TÁBLÁZAT!)

Ez az **EGYETLEN** táblázat, amit neked kell létrehoznod!

#### Oszlopok (A-N):
```
A: page_id
B: company_name
C: access_token
D: admin_password
E: welcome_text
F: button1_text
G: button1_link
H: button2_text
I: button2_link
J: button3_text
K: button3_link
L: admin_psid
M: dashboard
N: spreadsheet_id  <-- ÚJ! (üresen hagyva, a program tölti ki)
```

#### Példa sor:
```
123456789 | SmileScale Fogászat | EAAxxxxx | admin123 | Üdvözlünk! 🦷 | 📅 Időpont | Köszönjük! | 💰 Árlista | Áraink... | ℹ️ Info | Címünk... | | 1 | 
```

**Fontos:**
- Az **N oszlop** (spreadsheet_id) legyen **ÜRES**!
- A program automatikusan kitölti, amikor az ügyfél először használja a rendszert

#### Mit csinálj:
1. ✅ Hozd létre a Config Sheet-et
2. ✅ Add hozzá az **N oszlopot** (spreadsheet_id) - üresen!
3. ✅ Publikáld CSV-ként (File → Share → Publish to web → CSV)
4. ✅ Share → Add a service account email-t (Editor jog)

---

## 2. Service Account (Google Cloud)

1. ✅ Google Cloud Console → Service Account létrehozása
2. ✅ JSON kulcs letöltése
3. ✅ Service account email kimásolása (pl. `smilescale@...iam.gserviceaccount.com`)
4. ✅ Config Sheet-en Share → Add az email-t (Editor jog)

**FONTOS:** A service account-nak **CSAK** a Config Sheet-hez kell hozzáférés!  
A többi Spreadsheet-et a program automatikusan létrehozza és megosztja!

---

## 3. Render Environment Variables

```bash
GOOGLE_CREDENTIALS = {teljes JSON tartalom}
SPREADSHEET_ID = {Config Sheet ID}
SECRET_KEY = smilescale_secret_key_2026
```

**Ennyi!** Nincs szükség LEADS_SPREADSHEET_ID, PATIENTS_SPREADSHEET_ID, stb.

---

## Hogyan Működik?

### Első Használat (Automatikus!)

1. **Ügyfél bejelentkezik** a Dashboard-ra (page_id + password)
2. **Program ellenőrzi** a Config Sheet N oszlopát (spreadsheet_id)
3. **Ha üres:**
   - 🆕 Létrehoz egy új Spreadsheet-et: `{company_name} - CRM`
   - 📋 Létrehozza a 3 lapot: **Leads**, **Patients**, **Treatments**
   - 📝 Hozzáadja a fejléceket minden laphoz
   - 💾 Visszaírja a Spreadsheet ID-t a Config Sheet N oszlopába
   - ✅ Kész!
4. **Ha már van:**
   - 📂 Megnyitja a meglévő Spreadsheet-et
   - ✅ Használja azt

### Minden Ügyfélnek Saját Spreadsheet!

```
Config Sheet (1 db):
├─ SmileScale Fogászat (page_id: 123)
│  └─ spreadsheet_id: abc123xyz
│
├─ Dental Clinic (page_id: 456)
│  └─ spreadsheet_id: def456uvw
│
└─ Mosolygó Fogászat (page_id: 789)
   └─ spreadsheet_id: ghi789rst

Automatikusan létrehozott Spreadsheet-ek:
├─ "SmileScale Fogászat - CRM" (abc123xyz)
│  ├─ Leads lap
│  ├─ Patients lap
│  └─ Treatments lap
│
├─ "Dental Clinic - CRM" (def456uvw)
│  ├─ Leads lap
│  ├─ Patients lap
│  └─ Treatments lap
│
└─ "Mosolygó Fogászat - CRM" (ghi789rst)
   ├─ Leads lap
   ├─ Patients lap
   └─ Treatments lap
```

---

## Előnyök

### ✅ Egyszerű Setup
- Csak **1 táblázat** kell létrehoznod (Config)
- Minden más **automatikus**!

### ✅ Tiszta Szervezés
- Minden ügyfélnek **saját Spreadsheet-je**
- Nincs keveredés az adatokban
- Könnyű backup és export

### ✅ Automatikus Megosztás
- A program automatikusan megosztja a service account-tal
- Nincs manuális megosztás minden ügyfélnél

### ✅ Skálázható
- Új ügyfél? Csak add hozzá a Config Sheet-hez!
- Első bejelentkezéskor automatikusan létrejön a Spreadsheet

---

## Tesztelés

### 1. Első Ügyfél Hozzáadása

Config Sheet-be új sor:
```
123456789 | SmileScale | EAAxxxxx | admin123 | Üdvözlünk! | ... | 1 | 
```
(N oszlop üres!)

### 2. Bejelentkezés

1. Menj a `/login` oldalra
2. Írd be: `123456789` + `admin123`
3. **Automatikus történik:**
   - 🆕 Létrejön: "SmileScale - CRM" Spreadsheet
   - 📋 3 lap: Leads, Patients, Treatments
   - 💾 N oszlop kitöltődik a Spreadsheet ID-vel

### 3. Ellenőrzés

1. Nézd meg a Config Sheet N oszlopát → Van benne ID!
2. Nyisd meg a Spreadsheet-et (Google Drive)
3. Látod a 3 lapot fejlécekkel!

---

## Hibaelhárítás

### "Spreadsheet hiba" üzenet
- Ellenőrizd a service account jogosultságokat
- Ellenőrizd a GOOGLE_CREDENTIALS-t
- Nézd meg a Render logs-ot

### N oszlop nem töltődik ki
- Ellenőrizd, hogy van-e N oszlop a Config Sheet-ben
- Ellenőrizd a service account Editor jogát
- Nézd meg a Render logs-ot

### Spreadsheet nem jelenik meg a Drive-ban
- Ellenőrizd a service account email-t
- A Spreadsheet a service account Drive-jában van
- Share → Add a saját email-ed, hogy lásd

---

## Összefoglalás

### Régi Módszer (Bonyolult):
```
❌ Config Sheet létrehozása
❌ Leads Sheet létrehozása
❌ Patients Sheet létrehozása
❌ Treatments Sheet létrehozása
❌ Mind a 4 megosztása service account-tal
❌ Mind a 4 ID bemásolása Render-be
❌ Minden ügyfélnél ugyanez...
```

### Új Módszer (Egyszerű):
```
✅ Config Sheet létrehozása (N oszloppal)
✅ Service account megosztása
✅ 2 environment variable Render-ben
✅ Kész! Minden más automatikus!
```

---

**Kérdések?** Minden automatikus, csak indítsd el! 🚀
