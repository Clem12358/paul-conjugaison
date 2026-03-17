import streamlit as st
import random
import unicodedata
from supabase import create_client

# --- Config ---
ADMIN_PASSWORD = "23052003"
PERSONNES = ["je", "tu", "il/elle", "nous", "vous", "ils/elles"]
TEMPS = ["présent", "imparfait", "futur", "passé composé"]

st.set_page_config(page_title="Conjugaison", page_icon="⭐", layout="centered")

# --- Supabase client ---
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase()

# --- CSS ---
st.markdown("""
<style>
    .stTextInput input {
        font-size: 1.4rem !important;
        padding: 0.8rem !important;
    }
    .stButton button {
        font-size: 1.3rem !important;
        padding: 0.7rem 2rem !important;
        border-radius: 12px !important;
    }
    .question-card {
        background: linear-gradient(135deg, #e0f2fe, #f0e6ff);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        text-align: center;
        font-size: 1.6rem;
        font-weight: bold;
        color: #1e3a5f;
        border: 3px solid #a5b4fc;
    }
    .score-box {
        font-size: 1.4rem;
        font-weight: bold;
        color: #2563eb;
        text-align: right;
    }
    .big-title {
        font-size: 2.5rem;
        text-align: center;
        font-weight: bold;
        color: #7c3aed;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .success-box {
        background: #d1fae5;
        border: 2px solid #34d399;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        font-size: 1.3rem;
        color: #065f46;
        margin: 1rem 0;
    }
    .error-box {
        background: #fef3c7;
        border: 2px solid #fbbf24;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        font-size: 1.3rem;
        color: #92400e;
        margin: 1rem 0;
    }
    .result-box {
        background: linear-gradient(135deg, #fdf2f8, #ede9fe);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        border: 3px solid #c084fc;
    }
</style>
""", unsafe_allow_html=True)


# --- Data helpers (Supabase) ---
def load_verbs():
    """Load all verbs from Supabase and return as nested dict."""
    response = supabase.table("conjugaisons").select("*").execute()
    data = {}
    for row in response.data:
        inf = row["infinitif"]
        temps = row["temps"]
        personne = row["personne"]
        reponse = row["reponse"]
        if inf not in data:
            data[inf] = {}
        if temps not in data[inf]:
            data[inf][temps] = {}
        data[inf][temps][personne] = reponse
    return data


def save_verb(infinitif, forms):
    """Save/update a verb's conjugations in Supabase."""
    # Delete existing entries for this verb
    supabase.table("conjugaisons").delete().eq("infinitif", infinitif).execute()
    # Insert all new entries
    rows = []
    for temps in TEMPS:
        for personne in PERSONNES:
            rows.append({
                "infinitif": infinitif,
                "temps": temps,
                "personne": personne,
                "reponse": forms[temps][personne]
            })
    supabase.table("conjugaisons").insert(rows).execute()


def delete_verb(infinitif):
    """Delete a verb from Supabase."""
    supabase.table("conjugaisons").delete().eq("infinitif", infinitif).execute()


# --- Answer comparison ---
def normalize(text):
    text = text.strip().lower()
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = unicodedata.normalize("NFC", text)
    text = " ".join(text.split())
    return text


