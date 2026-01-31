# Facebook Messenger Webhook - Időpontfoglaló Bot

Flask alapú Messenger bot időpontfoglaláshoz, állapotkezeléssel és admin értesítéssel.

## Funkciók

✅ **Gombos menü**: Árak, Helyszín, Időpontkérés  
✅ **Állapotkezelés**: Telefonszám bekérés időpontkérésnél  
✅ **Validálás**: Magyar telefonszám formátum ellenőrzés  
✅ **Admin értesítés**: Automatikus üzenet a dokinak új lead esetén  
✅ **Adattárolás**: CSV fájlba mentés (leads.csv)  
✅ **Biztonság**: Facebook verify_token ellenőrzés  

## Telepítés

1. **Függőségek telepítése:**
```bash
pip install -r requirements.txt
```

2. **Környezeti változók beállítása:**
```bash
copy .env.example .env
```

Szerkeszd a `.env` fájlt:
- `PAGE_ACCESS_TOKEN`: Facebook oldal access token
- `VERIFY_TOKEN`: Saját verify token (bármilyen string)
- `ADMIN_PSID`: Doki Facebook PSID-ja

3. **Alkalmazás indítása:**
```bash
python app.py
```

## Facebook Beállítások

### 1. Facebook App létrehozása
- Menj a [Facebook Developers](https://developers.facebook.com/) oldalra
- Hozz létre új alkalmazást
- Add hozzá a "Messenger" terméket

### 2. Webhook beállítása
- Callback URL: `https://your-domain.com/webhook`
- Verify Token: Az általad választott token (`.env` fájlban)
- Subscription Fields: `messages`, `messaging_postbacks`

### 3. Page Access Token megszerzése
- Messenger Settings → Access Tokens
- Generálj tokent az oldaladhoz
- Másold be a `.env` fájlba

### 4. Admin PSID megszerzése
Küldj üzenetet a botnak, majd nézd meg a logokban a sender_id-t, vagy használd ezt:
```bash
curl "https://graph.facebook.com/v18.0/me?access_token=YOUR_PAGE_ACCESS_TOKEN"
```

## Használat

A bot három gombot kínál:

1. **💰 Árak** - Árlistát mutat
2. **📍 Helyszín** - Címet és nyitvatartást mutat
3. **📅 Időpontkérés** - Telefonszámot kér, majd értesíti a dokit

### Időpontkérés folyamat:
1. Felhasználó rákattint az "Időpontkérés" gombra
2. Bot telefonszámot kér
3. Felhasználó megadja a számot
4. Bot validálja a formátumot
5. Sikeres validálás esetén:
   - Elmenti a `leads.csv` fájlba
   - Értesíti a dokit Messengeren
   - Visszajelzést ad a felhasználónak

## Adatstruktúra (leads.csv)

```csv
Dátum,PSID,Név,Telefonszám
2026-01-31 14:30:00,1234567890,Kiss János,+36301234567
```

## Production Deploy

### Ngrok (teszteléshez):
```bash
ngrok http 5000
```

### Heroku:
```bash
heroku create your-app-name
heroku config:set PAGE_ACCESS_TOKEN=your_token
heroku config:set VERIFY_TOKEN=your_verify_token
heroku config:set ADMIN_PSID=your_psid
git push heroku main
```

## Továbbfejlesztési lehetőségek

- SQLite/PostgreSQL adatbázis használata CSV helyett
- Redis session kezelés több szerver esetén
- Időpont választó naptár integráció
- Email értesítés a doki számára
- CRM integráció (pl. HubSpot, Salesforce)
- Többnyelvű támogatás

## Biztonság

⚠️ **Fontos:**
- Soha ne commitold a `.env` fájlt!
- Használj HTTPS-t production környezetben
- Rendszeresen frissítsd a függőségeket
- Korlátozd az API hozzáférést IP alapján ha lehetséges

## Licenc

MIT
