# StudySpace — School Planner

Een uitgebreidere Streamlit-planner voor toetsen, PTA's en studietaken. De interface is Nederlandstalig en werkt lokaal of met Supabase als cloud-database.

## Functies

- Dashboard met aankomende toets, aftellen in dagen, open taken en voortgang.
- Weekplanner met zeven dagen en agendaoverzicht.
- Automatische planning: twee studieblokken per onderwerp, gelijkmatig verdeeld over gekozen dagen.
- Controle op dubbele toetsen, capaciteit en tijdsconflicten; bestaande afspraken worden niet verwijderd.
- Taken afvinken, individueel verwijderen en prioriteit wijzigen.
- Automatisch herplannen van achterstallige, onafgeronde studietaken.
- Filter op vak in alle hoofdschermen.
- Studie-uren en voortgang per vak in grafieken.
- Kalender exporteren als `.ics` (Google Calendar, Apple Calendar, Outlook).
- JSON-back-up maken en terugzetten.
- Donker en licht thema.
- Optionele gedeelde toegangscode via Streamlit secrets.
- SQLite voor lokaal gebruik; optionele Supabase-opslag voor Streamlit Cloud.

## Lokaal starten

Vereist Python 3.10 of nieuwer.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open daarna de lokale URL die Streamlit in de terminal toont.

Voer de ingebouwde logictests uit met:

```bash
python -m unittest discover -s tests -v
```

## GitHub + Streamlit Community Cloud

1. Pak de projectmap uit.
2. Push de volledige inhoud naar de hoofdmap van je GitHub-repository.
3. Maak in Streamlit Community Cloud een app aan vanuit die repository.
4. Stel **Main file path** in op `app.py`.
5. Laat Streamlit de dependencies installeren uit `requirements.txt`.
6. Configureer Supabase via de stappen in `SUPABASE_SETUP.md` als je data persistent wilt bewaren.

## Database-opmerking

Zonder Supabase gebruikt de app `planner.db` naast `app.py`. Dit is handig voor lokaal testen, maar Streamlit Community Cloud garandeert niet dat lokale bestanden na een herstart of redeploy behouden blijven. Voor online gebruik met belangrijke gegevens: stel Supabase in. De SQL staat in `supabase_schema.sql`.

## Veiligheid en gebruikers

Je kunt een gedeelde toegangscode instellen via `[app] password` in Streamlit secrets. Dit is alleen een eenvoudige toegangsdrempel: mensen met de code delen dezelfde planning. Voor individuele leerlingen/accounts is echte authenticatie met `user_id`, Row Level Security en database policies nodig. Zet nooit een Supabase `service_role` key in GitHub.