def strip_accents(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def check_answer(user_input, expected):
    u = normalize(user_input)
    e = normalize(expected)
    if u == e:
        return "correct"
    if strip_accents(u) == strip_accents(e):
        return "almost"
    return "wrong"


# --- Session state init ---
if "mode" not in st.session_state:
    st.session_state.mode = "accueil"
if "selected_verbs" not in st.session_state:
    st.session_state.selected_verbs = []
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "total_answered" not in st.session_state:
    st.session_state.total_answered = 0
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "feedback_type" not in st.session_state:
    st.session_state.feedback_type = None
if "feedback_answer" not in st.session_state:
    st.session_state.feedback_answer = ""
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
if "select_all" not in st.session_state:
    st.session_state.select_all = False


# --- Load verbs ---
verbes_data = load_verbs()


# ============================================================
# ACCUEIL
# ============================================================
def show_accueil():
    st.markdown('<div class="big-title">⭐ Conjugaison ⭐</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Entraine-toi a conjuguer les verbes !</div>', unsafe_allow_html=True)

    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Je veux m'entrainer !", type="primary", use_container_width=True):
            st.session_state.mode = "selection"
            st.session_state.selected_verbs = []
            st.session_state.questions = []
            st.session_state.select_all = False
            st.rerun()

    st.write("")
    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🔒 Administration", use_container_width=True):
            st.session_state.mode = "admin"
            st.session_state.admin_authenticated = False
            st.rerun()


# ============================================================
# SELECTION DES VERBES
# ============================================================
def show_selection():
    st.markdown('<div class="big-title">📚 Choisis tes verbes</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Coche les verbes que tu veux reviser</div>', unsafe_allow_html=True)

    verbes_list = sorted(verbes_data.keys())

    # --- Selection des temps ---
    st.markdown("**Quels temps veux-tu reviser ?**")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("✅ Tous les temps"):
            for t in TEMPS:
                st.session_state[f"ct_{t}"] = True
            st.rerun()
    with col_t2:
        if st.button("❌ Aucun temps"):
            for t in TEMPS:
                st.session_state[f"ct_{t}"] = False
            st.rerun()

    selected_temps = []
    cols_t = st.columns(len(TEMPS))
    for i, temps in enumerate(TEMPS):
        with cols_t[i]:
            if st.checkbox(temps.capitalize(), value=True, key=f"ct_{temps}"):
                selected_temps.append(temps)

    st.write("")

    # --- Selection des verbes ---
    st.markdown("**Quels verbes veux-tu reviser ?**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Tous les verbes"):
            for verbe in verbes_list:
                st.session_state[f"cb_{verbe}"] = True
            st.rerun()
    with col2:
        if st.button("❌ Aucun verbe"):
            for verbe in verbes_list:
                st.session_state[f"cb_{verbe}"] = False
            st.rerun()

    selected = []
    nb_cols = 3
    cols = st.columns(nb_cols)
    for i, verbe in enumerate(verbes_list):
        with cols[i % nb_cols]:
            if st.checkbox(verbe.capitalize(), key=f"cb_{verbe}"):
                selected.append(verbe)

    st.write("")

    # --- Nombre de questions ---
    max_possible = len(selected) * len(selected_temps) * len(PERSONNES)
    st.markdown("**Combien de questions ?**")
    if max_possible > 0:
        nb_questions = st.slider(
            "Nombre de questions :",
            min_value=5,
            max_value=max_possible,
            value=min(20, max_possible),
            step=5
        )
    else:
        nb_questions = 0

    st.write("")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if len(selected) > 0 and len(selected_temps) > 0:
            if st.button("🎯 C'est parti !", type="primary", use_container_width=True):
                st.session_state.selected_verbs = selected
                st.session_state.selected_temps = selected_temps
                st.session_state.nb_questions = nb_questions
                generate_questions(selected, selected_temps, nb_questions)
                st.session_state.mode = "quiz"
                st.rerun()
        else:
            st.info("Coche au moins un verbe et un temps pour commencer !")

    st.write("")
    if st.button("⬅️ Retour"):
        st.session_state.mode = "accueil"
        st.rerun()


def generate_questions(selected_verbs, selected_temps, nb_questions):
    all_questions = []
    for verbe in selected_verbs:
        data = verbes_data[verbe]
        for temps in selected_temps:
            if temps in data:
                for personne in PERSONNES:
                    if personne in data[temps]:
                        all_questions.append({
                            "verbe": verbe,
                            "temps": temps,
                            "personne": personne,
                            "reponse": data[temps][personne]
                        })
    random.shuffle(all_questions)
    st.session_state.questions = all_questions[:nb_questions]
    st.session_state.current_q = 0
    st.session_state.score = 0
    st.session_state.total_answered = 0
    st.session_state.show_feedback = False


# ============================================================
# QUIZ
# ============================================================
def show_quiz():
    questions = st.session_state.questions
    idx = st.session_state.current_q

    if idx >= len(questions):
        show_results()
        return

    q = questions[idx]

    # Progress
    progress = idx / len(questions)
    st.progress(progress)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Question {idx + 1} / {len(questions)}**")
    with col2:
        st.markdown(
            f'<div class="score-box">Score : {st.session_state.score} / {st.session_state.total_answered}</div>',
            unsafe_allow_html=True
        )

    # Question card
    personne_display = q["personne"].capitalize()
    st.markdown(
        f'<div class="question-card">{personne_display} ______ ({q["verbe"]}, {q["temps"]})</div>',
        unsafe_allow_html=True
    )

    # Feedback or input
    if st.session_state.show_feedback:
        if st.session_state.feedback_type == "correct":
            st.markdown(
                '<div class="success-box">🎉 Bravo ! C\'est correct !</div>',
                unsafe_allow_html=True
            )
        elif st.session_state.feedback_type == "almost":
            st.markdown(
                f'<div class="success-box">👍 Presque ! Pense aux accents.<br>'
                f'La bonne reponse : <b>{st.session_state.feedback_answer}</b></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="error-box">Pas tout a fait...<br>'
                f'La bonne reponse etait : <b>{st.session_state.feedback_answer}</b></div>',
                unsafe_allow_html=True
            )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("➡️ Question suivante", type="primary", use_container_width=True):
                st.session_state.current_q += 1
                st.session_state.show_feedback = False
                st.rerun()
    else:
        user_answer = st.text_input(
            "Ta reponse :",
            key=f"answer_{idx}",
            placeholder="Ecris ta reponse ici..."
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✅ Verifier", type="primary", use_container_width=True):
                if user_answer.strip():
                    result = check_answer(user_answer, q["reponse"])
                    st.session_state.total_answered += 1
                    st.session_state.feedback_answer = q["reponse"]
                    if result == "correct":
                        st.session_state.score += 1
                        st.session_state.feedback_type = "correct"
                    elif result == "almost":
                        st.session_state.score += 1
                        st.session_state.feedback_type = "almost"
                    else:
                        st.session_state.feedback_type = "wrong"
                    st.session_state.show_feedback = True
                    st.rerun()
                else:
                    st.warning("Ecris une reponse avant de verifier !")

    st.write("")
    if st.button("⬅️ Arreter l'entrainement"):
        st.session_state.mode = "accueil"
        st.session_state.questions = []
        st.rerun()


# ============================================================
# RESULTATS
# ============================================================
def show_results():
    score = st.session_state.score
    total = st.session_state.total_answered

    if total > 0:
        pct = score / total * 100
    else:
        pct = 0

    if pct >= 90:
        emoji = "🏆"
        message = "Fantastique ! Tu es un champion !"
    elif pct >= 70:
        emoji = "🌟"
        message = "Tres bien ! Continue comme ca !"
    elif pct >= 50:
        emoji = "💪"
        message = "Pas mal ! Tu progresses !"
    else:
        emoji = "🌈"
        message = "Continue a t'entrainer, tu vas y arriver !"

    st.markdown(
        f'<div class="result-box">'
        f'<div style="font-size:3rem;">{emoji}</div>'
        f'<div style="font-size:1.8rem;font-weight:bold;margin:1rem 0;">{message}</div>'
        f'<div style="font-size:1.4rem;">Tu as eu <b>{score}</b> / <b>{total}</b> bonnes reponses !</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Recommencer", use_container_width=True):
            generate_questions(
                st.session_state.selected_verbs,
                st.session_state.get("selected_temps", TEMPS),
                st.session_state.get("nb_questions", 20)
            )
            st.session_state.mode = "quiz"
            st.rerun()
    with col2:
        if st.button("📚 Autres verbes", use_container_width=True):
            st.session_state.mode = "selection"
            st.session_state.select_all = False
            st.rerun()
    with col3:
        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state.mode = "accueil"
            st.rerun()


# ============================================================
# ADMIN
# ============================================================
def show_admin():
    st.markdown("### 🔒 Mode Administration")

    if not st.session_state.admin_authenticated:
        password = st.text_input("Mot de passe :", type="password", key="admin_pwd")
        if st.button("Entrer"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")

        if st.button("⬅️ Retour"):
            st.session_state.mode = "accueil"
            st.rerun()
        return

    # Authenticated
    tab1, tab2 = st.tabs(["Ajouter un verbe", "Voir / Modifier les verbes"])

    with tab1:
        show_admin_add()

    with tab2:
        show_admin_edit()

    st.write("")
    if st.button("⬅️ Retour a l'accueil"):
        st.session_state.mode = "accueil"
        st.session_state.admin_authenticated = False
        st.rerun()


def show_admin_add():
    st.subheader("Ajouter un nouveau verbe")

    infinitif = st.text_input("Infinitif du verbe :", key="add_infinitif")

    forms = {}
    for temps in TEMPS:
        st.markdown(f"**{temps.capitalize()}**")
        forms[temps] = {}
        col1, col2 = st.columns(2)
        for i, personne in enumerate(PERSONNES):
            with (col1 if i < 3 else col2):
                forms[temps][personne] = st.text_input(
                    f"{personne} :",
                    key=f"add_{temps}_{personne}"
                )

    if st.button("💾 Enregistrer le verbe", type="primary"):
        if not infinitif.strip():
            st.error("Entre l'infinitif du verbe.")
            return

        verb_key = infinitif.strip().lower()

        # Check all fields filled
        empty_fields = []
        for temps in TEMPS:
            for personne in PERSONNES:
                if not forms[temps][personne].strip():
                    empty_fields.append(f"{temps} - {personne}")

        if empty_fields:
            st.error(f"Il manque des conjugaisons : {', '.join(empty_fields[:5])}...")
            return

        # Save to Supabase
        clean_forms = {}
        for temps in TEMPS:
            clean_forms[temps] = {}
            for personne in PERSONNES:
                clean_forms[temps][personne] = forms[temps][personne].strip()

        save_verb(verb_key, clean_forms)
        st.success(f"Le verbe '{verb_key}' a ete ajoute !")
        st.cache_data.clear()
        st.rerun()


def show_admin_edit():
    st.subheader("Voir / Modifier les verbes")

    verbes_list = sorted(verbes_data.keys())

    if not verbes_list:
        st.info("Aucun verbe enregistre.")
        return

    selected_verb = st.selectbox(
        "Choisir un verbe :",
        verbes_list,
        format_func=lambda x: x.capitalize()
    )

    if selected_verb:
        verb_data = verbes_data[selected_verb]

        forms = {}
        for temps in TEMPS:
            st.markdown(f"**{temps.capitalize()}**")
            forms[temps] = {}
            col1, col2 = st.columns(2)
            current_data = verb_data.get(temps, {})
            for i, personne in enumerate(PERSONNES):
                with (col1 if i < 3 else col2):
                    forms[temps][personne] = st.text_input(
                        f"{personne} :",
                        value=current_data.get(personne, ""),
                        key=f"edit_{selected_verb}_{temps}_{personne}"
                    )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Sauvegarder les modifications", type="primary"):
                clean_forms = {}
                for temps in TEMPS:
                    clean_forms[temps] = {}
                    for personne in PERSONNES:
                        clean_forms[temps][personne] = forms[temps][personne].strip()
                save_verb(selected_verb, clean_forms)
                st.success("Modifications sauvegardees !")
                st.rerun()

        with col2:
            if st.button("🗑️ Supprimer ce verbe"):
                st.session_state.confirm_delete = selected_verb
                st.rerun()

        if st.session_state.get("confirm_delete") == selected_verb:
            st.warning(f"Es-tu sure de vouloir supprimer '{selected_verb}' ?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Oui, supprimer", type="primary"):
                    delete_verb(selected_verb)
                    st.session_state.confirm_delete = None
                    st.success(f"'{selected_verb}' supprime !")
                    st.rerun()
            with c2:
                if st.button("Non, annuler"):
                    st.session_state.confirm_delete = None
                    st.rerun()


# ============================================================
# ROUTER
# ============================================================
mode = st.session_state.mode

if mode == "accueil":
    show_accueil()
elif mode == "selection":
    show_selection()
elif mode == "quiz":
    show_quiz()
elif mode == "admin":
    show_admin()
else:
    st.session_state.mode = "accueil"
    st.rerun()
