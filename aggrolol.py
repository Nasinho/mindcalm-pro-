import streamlit as st
import os
import json
from datetime import datetime
from google import genai
from google.genai import types
import streamlit_authenticator as stauth

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="MindCalm Pro", page_icon="🌱", layout="wide")

# --- USER DATENBANK (Für die Demo direkt im Code) ---
# In der Praxis werden diese Passwörter als Hashes gespeichert.
credentials = {
    "usernames": {
        "toenni": {
            "name": "Melibär",
            "password": "Aggrobär" # Vergib hier dein Wunschpasswort
        }
    }
}

# Passwort-Hasher für den Authenticator initialisieren
# --- SO IST ES RICHTIG FÜR VERSION 0.4.2 ---
for username, user_info in credentials['usernames'].items():
    # Der neue Hasher wird ohne Argumente instanziiert, danach hashen wir den String direkt
    credentials['usernames'][username]['password'] = stauth.Hasher.hash(user_info['password'])
authenticator = stauth.Authenticate(
    credentials,
    cookie_name="mindcalm_cookie",
    key="mindcalm_secret_key",
    cookie_expiry_days=30
)

# --- LOGIN INTERFACE ---
# --- SO IST ES RICHTIG FÜR VERSION 0.4.2 ---
# --- LOGIN INTERFACE ---
# Die Methode braucht jetzt zwingend ein Label, gibt aber nichts mehr zurück
authenticator.login(fields={'Form name': 'Login'})

# Wir holen uns die Werte direkt aus dem Session State von Streamlit
authentication_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")
name = st.session_state.get("name")

if authentication_status is False:
    st.error("Username/Passwort falsch, Bro. Versuchs nochmal.")
elif authentication_status is None:
    st.warning("Bitte logge dich ein, um MindCalm Pro zu nutzen.")
    st.info("Demo-Zugang: `toenni` mit Passwort `123`")

