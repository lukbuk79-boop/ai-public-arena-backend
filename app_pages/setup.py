import hashlib
import random
import time

import streamlit as st

from utils.config import (
    t, PRESET_KEYS, TEMPERAMENT_KEYS, EXPERTISE_KEYS, LENGTH_KEYS,
    GOAL_KEYS, RULE_KEYS, MODE_KEYS, PRESETS,
)
from utils.pdf_export import extract_text_from_file

MAX_PERSONA_CHARS = 10000
MAX_TOPIC_CHARS = 45000

# Které režimy mají jakého účastníka (musí odpovídat logice v arena.py)
HUMAN_B_MODES = ("ai_vs_human", "ai_vs_human_vs_human")
HAS_C_MODES = ("ai_vs_ai_vs_ai", "ai_vs_ai_vs_human", "ai_vs_human_vs_human")
HUMAN_C_MODES = ("ai_vs_ai_vs_human", "ai_vs_human_vs_human")

is_simple = st.session_state.get("debate_type", "advanced") == "simple"

if is_simple and st.session_state.setup_step == 1:
    st.session_state.setup_step = 2
    st.session_state.debate_mode = "ai_vs_ai"

TEMPERAMENT_OPTIONS = ["undefined"] + [k for k in TEMPERAMENT_KEYS if k != "undefined"]
EXPERTISE_OPTIONS = ["undefined"] + [k for k in EXPERTISE_KEYS if k != "undefined"]
NO_KEY_LABEL = "(Zadejte klíč)" if st.session_state.lang == "cs" else "(Enter a key)"


# --------------------------------------------------------------------------
# Pomocné funkce a callbacky
# --------------------------------------------------------------------------
def format_temperament(k):
    if k == "undefined":
        return "Nedefinováno" if st.session_state.lang == "cs" else "Undefined"
    return t(f"temperament_{k}")


def format_expertise(k):
    if k == "undefined":
        return "Nedefinováno" if st.session_state.lang == "cs" else "Undefined"
    return t(f"expertise_{k}")


def update_state(widget_key, state_key):
    st.session_state[state_key] = st.session_state[widget_key]


def clear_widget_state():
    for k in list(st.session_state.keys()):
        if k.startswith("w_"):
            del st.session_state[k]


def apply_preset_callback():
    preset = st.session_state.w_preset
    st.session_state.preset_select = preset
    if preset == "custom" or preset not in PRESETS:
        return
    cfg = PRESETS[preset]
    st.session_state.response_length = cfg["response_length"]
    st.session_state.debate_goal = cfg["debate_goal"]
    st.session_state.debate_rules = list(cfg["debate_rules"])
    st.session_state.temperament_a = cfg["temperament_a"]
    st.session_state.expertise_a = cfg["expertise_a"]
    st.session_state.temperament_b = cfg["temperament_b"]
    st.session_state.expertise_b = cfg["expertise_b"]
    st.session_state.temperament_c = cfg["temperament_a"]
    st.session_state.expertise_c = cfg["expertise_a"]
    # Widgety v expanderu mají vlastní klíče – bez tohoto by po změně presetu
    # ukazovaly staré hodnoty, i když stav aplikace už je jiný.
    st.session_state.w_length = cfg["response_length"]
    st.session_state.w_goal = cfg["debate_goal"]
    st.session_state.w_rules = list(cfg["debate_rules"])


def randomize_persona(prefix):
    valid_temperaments = [k for k in TEMPERAMENT_KEYS if k != "undefined"]
    valid_expertises = [k for k in EXPERTISE_KEYS if k != "undefined"]
    new_t = random.choice(valid_temperaments)
    new_e = random.choice(valid_expertises)
    st.session_state[f"temperament_{prefix}"] = new_t
    st.session_state[f"expertise_{prefix}"] = new_e
    st.session_state[f"w_temperament_{prefix}"] = new_t
    st.session_state[f"w_expertise_{prefix}"] = new_e


# Callbacky samy způsobí rerun – st.rerun() uvnitř callbacku je zbytečné.
def go_next():
    st.session_state.setup_step += 1
    clear_widget_state()


def go_back():
    st.session_state.setup_step -= 1
    clear_widget_state()


def load_persona_file(uploaded, prefix):
    """Načte instrukce osobnosti ze souboru (md/txt) do stavu aplikace."""
    if uploaded is None:
        return
    uploaded.seek(0)
    text = extract_text_from_file(uploaded)
    if len(text) > MAX_PERSONA_CHARS:
        st.warning(t("err_persona_too_long"))
        text = text[:MAX_PERSONA_CHARS]
    st.session_state[f"w_role_{prefix}_prompt"] = text
    st.session_state[f"role_{prefix}_prompt"] = text


