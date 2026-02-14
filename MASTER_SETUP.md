# SmileScale CRM - MASTER Spreadsheet Setup 🚀

## Egyszerű Megoldás!

Egy MASTER Spreadsheet-ben minden ügyfélnek külön lapok:

```
Master CRM Spreadsheet:
├─ SmileScale_Leads
├─ SmileScale_Patients  
├─ SmileScale_Treatments
├─ DentalClinic_Leads
├─ DentalClinic_Patients
├─ DentalClinic_Treatments
└─ ...
```

## Setup Lépések

### 1. Master Spreadsheet Létrehozása

1. ✅ Hozz létre egy új Google Sheets dokumentumot
2. ✅ Nevezd el: "SmileScale Master CRM"
3. ✅ Share → Add a service account email-t (Editor jog)
4. ✅ Másold ki a Spreadsheet ID-t

### 2. Render Environment Variables

```bash
GOOGLE_CREDENTIALS = {JSON}
SPREADSHEET_ID = {Config Sheet ID}
MASTER_SPREADSHEET_ID = {Master CRM Sheet ID}
SECRET_KEY = smilescale_secret_key_2026
```

### 3. Működés

Amikor egy ügyfél először használja a rendszert:
- ✅ Automatikusan létrejön 3 lap: `{company_name}_Leads`, `{company_name}_Patients`, `{company_name}_Treatments`
- ✅ Fejlécek automatikusan hozzáadódnak
- ✅ Minden adat az ügyfél saját lapjaira kerül

## Előnyök

✅ Egy Spreadsheet = könnyű kezelés  
✅ Automatikus lap létrehozás  
✅ Tiszta szervezés (minden ügyfélnek saját lapjai)  
✅ Nincs szükség új Spreadsheet-ek létrehozására

## Kész!

Push-old GitHub-ra és állítsd be a `MASTER_SPREADSHEET_ID`-t! 🚀
