import streamlit as st
import datetime
import math
from PIL import Image

# Pagina-instellingen
st.set_page_config(page_title="<mark>PTA Studieplanner</mark>", page_icon="📚", layout="centered")

# Titel en uitleg
st.title("📚 <mark>PTA Studieplanner</mark>")
st.write("Upload je PTA-informatie, kies je toetsdatum en krijg een automatisch verdeeld leerschema!")

# --- SECTIE 1: INFORMATIE INVOEREN / SCREENSHOT ---
st.header("1. PTA Informatie of Screenshot")

uploaded_file = st.file_uploader("Upload een screenshot van je PTA (optioneel):", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Geüploade PTA-afbeelding", use_container_width=True)
    st.info("💡 Bekijk je screenshot hierboven en vul hieronder de hoofdstukken in.")

st.subheader("Wat moet je leren?")
st.caption("Typ de onderwerpen of hoofdstukken gescheiden door een komma:")

# Standaard voorbeeldtekst die in het tekstvak staat
default_text = "<mark>Hoofdstuk 1, Hoofdstuk 2, Paragraaf 3.1, Paragraaf 3.2, Samenvatting maken</mark>"
raw_topics = st.text_area("Onderwerpen/Hoofdstukken:", default_text)

# Omzetten naar een lijst van onderwerpen
topics_list = [t.strip() for t in raw_topics.split(",") if t.strip()]

# --- SECTIE 2: DATUM EN PLANNING INSTELLINGEN ---
st.header("2. Planningsinstellingen")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input("Startdatum leren:", datetime.date.today())

with col2:
    # Standaard ingesteld op 7 dagen vanaf vandaag
    exam_date = st.date_input("Datum PTA Toets:", datetime.date.today() + datetime.timedelta(days=7))

st.subheader("Op welke dagen kun/wil je leren?")
study_days = {
    "Maandag": st.checkbox("Maandag", value=True),
    "Dinsdag": st.checkbox("Dinsdag", value=True),
    "Woensdag": st.checkbox("Woensdag", value=True),
    "Donderdag": st.checkbox("Donderdag", value=True),
    "Vrijdag": st.checkbox("Vrijdag", value=True),
    "Zaterdag": st.checkbox("Zaterdag", value=True),
    "Zondag": st.checkbox("Zondag", value=False), # Zondag standaard uitgevinkt
}

# --- SECTIE 3: GENEREREN EN TONEN VAN HET SCHEMA ---
st.header("3. Jouw Persoonlijke Leerschema")

if st.button("🚀 Genereer Leerschema"):
    if not topics_list:
        st.error("Voer eerst ten minste één onderwerp of hoofdstuk in!")
    elif start_date >= exam_date:
        st.error("De toetsdatum moet ná de startdatum liggen.")
    else:
        # Bereken geldige studiedagen
        current_date = start_date
        valid_dates = []
        days_nl = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
        
        while current_date < exam_date:
            day_name = days_nl[current_date.weekday()]
            if study_days[day_name]:
                valid_dates.append(current_date)
            current_date += datetime.timedelta(days=1)
            
        if not valid_dates:
            st.warning("Geen geldige studiedagen geselecteerd binnen deze periode!")
        else:
            # Verdeel onderwerpen over de dagen
            num_days = len(valid_dates)
            num_topics = len(topics_list)
            topics_per_day = math.ceil(num_topics / num_days)
            
            st.success(f"Totaal {num_topics} onderwerpen verdeeld over {num_days} studiedagen!")
            
            schedule = {}
            for i, date in enumerate(valid_dates):
                start_idx = i * topics_per_day
                end_idx = min(start_idx + topics_per_day, num_topics)
                assigned_topics = topics_list[start_idx:end_idx]
                
                if assigned_topics:
                    schedule[date] = assigned_topics
            
            # Toon het schema op het scherm
            for date, tasks in schedule.items():
                day_str = days_nl[date.weekday()]
                formatted_date = date.strftime("%d-%m-%Y")
                
                with st.expander(f"📅 **{day_str} {formatted_date}** — ({len(tasks)} onderwerpen)", expanded=True):
                    for task in tasks:
                        st.checkbox(f"Leren: {task}", key=f"{date}_{task}")
            
            st.info(f"💡 **{exam_date.strftime('%d-%m-%Y')} (Toetsdag):** Heel veel succes met je toets!")
