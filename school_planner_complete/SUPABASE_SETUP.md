# Supabase instellen (aanbevolen voor Streamlit Cloud)

De app gebruikt SQLite tijdens lokale ontwikkeling. Op Streamlit Community Cloud kan een lokaal databasebestand verdwijnen bij opnieuw opstarten of opnieuw uitrollen. Supabase zorgt voor opslag buiten de app-container.

## 1. Maak een Supabase-project

1. Maak een project aan op [supabase.com](https://supabase.com/).
2. Open **SQL Editor**.
3. Plak de inhoud van `supabase_schema.sql` en voer het script uit.
4. Open **Project Settings → API** en kopieer de Project URL en de anon/publishable key.

## 2. Koppel Streamlit Cloud

1. Open je app in Streamlit Community Cloud.
2. Open **Settings → Secrets**.
3. Voeg toe (vervang de voorbeeldwaarden):

```toml
[supabase]
url = "https://YOUR-PROJECT.supabase.co"
key = "YOUR_SUPABASE_ANON_OR_PUBLISHABLE_KEY"

# Optional shared password for the Streamlit app itself.
[app]
password = "USE_A_LONG_UNIQUE_PASSWORD"
```

4. Sla de secrets op en herstart/redeploy de app.
5. In de zijbalk moet nu **Cloud database · Supabase** staan.

De app gebruikt de Supabase client via de Python SDK. Zet nooit een `service_role` key in een publiek GitHub-repository. De optionele `[app] password` blokkeert bezoekers zonder de gedeelde toegangscode, maar is geen individuele account-/gebruikersauthenticatie. Iedereen met die code ziet dezelfde planner en dezelfde afspraken. Voor meerdere leerlingen of individuele privégegevens moet een echte login met `user_id`, Row Level Security en policies worden toegevoegd.

## 3. Bestaande SQLite-data overzetten

Als je nog afspraken in een lokale `planner.db` hebt:

1. Start de app lokaal zonder Supabase-secrets.
2. Ga naar **Instellingen → Download gegevens-back-up (.json)**.
3. Configureer Supabase zoals hierboven.
4. Open de online app, ga naar **Instellingen → Back-up terugzetten** en importeer het JSON-bestand.

De import gebruikt de event-ID's en werkt bestaande records bij in plaats van duplicaten te maken.