def render_ai_persona(p):
    """Formulář AI osobnosti (A/B/C). Pro C se nikdy nevolá v jednoduchém režimu."""
    letter = p.upper()
    st.text_input(
        f"{t('name')} {letter}", key=f"w_role_{p}_name",
        on_change=update_state, args=(f"w_role_{p}_name", f"role_{p}_name"),
    )
    st.selectbox(
        f"{t('provider_select')} {letter}:", select_options, key=f"w_provider_{p}",
        on_change=update_state, args=(f"w_provider_{p}", f"provider_{p}"),
    )

    if not is_simple:
        col_t, col_e = st.columns(2)
        with col_t:
            st.selectbox(
                t("temperament_label"), options=TEMPERAMENT_OPTIONS, format_func=format_temperament,
                key=f"w_temperament_{p}", on_change=update_state,
                args=(f"w_temperament_{p}", f"temperament_{p}"), help=t("temperament_hint"),
            )
        with col_e:
            st.selectbox(
                t("expertise_label"), options=EXPERTISE_OPTIONS, format_func=format_expertise,
                key=f"w_expertise_{p}", on_change=update_state,
                args=(f"w_expertise_{p}", f"expertise_{p}"), help=t("temperament_hint"),
            )
        st.button(t("random_button"), key=f"random_{p}", on_click=randomize_persona, args=(p,), use_container_width=True)

    st.radio(
        f"{t('input_type')} {letter}:", options=["manual", "upload"], format_func=lambda x: t(x),
        key=f"w_input_type_{p}", on_change=update_state,
        args=(f"w_input_type_{p}", f"input_type_{p}"),
    )

    if st.session_state[f"w_input_type_{p}"] == "manual":
        st.text_area(
            f"{t('instructions')} {letter}", key=f"w_role_{p}_prompt",
            on_change=update_state, args=(f"w_role_{p}_prompt", f"role_{p}_prompt"), height=150,
        )
    else:
        st.caption(t("allowed_persona"))
        uploaded = st.file_uploader(f"{t('upload')} {letter}", type=["md", "txt"], key=f"file_{p}", label_visibility="collapsed")
        load_persona_file(uploaded, p)


def render_human_persona(p):
    st.text_input(
        t("human_name"), key=f"w_role_{p}_name",
        on_change=update_state, args=(f"w_role_{p}_name", f"role_{p}_name"),
    )


def validate_setup():
    """Vrací text chyby, nebo None, pokud je nastavení v pořádku."""
    s = st.session_state
    mode = "ai_vs_ai" if is_simple else s.debate_mode
    has_c = (not is_simple) and mode in HAS_C_MODES

    # Účastník B existuje ve všech režimech (i jako člověk), proto vždy vyžadujeme jeho jméno.
    if not s.topic_input.strip() or not s.role_a_name.strip() or not s.role_b_name.strip():
        return t("err_validation")
    if has_c and not s.role_c_name.strip():
        return t("err_validation")

    if s.topic_input_type == "upload" and not s.topic_document_text:
        return t("err_no_docs")

    # Všichni použití AI poskytovatelé musí mít zadaný klíč.
    used = [s.provider_a, s.provider_mod]
    if mode not in HUMAN_B_MODES:
        used.append(s.provider_b)
    if has_c and mode not in HUMAN_C_MODES:
        used.append(s.provider_c)
    if any(p not in available_providers for p in used):
        return t("no_key_error")
    return None


def start_debate():
    s = st.session_state
    s.debate_active = True
    s.debate_finished = False
    s.current_round = 0
    s.turn_index = 0
    s.full_history = []
    s.current_topic = s.topic_input.strip()
    s.setup_step = 1

    # Vyčistit výsledky předchozí debaty, aby se nemíchaly s novou
    s.final_summary = ""
    s.model_mod_used = ""
    s.md_content = ""
    s.pdf_bytes = b""
    s.file_base_name = "debata"
    s.critique_md = ""
    s.critique_pdf = b""
    s.critique_base = ""
    s.show_critique_ui = False
    s.summary_md = ""
    s.summary_pdf = b""
    s.summary_base_name = ""

    # Reset času pro měření délky debaty
    s.debate_start_time = time.time()

    st.switch_page("app_pages/arena.py")


