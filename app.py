import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import random
from utils.state import init_state
from utils.config import t, PRESET_KEYS, PRESETS, MODE_KEYS, TEMPERAMENT_KEYS, EXPERTISE_KEYS, LENGTH_KEYS, GOAL_KEYS, RULE_KEYS
from utils.pdf_export import extract_text_from_file

st.set_page_config(page_title="AI Public Aréna", layout="wide")
init_state()

def save_keys_to_storage():
    g = json.dumps(st.session_state.saved_gemini)
    n = json.dumps(st.session_state.saved_nim)
    m = json.dumps(st.session_state.saved_mistral)
    js = f"""
    <script>
        try {{
            localStorage.setItem('arena_gemini', {g});
            localStorage.setItem('arena_nim', {n});
            localStorage.setItem('arena_mistral', {m});
        }} catch(e) {{ console.error("LocalStorage blocked", e); }}
    </script>
    """
    components.html(js, height=0)

def apply_preset_callback():
    preset = st.session_state.preset_select
    if preset == "custom" or preset not in PRESETS: return
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

def randomize_persona(prefix):
    st.session_state[f"temperament_{prefix}"] = random.choice(TEMPERAMENT_KEYS)
    st.session_state[f"expertise_{prefix}"] = random.choice(EXPERTISE_KEYS)

def save_settings():
    st.session_state.is_configured = True
    st.toast("✅ Nastavení uloženo. Nyní můžete spustit diskuzi.")

