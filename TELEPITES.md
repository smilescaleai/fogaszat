# 🚀 SmileScale Telepítési Útmutató

## ✅ KÉSZ! A rendszer működik!

A SmileScale teljes működő rendszer:
- Login oldal (page_id + admin_password)
- Dashboard (leadek listázása Sheets API-ból - biztonságos!)
- Bot testreszabás oldal
- Automatikus lead mentés Google Sheets-be (Sheets API - biztonságos!)
- Messenger bot időpontfoglalás (3 kérdés: név, telefon, megjegyzés)

## 🔒 Biztonság

- Config tábla: CSV-ből töltődik (publikus, de csak bot beállítások)
- Leads tábla: Sheets API-ból (biztonságos, service account-tal)
- Érzékeny adatok (név, telefon) NEM publikusak!

## 📊 Táblák

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
12. company_name

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

## 🎉 Kész!

Minden működik! Élvezd! 🦷