# --- WENN LOGGED IN, STARTET DIE APP ---
elif authentication_status:

    # --- MODERN GLASSMORPHISM CSS ---
    st.markdown("""
    <style>
        .stApp { 
            background: linear-gradient(135deg, #e0e7ff 0%, #f1f5f9 50%, #fef3c7 100%) !important;
            background-attachment: fixed !important;
        }
        h1, h2, h3, h4 { color: #0f172a !important; font-family: 'Inter', sans-serif; font-weight: 700 !important; }
        p, li, span, label { color: #334155 !important; font-family: 'Inter', sans-serif; }
        
        .glass-card {
            background: rgba(255, 255, 255, 0.45);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.6);
            padding: 24px;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.06);
        }
        .glass-card-green { background: rgba(240, 253, 244, 0.5); border-left: 6px solid #16a34a; }
        .glass-card-blue { background: rgba(240, 249, 255, 0.5); border-left: 6px solid #0284c7; }
        .glass-card-emergency { background: rgba(254, 242, 242, 0.6); border: 1px solid rgba(254, 205, 205, 0.7); border-top: 6px solid #ef4444; }
        
        .mascot-banner {
            background: rgba(255, 255, 255, 0.55);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.7);
            padding: 20px; border-radius: 16px; margin-bottom: 25px; display: flex; align-items: center; gap: 20px;
        }
        .mascot-avatar { font-size: 2.5rem; }
        
        /* Button Styles */
        .stButton>button { color: #0f172a !important; font-weight: 600 !important; border-radius: 12px !important; }
        .stButton>button:has(div:contains("🔴")), .stButton>button:contains("🔴") {
            background-color: #ef4444 !important; color: #ffffff !important; font-weight: 800 !important; border: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- CONFIG & INITIALISIERUNG ---
    # API-Key wird aus den Streamlit Secrets gezogen (für das Deployment)
    if "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = st.secrets.get("GEMINI_API_KEY", "HIER_DEIN_LOCAL_KEY_FALLS_NÖTIG")

    SYSTEM_PROMPT = """
    Du bist Liko, ein empathischer, absolut ruhiger und deeskalierender KI-Coach für Aggressionsbewältigung. 
    Deine Aufgabe ist es, Nutzern zu helfen, ihre Wut-Trigger zu reflektieren.
    Bringe das Gespräch nach ca. 3-4 Chatnachrichten aktiv zu einem positiven, konkreten Abschluss (z.B. rausgehen, Übung machen).
    """

    @st.cache_resource
    def get_gemini_client():
        return genai.Client()

    try: client = get_gemini_client()
    except Exception: st.warning("Gemini API-Key fehlt.")

    # --- USER-SPEZIFISCHE SPEICHERUNG ---
    # Jeder Nutzer bekommt eine eigene JSON-Datei auf dem Server basierend auf seinem Username
    DB_FILE = f"archive_{username}.json"

    def save_chat_to_user_history(history):
        if history:
            session_data = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "chat": history}
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    try: data = json.load(f)
                    except json.JSONDecodeError: data = []
            else: data = []
            data.append(session_data)
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    # Session States für den aktuellen User initialisieren
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    if "timeout_active" not in st.session_state: st.session_state.timeout_active = False

    # --- HEADER & LOGOUT ---
    st.markdown(f"""
    <div class="mascot-banner">
        <div class="mascot-avatar">🦎</div>
        <div>
            <h3 style="margin:0; color:#0f172a !important;">Hi {name}, ich bin Liko!</h3>
            <p style="margin:0; color:#475569 !important;">Schön, dass du eingeloggt bist. Lass uns deine Impulse gemeinsam ordnen.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Logout-Button oben rechts platzieren
    col_title_space, col_logout = st.columns([6, 1])
    with col_logout:
        authenticator.logout('Logout', 'main')

    st.title("MindCalm Pro")
    st.write(f"Eingeloggt als: **{name}**")
    st.markdown("---")

    # --- MAIN CONTENT ---
    tab_chat, tab_exercises, tab_archive = st.tabs(["🤖 KI-Reflexion mit Liko", "🧘 Übungs-Zentrum", "📂 Gespeicherte Sitzungen"])

    with tab_chat:
        st.write("### Interaktive Situations-Analyse")
        for role, text in st.session_state.chat_history:
            with st.chat_message(role): st.write(text)
        
        if user_input := st.chat_input("Was hat dich aufgebracht?"):
            st.session_state.chat_history.append(("user", user_input))
            st.rerun()
            
        if st.session_state.chat_history and st.session_state.chat_history[-1][0] == "user":
            with st.chat_message("assistant"):
                with st.spinner("Liko reflektiert..."):
                    try:
                        api_contents = []
                        for role, text in st.session_state.chat_history:
                            api_contents.append(types.Content(role="user" if role == "user" else "model", parts=[types.Part.from_text(text=text)]))
                        response = client.models.generate_content(
                            model='gemini-2.5-flash', contents=api_contents,
                            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.3)
                        )
                        st.session_state.chat_history.append(("assistant", response.text))
                        st.rerun()
                    except Exception as e: st.error(f"Fehler: {e}")
        
        if st.session_state.chat_history:
            st.markdown("---")
            if st.button("💾 Sitzung archivieren & Chat leeren"):
                save_chat_to_user_history(st.session_state.chat_history)
                st.session_state.chat_history = []
                st.success("In deinem Profil gespeichert!")
                st.rerun()

    with tab_exercises:
        st.write("### Mentale Werkzeuge & Übungen")
        st.markdown("""
        <div class="glass-card glass-card-green">
            <h4>🧠 1. Kognitives Reframing (Gedanken-Check)</h4>
            <p>Halt inne, wenn der Gedanke <strong>'Der macht das extra!'</strong> blockiert.</p>
        </div>
        <div class="glass-card glass-card-blue">
            <h4>💪 2. Blitz-Entspannung (PME)</h4>
            <p>Fäuste & Schultern für 5s maximal fest anspannen und abrupt lösen.</p>
        </div>
        <div class="glass-card glass-card-green">
            <h4>🌬️ 3. Box-Breathing (Taktatmen)</h4>
            <p>4s Einatmen ➡️ 4s Halten ➡️ 4s Ausatmen ➡️ 4s Halten.</p>
        </div>
        <div class="glass-card glass-card-blue">
            <h4>👀 4. Die 5-4-3-2-1 Erdungsmethode</h4>
            <p>Benenne 5 Dinge die du siehst, 4 die du spürst, 3 die du hörst, 2 die du riechst, 1 die du schmeckst.</p>
        </div>
        """, unsafe_allow_html=True)

    with tab_archive:
        st.write(f"### Archivierte Sitzungen von {name}")
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                try:
                    saved_data = json.load(f)
                    for entry in reversed(saved_data):
                        with st.expander(f"Sitzung vom {entry['timestamp']}"):
                            for role, text in entry["chat"]:
                                st.markdown(f"**{role.capitalize()}**: {text}")
                except Exception: st.info("Archiv leer.")
        else:
            st.info("Noch keine gespeicherten Sitzungen in deinem Profil gefunden.")

    # --- SIDE CONTENT (SOFORTHILFE) ---
    st.markdown("---")
    st.markdown('<div class="glass-card glass-card-emergency">', unsafe_allow_html=True)
    st.write("### 🚨 Soforthilfe")
    if st.button("🔴 TIME-OUT JETZT", use_container_width=True):
        st.session_state.timeout_active = True

    if st.session_state.timeout_active:
        if os.path.exists("calm_music.mp3"): st.audio("calm_music.mp3", format="audio/mp3", loop=True)
        st.info("4s Einatmen ➡️ 4s Halten ➡️ 4s Ausatmen. Komm erst mal runter.")
        if st.button("Ich bin wieder ruhig"):
            st.session_state.timeout_active = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)