with st.sidebar:
    def get_image_base64(path):
        try:
            with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
        except Exception: return ""

    cz_b64 = get_image_base64("cz.png")
    gb_b64 = get_image_base64("gb.png")
    
    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 10px; margin-bottom: 20px;">
            <img src="data:image/png;base64,{cz_b64}" width="30" style="border-radius: 3px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
            <img src="data:image/png;base64,{gb_b64}" width="30" style="border-radius: 3px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
        </div>
    """, unsafe_allow_html=True)

    lang_choice = st.radio(t("lang_name"), ["Čeština", "English"], index=0 if st.session_state.lang == "cs" else 1, horizontal=True)
    st.session_state.lang = "cs" if "Čeština" in lang_choice else "en"

    st.divider()
    st.header(t("api_keys"))
    
    temp_g = st.text_input(f"🔑 Gemini {t('api_keys')}:", type="password", value=st.session_state.saved_gemini, placeholder="AIzaSy...")
    st.session_state.saved_gemini = temp_g 
    
    temp_m = st.text_input(f"🔑 Mistral {t('api_keys')}:", type="password", value=st.session_state.saved_mistral, placeholder="...")
    st.session_state.saved_mistral = temp_m
    
    temp_n = st.text_input(f"🔑 NVIDIA {t('api_keys')}:", type="password", value=st.session_state.saved_nim, placeholder="nvapi-...")
    st.session_state.saved_nim = temp_n

    st.session_state.gemini_key = st.session_state.saved_gemini
    st.session_state.mistral_key = st.session_state.saved_mistral
    st.session_state.nim_key = st.session_state.saved_nim

    if st.button(t("save_keys"), use_container_width=True):
        save_keys_to_storage()
        st.success(t("save_keys_success"))

    st.divider()
    st.header(t("nav"))
    app_mode = st.radio(t("nav"), [t("nav_arena"), t("nav_help")], index=0)
    st.divider()

    if app_mode == t("nav_arena"):
        st.header(t("settings"))
        
        st.radio(t("mode_label"), options=MODE_KEYS, format_func=lambda k: t(f"mode_{k}"), key="debate_mode")
        st.selectbox(t("preset_label"), options=PRESET_KEYS, format_func=lambda k: t(f"preset_{k}"), key="preset_select", on_change=apply_preset_callback, help=t("preset_help"))
        st.selectbox(t("response_length_label"), options=LENGTH_KEYS, format_func=lambda k: t(f"length_{k}"), key="response_length")
        st.radio(t("debate_goal_label"), options=GOAL_KEYS, format_func=lambda k: t(f"goal_{k}"), key="debate_goal")
        st.multiselect(t("rules_label"), options=RULE_KEYS, format_func=lambda k: t(f"rule_{k}"), key="debate_rules")
        
        st.slider(t("rounds"), min_value=2, max_value=30, key="max_rounds")
        
        available_providers = []
        if st.session_state.gemini_key.strip(): available_providers.append("Gemini")
        if st.session_state.mistral_key.strip(): available_providers.append("Mistral")
        if st.session_state.nim_key.strip(): available_providers.append("NVIDIA NIM")
        select_options = available_providers if available_providers else ["(Zadejte klíč)"]

        if st.session_state.provider_a not in select_options: st.session_state.provider_a = select_options[0]
        if st.session_state.provider_b not in select_options: st.session_state.provider_b = select_options[0]
        if st.session_state.provider_c not in select_options: st.session_state.provider_c = select_options[0]
        if st.session_state.provider_mod not in select_options: st.session_state.provider_mod = select_options[0]

        st.subheader(t("persona_a") + " (AI)")
        st.text_input(f"{t('name')} A", key="role_a_name")
        st.selectbox(f"{t('provider_select')} A:", select_options, key="provider_a")
        col_t, col_e = st.columns(2)
        with col_t: st.selectbox(t("temperament_label"), options=TEMPERAMENT_KEYS, format_func=lambda k: t(f"temperament_{k}"), key="temperament_a")
        with col_e: st.selectbox(t("expertise_label"), options=EXPERTISE_KEYS, format_func=lambda k: t(f"expertise_{k}"), key="expertise_a")
        st.button(t("random_button"), key="random_a", on_click=randomize_persona, args=("a",), use_container_width=True)
        st.radio(f"{t('input_type')} A:", options=["manual", "upload"], format_func=lambda x: t(x), key="input_type_a")
        if st.session_state.input_type_a == "manual": 
            st.text_area(f"{t('instructions')} A", key="role_a_prompt")
        else:
            file_a = st.file_uploader(f"{t('upload')} A", type=["pdf", "md", "txt"], key="file_a")
            if file_a: st.session_state.role_a_prompt = extract_text_from_file(file_a)

        mode = st.session_state.debate_mode
        if mode in ["ai_vs_human", "ai_vs_human_vs_human"]:
            st.subheader(t("persona_b") + " (Člověk)")
            st.text_input(t("human_name"), key="role_b_name")
        else:
            st.subheader(t("persona_b") + " (AI)")
            st.text_input(f"{t('name')} B", key="role_b_name")
            st.selectbox(f"{t('provider_select')} B:", select_options, key="provider_b")
            col_t2, col_e2 = st.columns(2)
            with col_t2: st.selectbox(t("temperament_label"), options=TEMPERAMENT_KEYS, format_func=lambda k: t(f"temperament_{k}"), key="temperament_b")
            with col_e2: st.selectbox(t("expertise_label"), options=EXPERTISE_KEYS, format_func=lambda k: t(f"expertise_{k}"), key="expertise_b")
            st.button(t("random_button"), key="random_b", on_click=randomize_persona, args=("b",), use_container_width=True)
            st.radio(f"{t('input_type')} B:", options=["manual", "upload"], format_func=lambda x: t(x), key="input_type_b")
            if st.session_state.input_type_b == "manual": 
                st.text_area(f"{t('instructions')} B", key="role_b_prompt")
            else:
                file_b = st.file_uploader(f"{t('upload')} B", type=["pdf", "md", "txt"], key="file_b")
                if file_b: st.session_state.role_b_prompt = extract_text_from_file(file_b)

        if mode in ["ai_vs_ai_vs_ai", "ai_vs_ai_vs_human", "ai_vs_human_vs_human"]:
            if mode in ["ai_vs_ai_vs_human", "ai_vs_human_vs_human"]:
                st.subheader(t("persona_c") + " (Člověk)")
                st.text_input(t("human_name"), key="role_c_name")
            else:
                st.subheader(t("persona_c") + " (AI)")
                st.text_input(f"{t('name')} C", key="role_c_name")
                st.selectbox(f"{t('provider_select')} C:", select_options, key="provider_c")
                col_t3, col_e3 = st.columns(2)
                with col_t3: st.selectbox(t("temperament_label"), options=TEMPERAMENT_KEYS, format_func=lambda k: t(f"temperament_{k}"), key="temperament_c")
                with col_e3: st.selectbox(t("expertise_label"), options=EXPERTISE_KEYS, format_func=lambda k: t(f"expertise_{k}"), key="expertise_c")
                st.button(t("random_button"), key="random_c", on_click=randomize_persona, args=("c",), use_container_width=True)
                st.radio(f"{t('input_type')} C:", options=["manual", "upload"], format_func=lambda x: t(x), key="input_type_c")
                if st.session_state.input_type_c == "manual": 
                    st.text_area(f"{t('instructions')} C", key="role_c_prompt")
                else:
                    file_c = st.file_uploader(f"{t('upload')} C", type=["pdf", "md", "txt"], key="file_c")
                    if file_c: st.session_state.role_c_prompt = extract_text_from_file(file_c)

        st.subheader(t("moderator"))
        st.selectbox(f"{t('provider_select')}:", select_options, key="provider_mod")
        
        with st.expander(t("advanced_settings")):
            st.slider(t("memory_limit_label"), min_value=2, max_value=30, key="memory_limit")

        # NOVÉ TLAČÍTKO PRO ULOŽENÍ NASTAVENÍ
        st.divider()
        st.button("💾 Uložit nastavení", type="primary", use_container_width=True, on_click=save_settings)

    st.divider()
    st.caption("© 2026 Lukáš Buchvalek")

pg = st.navigation([
    st.Page("app_pages/arena.py", title=t("nav_arena"), icon=":material/swords:"),
    st.Page("app_pages/help.py", title=t("nav_help"), icon=":material/help:"),
])

pg.run()
