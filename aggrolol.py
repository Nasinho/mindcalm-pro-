import streamlit as st
import os
import json
from datetime import datetime
from google import genai
from google.genai import types

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="MindCalm Pro", page_icon="🌱", layout="wide")

# --- MODERN GLASSMORPHISM & RESPONSIVE CSS ---
st.markdown("""
<style>
    /* Sanfter, moderner Verlauf im Hintergrund, der durch das Glas schimmert */
    .stApp { 
        background: linear-gradient(135deg, #e0e7ff 0%, #f1f5f9 50%, #fef3c7 100%) !important;
        background-attachment: fixed !important;
    }
    
    /* Globale Typografie */
    h1, h2, h3, h4 { color: #0f172a !important; font-family: 'Inter', system-ui, sans-serif; font-weight: 700 !important; }
    p, li, span, label { color: #334155 !important; font-family: 'Inter', system-ui, sans-serif; }

    /* RESPONSIVES LAYOUT via CSS Flexbox statt Streamlit Columns */
    .responsive-container {
        display: flex;
        flex-direction: row;
        gap: 25px;
        width: 100%;
        margin-top: 20px;
    }
    
    .main-content { flex: 2; min-width: 300px; }
    .side-content { flex: 1; min-width: 280px; }

    /* Handy-Optimierung: Wenn der Bildschirm kleiner als 800px ist, Spalten untereinander brechen */
    @media (max-width: 800px) {
        .responsive-container { flex-direction: column; }
        .main-content { width: 100%; }
        .side-content { width: 100%; }
    }

    /* GLASSMORPHISMUS KARTEN-STYLING */
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
    
    /* Farbige Akzente für die Glas-Karten im Übungszentrum */
    .glass-card-green {
        background: rgba(240, 253, 244, 0.5);
        border-left: 6px solid #16a34a;
    }
    .glass-card-blue {
        background: rgba(240, 249, 255, 0.5);
        border-left: 6px solid #0284c7;
    }
    
    /* Notfall-Box im Glas-Design */
    .glass-card-emergency {
        background: rgba(254, 242, 242, 0.6);
        border: 1px solid rgba(254, 205, 205, 0.7);
        border-top: 6px solid #ef4444;
    }

    /* Maskottchen Banner */
    .mascot-banner {
        background: rgba(255, 255, 255, 0.55);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.7);
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        gap: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.04);
    }
    .mascot-avatar { font-size: 2.5rem; }
    
    /* Tabs Clean Design */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; color: #64748b; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #0f172a; font-weight: 600; }
            
    .stButton>button[data-testid="baseButton-primary"] {
        background-color: #ef4444 !important;
        color: #ffffff !important;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4) !important;
    }
    .stButton>button[data-testid="baseButton-primary"]:hover {
        background-color: #dc2626 !important;
        color: #ffffff !important;
    }
    .stButton>button[data-testid="baseButton-secondary"] {
        background-color: #ef4444 !important;
        color: #ffffff !important;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4) !important;
</style>
""", unsafe_allow_html=True)

# --- CONFIG & INITIALISIERUNG ---
os.environ["GEMINI_API_KEY"] = "AQ.Ab8RN6KFBI2Yz_1hC-Mh_G7Zi-lRKnqUbOAhUaa-3QTqsSbmwA"

SYSTEM_PROMPT = """
Du bist Liko, ein empathischer, absolut ruhiger und deeskalierender KI-Coach für Aggressionsbewältigung. 
Stelle dich in der ersten Nachricht kurz als Liko vor, falls der Verlauf noch leer ist.
Deine Aufgabe ist es, Nutzern zu helfen, ihre Wut-Trigger zu reflektieren.

WICHTIGE REGEL FÜR DEN GESPRÄCHSABSCHLUSS:
Führe kein endloses Gespräch und verfalle nicht in Schleifen. Sobald der Nutzer den Vorfall geschildert hat und du eine analytische Rückfrage gestellt hast (nach ca. 3-4 Chatnachrichten insgesamt), 
bringe das Gespräch aktiv zu einem positiven, konkreten Abschluss. 
Empfiehl dem Nutzer ausdrücklich, jetzt das Gerät wegzulegen und eine reale, beruhigende Aktion zu starten (z. B. 'Geh ein paar Minuten an die frische Luft', 'Trink ein Glas kaltes Wasser' oder 'Mache eine der Übungen aus dem Menü').
Verabschiede dich freundlich und signalisiere, dass die Sitzung damit beendet ist.
"""

