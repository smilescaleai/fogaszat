# SmileScale CRM - MASTER Spreadsheet Setup 🚀

## Egyszerű Megoldás!

A meglévő Leads Spreadsheet-et használjuk Master-ként! Minden ügyfélnek külön lapok:

```
Meglévő Leads Spreadsheet (Master):
├─ Sheet1 (régi adatok - megtartjuk)
├─ SmileScale_Leads (új lap - automatikusan létrejön)
├─ SmileScale_Patients (új lap - automatikusan létrejön)
├─ SmileScale_Treatments (új lap - automatikusan létrejön)
├─ DentalClinic_Leads
├─ DentalClinic_Patients
├─ DentalClinic_Treatments
└─ ...
```

## Setup Lépések

### 1. Semmi! 😎

A meglévő Leads Spreadsheet-et használjuk! Már meg van osztva a service account-tal!

### 2. Render Environment Variables

```bash
GOOGLE_CREDENTIALS = {JSON}
SPREADSHEET_ID = {Config Sheet ID}
LEADS_SPREADSHEET_ID = {Meglévő Leads Sheet ID}
```

**Ennyi!** A `MASTER_SPREADSHEET_ID` automatikusan = `LEADS_SPREADSHEET_ID`

### 3. Működés

Amikor egy ügyfél először használja a rendszert:
- ✅ Automatikusan létrejön 3 lap: `{company_name}_Leads`, `{company_name}_Patients`, `{company_name}_Treatments`
- ✅ Fejlécek automatikusan hozzáadódnak
- ✅ Minden adat az ügyfél saját lapjaira kerül
- ✅ A régi Sheet1 lap megmarad (nem törlődik)

## Előnyök

✅ Meglévő Spreadsheet = nincs új setup  
✅ Automatikus lap létrehozás  
✅ Tiszta szervezés (minden ügyfélnek saját lapjai)  
✅ Régi adatok megmaradnak

## Kész!

Push-old GitHub-ra és működik! Semmi extra setup! 🚀
