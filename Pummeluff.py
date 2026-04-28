import streamlit as st
import pandas as pd
import json
import os
import pickle
import random
import time
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

# --- CONFIG & CLOUD SYNC ---
SCOPES = ['https://www.googleapis.com/auth/drive.file']
DB_FILE = 'pummeluff_db.json'

def get_gdrive_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def upload_to_drive():
    try:
        service = get_gdrive_service()
        file_metadata = {'name': DB_FILE, 'mimeType': 'application/json'}
        media = MediaFileUpload(DB_FILE, mimetype='application/json')
        results = service.files().list(q=f"name='{DB_FILE}'", spaces='drive').execute()
        items = results.get('files', [])
        if not items:
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        else:
            file_id = items[0]['id']
            service.files().update(fileId=file_id, media_body=media).execute()
        return True
    except Exception as e:
        st.error(f"Cloud-Sync Fehler: {e}")
        return False

# --- DATEN LOGIK ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {"matrix": {}, "pflichten": [], "feedback": [], "user_config": ["Papa", "Lea", "Nele", "Rapipat"]}

def save_and_sync(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    upload_to_drive()

# --- GUI START ---
st.set_page_config(page_title="Pummeluff Radar 1255", layout="wide")
if 'db' not in st.session_state:
    st.session_state.db = load_data()

st.sidebar.title("🐒 Sektor 1255")
st.sidebar.info(f"User im Sektor: {', '.join(st.session_state.db['user_config'])}")
menu = st.sidebar.selectbox("Modul wählen", [
    "1. Wochen-Matrix (Editor)",
    "2. Schiedsrichter (Verträge)",
    "3. Pflichten-Roulette 🎡",
    "4. Feedback-Tresor"
])

# --- MODULE ---
# --- SETZE DAS HIER DIREKT ÜBER ZEILE 74 (vor das erste IF) --
# 1. Aufgaben zählen für die Stimmung
offene_tasks = [p for p in st.session_state.db["pflichten"] if p.get("status") == "Offen"]
anzahl = len(offene_tasks)

# 2. Stimmung ermitteln
if anzahl == 0:
    mood, color = "😊 Pummeluff ist glücklich!", "#00ff00"
elif anzahl <= 2:
    mood, color = "😴 Pummeluff wird schläfrig...", "#ffaa00"
else:
    mood, color = "😠 Pummeluff singt gleich!", "#ff4b4b"

# 3. Anzeige im Dashboard (Zentriert ganz oben)
st.markdown(f"<h1 style='text-align: center;'>{mood}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: {color};'>Sektor-Status: {anzahl} offene Pflichten</p>", unsafe_allow_html=True)
st.divider()
    # ...
if menu == "1. Wochen-Matrix (Editor)":
    st.header("📅 Strategische Wochenübersicht")
    stunden = [f"{i:02d}:00 Uhr" for i in range(6, 22)]
    tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

    # DF erstellen aus DB
    df = pd.DataFrame("", index=stunden, columns=tage)
    for key, val in st.session_state.db["matrix"].items():
        if "|" in key:
            t, z = key.split("|")
            if t in tage and z in stunden: df.at[z, t] = val

    # Der Patch: Interaktiver Editor
    edited_df = st.data_editor(df, use_container_width=True, height=500, key="matrix_editor")

    if st.button("💾 Änderungen in Cloud-Tresor brennen"):
        for t in tage:
            for z in stunden:
                st.session_state.db["matrix"][f"{t}|{z}"] = edited_df.at[z, t]
        save_and_sync(st.session_state.db)
        st.success("Matrix synchronisiert! 🎈")
        st.rerun()

elif menu == "2. Schiedsrichter (Verträge)":
    st.header("⚖️ Schiedsrichter-Logik")
    col1, col2 = st.columns(2)
    with col1:
        with st.form("pflicht"):
            aufgabe = st.text_input("Neue Pflicht/Aufgabe")
            wer = st.multiselect("Verantwortlich", st.session_state.db["user_config"])
            if st.form_submit_button("Vertrag besiegeln 🤝"):
                st.session_state.db["pflichten"].append({"aufgabe": aufgabe, "wer": wer, "status": "Offen", "id": random.randint(1000,9999)})
                save_and_sync(st.session_state.db)
                st.rerun()
    with col2:
        st.subheader("Offene Verträge")
        for p in st.session_state.db["pflichten"]:
            st.write(f"📌 **{p['aufgabe']}** -> {', '.join(p['wer'])}")

elif menu == "3. Pflichten-Roulette 🎡":
    st.header("🎡 Sektor-Roulette")
    st.write("Wer wird heute vom Schicksal (Pummeluff) erwählt?")

    if st.button("DRAUFDRÜCKEN & HOFFEN! 🚀"):
        if st.session_state.db["pflichten"]:
            # Animation
            placeholder = st.empty()
            for _ in range(10):
                temp_user = random.choice(st.session_state.db["user_config"])
                placeholder.metric("Zielperson wird ermittelt...", temp_user)
                time.sleep(0.1)

            victim = random.choice(st.session_state.db["user_config"])
            task = random.choice([p['aufgabe'] for p in st.session_state.db["pflichten"]])

            placeholder.empty()
            st.warning(f"🚨 **{victim}** wurde für die Aufgabe **'{task}'** auserwählt!")
            st.balloons()
        else:
            st.info("Keine Pflichten im Speicher. Das Roulette hat heute Sendepause!")

elif menu == "4. Feedback-Tresor":
    st.header("📥 Sektor-Feedback")
    msg = st.text_area("Nachricht an den Sektor...")
    if st.button("Senden"):
        st.session_state.db["feedback"].append({"datum": str(datetime.now()), "msg": msg})
        save_and_sync(st.session_state.db)
        st.balloons()