@st.cache_resource
def get_gemini_client():
    return genai.Client()

try:
    client = get_gemini_client()
except Exception:
    st.warning("Gemini API-Key nicht gefunden. Bitte im Code hinterlegen.")

DB_FILE = "chat_history_archive.json"

def save_chat_to_history(history):
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

if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "timeout_active" not in st.session_state: st.session_state.timeout_active = False

# --- HEADER BEREICH ---
st.markdown("""
<div class="mascot-banner">
    <div class="mascot-avatar">🦎</div>
    <div>
        <h3 style="margin:0; color:#0f172a !important;">Hi, ich bin Liko!</h3>
        <p style="margin:0; color:#475569 !important;">Lass uns deine Impulse gemeinsam ordnen. Atme tief durch.</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.title("MindCalm Pro")
st.write("Dein geschützter Online-Raum für Entlastung und Klarheit.")

# --- START DES RESPONSIVEN HTML-CONTAINERS (AUSKOMMENTIERT) ---
# st.markdown('<div class="responsive-container">', unsafe_allow_html=True)

# --- SPALTE 1: MAIN CONTENT (CHAT, ÜBUNGEN, ARCHIV) (AUSKOMMENTIERT) ---
# st.markdown('<div class="main-content">', unsafe_allow_html=True)
# st.markdown('<div class="glass-card">', unsafe_allow_html=True)

tab_chat, tab_exercises, tab_archive = st.tabs(["🤖 KI-Reflexion mit Liko", "🧘 Übungs-Zentrum", "📂 Gespeicherte Sitzungen"])

with tab_chat:
    st.write("### Interaktive Situations-Analyse")
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(text)
    
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
                        model='gemini-2.5-flash',
                        contents=api_contents,
                        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.3)
                    )
                    st.session_state.chat_history.append(("assistant", response.text))
                    st.rerun()
                except Exception as e: 
                    st.error(f"Fehler: {e}")
    
    if st.session_state.chat_history:
        st.markdown("---")
        if st.button("💾 Sitzung archivieren & Chat leeren"):
            save_chat_to_history(st.session_state.chat_history)
            st.session_state.chat_history = []
            st.success("Sitzung gespeichert!")
            st.rerun()

with tab_exercises:
    st.write("### Mentale Werkzeuge & Übungen")
    
    # ÜBUNG 1
    st.markdown("""
    <div class="glass-card glass-card-green">
        <h4>🧠 1. Kognitives Reframing (Gedanken-Check)</h4>
        <p>Halt inne, wenn der Gedanke <strong>'Der macht das extra!'</strong> blockiert:</p>
        <ul>
            <li><strong>Fakten:</strong> Was ist rein objektiv passiert?</li>
            <li><strong>Perspektiven:</strong> Welche 3 anderen Gründe (Stress, Versehen) gibt es?</li>
            <li><strong>Relevanz:</strong> Wichtig in 6 Monaten?</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # ÜBUNG 2
    st.markdown("""
    <div class="glass-card glass-card-blue">
        <h4>💪 2. Blitz-Entspannung (PME)</h4>
        <p>Körperlichen Druck schlagartig abbauen:</p>
        <ol>
            <li><strong>Spannen:</strong> Fäuste & Schultern für 5s maximal fest anspannen.</li>
            <li><strong>Halten:</strong> Die Spannung bewusst im Körper wahrnehmen.</li>
            <li><strong>Lösen:</strong> Kräftig ausatmen und alles auf einmal komplett lockerlassen.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # ÜBUNG 3
    st.markdown("""
    <div class="glass-card glass-card-green">
        <h4>🌬️ 3. Box-Breathing (Taktatmen gegen den Stresstunnel)</h4>
        <p>Diese Methode senkt über das vegetative Nervensystem sofort deinen Puls, wenn die Wut hochkocht:</p>
        <ul>
            <li><strong>4 Sekunden:</strong> Tief in den Bauch einatmen.</li>
            <li><strong>4 Sekunden:</strong> Die Luft komplett anhalten und zur Ruhe kommen.</li>
            <li><strong>4 Sekunden:</strong> Langsam und gleichmäßig ausatmen.</li>
            <li><strong>4 Sekunden:</strong> Mit leeren Lungen halten, bevor der nächste Atemzug kommt.</li>
        </ul>
        <p><em>Wiederhole diesen Kreis 4-mal, um das biologische Alarmsignal im Gehirn zu stoppen.</em></p>
    </div>
    """, unsafe_allow_html=True)

    # ÜBUNG 4
    st.markdown("""
    <div class="glass-card glass-card-blue">
        <h4>👀 4. Die 5-4-3-2-1 Erdungsmethode (Zurück ins Hier & Jetzt)</h4>
        <p>Wenn die Aggression dich emotional komplett einnimmt, lenke deine Sinne bewusst um, um den Fokus vom Trigger wegzureißen:</p>
        <ol>
            <li><strong>5 Dinge sehen:</strong> Benenne fünf Gegenstände in deiner direkten Umgebung (z.B. den Stift, die Lampe).</li>
            <li><strong>4 Dinge spüren:</strong> Nimm vier körperliche Kontakte wahr (z.B. die Füße auf dem Boden, den Stoff der Hose).</li>
            <li><strong>3 Dinge hören:</strong> Achte auf drei Geräusche um dich herum (z.B. das Summen des PCs, Vogelzwitschern).</li>
            <li><strong>2 Dinge riechen:</strong> Versuche zwei Gerüche isoliert wahrzunehmen (z.B. Kaffee, frische Luft).</li>
            <li><strong>1 Ding schmecken:</strong> Konzentriere dich auf einen Geschmack im Mund.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

with tab_archive:
    st.write("### Archivierte Sitzungen")
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
        st.info("Noch keine Daten vorhanden.")

# st.markdown('</div>', unsafe_allow_html=True) # Ende glass-card
# st.markdown('</div>', unsafe_allow_html=True) # Ende main-content

st.markdown("---")

# --- SPALTE 2: SIDE CONTENT (SOFORTHILFE) ---
# st.markdown('<div class="side-content">', unsafe_allow_html=True)
st.write("### 🚨 Soforthilfe")
st.write("Aktiviere das begleitete Time-Out bei akutem Druck.")

if st.button("🔴 TIME-OUT JETZT", use_container_width=True, type="primary"):
    st.session_state.timeout_active = True

if st.session_state.timeout_active:
    st.write("**1. Augen zu.**")
    st.write("**2. Audio starten:**")
    
    if os.path.exists("calm_music.mp3"):
        st.audio("calm_music.mp3", format="audio/mp3", loop=True)
    else:
        st.warning("'calm_music.mp3' fehlt!")
        
    st.write("**3. Rhythmus-Atmen:**")
    st.info("4s Einatmen ➡️ 4s Halten ➡️ 4s Ausatmen")
    
    if st.button("Ich bin wieder ruhig", use_container_width=True, type="primary"):
        st.session_state.timeout_active = False
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True) # Ende glass-card
st.caption("📞 **Notfall-Seelsorge:**\n0800 111 0 111 (Kostenlos & anonym)")
st.markdown('</div>', unsafe_allow_html=True)

# st.markdown('</div>', unsafe_allow_html=True) # Ende side-content
# st.markdown('</div>', unsafe_allow_html=True) # Ende responsive-container