# --------------------------------------------------------------------------
# Dostupní poskytovatelé
# --------------------------------------------------------------------------
available_providers = []
if st.session_state.gemini_key.strip():
    available_providers.append("Gemini")
if st.session_state.mistral_key.strip():
    available_providers.append("Mistral")
if st.session_state.nim_key.strip():
    available_providers.append("NVIDIA NIM")
select_options = available_providers if available_providers else [NO_KEY_LABEL]

st.title(t("nav_setup"))

# --------------------------------------------------------------------------
# Krok 1 – režim a pravidla
# --------------------------------------------------------------------------
if st.session_state.setup_step == 1 and not is_simple:
    st.subheader(t("setup_step1"))

    if "w_mode" not in st.session_state:
        st.session_state.w_mode = st.session_state.debate_mode
    if "w_preset" not in st.session_state:
        st.session_state.w_preset = st.session_state.preset_select
    if "w_length" not in st.session_state:
        st.session_state.w_length = st.session_state.response_length
    if "w_goal" not in st.session_state:
        st.session_state.w_goal = st.session_state.debate_goal
    if "w_rules" not in st.session_state:
        st.session_state.w_rules = list(st.session_state.debate_rules)

    st.radio(t("mode_label"), options=MODE_KEYS, format_func=lambda k: t(f"mode_{k}"), key="w_mode", on_change=update_state, args=("w_mode", "debate_mode"))
    st.divider()
    st.selectbox(t("preset_label"), options=PRESET_KEYS, format_func=lambda k: t(f"preset_{k}"), key="w_preset", on_change=apply_preset_callback, help=t("preset_help"))

    adv_label = "⚙️ Pokročilá nastavení pravidel" if st.session_state.lang == "cs" else "⚙️ Advanced rule settings"
    with st.expander(adv_label):
        st.selectbox(t("response_length_label"), options=LENGTH_KEYS, format_func=lambda k: t(f"length_{k}"), key="w_length", on_change=update_state, args=("w_length", "response_length"))
        st.radio(t("debate_goal_label"), options=GOAL_KEYS, format_func=lambda k: t(f"goal_{k}"), key="w_goal", on_change=update_state, args=("w_goal", "debate_goal"))
        st.multiselect(t("rules_label"), options=RULE_KEYS, format_func=lambda k: t(f"rule_{k}"), key="w_rules", on_change=update_state, args=("w_rules", "debate_rules"))

# --------------------------------------------------------------------------
# Krok 2 – osobnosti a moderátor
# --------------------------------------------------------------------------
elif st.session_state.setup_step == 2:
    st.subheader(t("setup_step2"))
    mode = st.session_state.debate_mode

    for p in ("a", "b", "c", "mod"):
        if st.session_state[f"provider_{p}"] not in select_options:
            st.session_state[f"provider_{p}"] = select_options[0]

    for p in ("a", "b", "c"):
        if f"w_role_{p}_name" not in st.session_state:
            st.session_state[f"w_role_{p}_name"] = st.session_state[f"role_{p}_name"]
        if f"w_provider_{p}" not in st.session_state:
            st.session_state[f"w_provider_{p}"] = st.session_state[f"provider_{p}"]
        if f"w_temperament_{p}" not in st.session_state:
            st.session_state[f"w_temperament_{p}"] = st.session_state.get(f"temperament_{p}", "undefined")
        if f"w_expertise_{p}" not in st.session_state:
            st.session_state[f"w_expertise_{p}"] = st.session_state.get(f"expertise_{p}", "undefined")
        if f"w_role_{p}_prompt" not in st.session_state:
            st.session_state[f"w_role_{p}_prompt"] = st.session_state[f"role_{p}_prompt"]
        if f"w_input_type_{p}" not in st.session_state:
            # Při návratu do kroku 2 se instrukce ukážou v textovém poli (jdou upravit),
            # proto stav držíme v souladu s tím, co je vidět.
            st.session_state[f"w_input_type_{p}"] = "manual"
            st.session_state[f"input_type_{p}"] = "manual"

    if "w_provider_mod" not in st.session_state:
        st.session_state.w_provider_mod = st.session_state.provider_mod
    if "w_max_rounds" not in st.session_state:
        st.session_state.w_max_rounds = st.session_state.max_rounds
    if "w_memory_limit" not in st.session_state:
        st.session_state.w_memory_limit = st.session_state.memory_limit

    # OSOBNOST A – otevřená (vždy AI)
    with st.expander(f"**{t('persona_a')} (AI)**", expanded=True):
        render_ai_persona("a")

    # OSOBNOST B – sbalená
    if mode in HUMAN_B_MODES:
        with st.expander(f"**{t('persona_b')} ({t('human')})**", expanded=False):
            render_human_persona("b")
    else:
        with st.expander(f"**{t('persona_b')} (AI)**", expanded=False):
            render_ai_persona("b")

    # OSOBNOST C – pouze v pokročilém režimu s třemi účastníky
    if mode in HAS_C_MODES and not is_simple:
        if mode in HUMAN_C_MODES:
            with st.expander(f"**{t('persona_c')} ({t('human')})**", expanded=False):
                render_human_persona("c")
        else:
            with st.expander(f"**{t('persona_c')} (AI)**", expanded=False):
                render_ai_persona("c")

    st.divider()

    # Moderátor
    with st.expander(f"**{t('moderator')}**", expanded=False):
        st.selectbox(f"{t('provider_select')}:", select_options, key="w_provider_mod", on_change=update_state, args=("w_provider_mod", "provider_mod"))

        if not is_simple:
            st.slider(f"{t('rounds')} {t('max_7')}", min_value=2, max_value=7, key="w_max_rounds", on_change=update_state, args=("w_max_rounds", "max_rounds"))
            st.slider(t("memory_limit_label"), min_value=2, max_value=10, key="w_memory_limit", on_change=update_state, args=("w_memory_limit", "memory_limit"))

# --------------------------------------------------------------------------
# Krok 3 – téma
# --------------------------------------------------------------------------
elif st.session_state.setup_step == 3:
    st.subheader(t("setup_step3"))

    if "w_topic_input_type" not in st.session_state:
        st.session_state.w_topic_input_type = st.session_state.topic_input_type
    if "w_topic_input" not in st.session_state:
        st.session_state.w_topic_input = st.session_state.topic_input

    st.radio(t("topic_type"), options=["manual", "upload"], format_func=lambda x: t(x), key="w_topic_input_type", on_change=update_state, args=("w_topic_input_type", "topic_input_type"))

    if st.session_state.w_topic_input_type == "manual":
        st.text_area(t("topic_text"), key="w_topic_input", on_change=update_state, args=("w_topic_input", "topic_input"), height=250)
        st.session_state.topic_document_text = ""
        st.session_state.uploaded_files_hash = ""
    else:
        st.text_input(t("topic_file"), key="w_topic_input", on_change=update_state, args=("w_topic_input", "topic_input"))
        st.caption(t("allowed_topic"))
        topic_files = st.file_uploader(t("upload_topic"), type=["md", "txt"], accept_multiple_files=True, label_visibility="collapsed")

        if topic_files:
            # Otisk podle názvu i obsahu – změna souboru se stejným názvem se tak také pozná.
            sig = hashlib.sha1()
            for f in topic_files:
                sig.update(f.name.encode("utf-8"))
                sig.update(f.getvalue())
            files_hash = sig.hexdigest()

            if st.session_state.uploaded_files_hash != files_hash or not st.session_state.topic_document_text:
                full_text = ""
                for f in topic_files:
                    f.seek(0)
                    full_text += f"--- Document: {f.name} ---\n" + extract_text_from_file(f) + "\n\n"

                if len(full_text) > MAX_TOPIC_CHARS:
                    st.warning(t("err_topic_too_long", len=len(full_text), max=MAX_TOPIC_CHARS))
                    full_text = full_text[:MAX_TOPIC_CHARS] + "\n\n[... Zbývající text byl zkrácen ...]"

                st.session_state.topic_document_text = full_text
                st.session_state.uploaded_files_hash = files_hash

            if st.session_state.topic_document_text:
                st.success(t("ok_docs_loaded", len=len(topic_files), len_full=len(st.session_state.topic_document_text)))
        else:
            # Soubory byly odebrány – nesmí zůstat "neviditelné" podklady z minula.
            st.session_state.topic_document_text = ""
            st.session_state.uploaded_files_hash = ""

# --------------------------------------------------------------------------
# Navigace
# --------------------------------------------------------------------------
st.divider()
col1, col2 = st.columns([1, 1])
with col1:
    if st.session_state.setup_step > 1 and not (is_simple and st.session_state.setup_step == 2):
        st.button(t("back"), use_container_width=True, on_click=go_back)
with col2:
    if st.session_state.setup_step < 3:
        st.button(t("next"), type="primary", use_container_width=True, on_click=go_next)
    else:
        if st.button(t("start"), type="primary", use_container_width=True):
            error = validate_setup()
            if error:
                st.error(error)
            else:
                start_debate()
