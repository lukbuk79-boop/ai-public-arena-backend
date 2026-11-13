import streamlit as st
import streamlit.components.v1 as components
import base64
from utils.state import init_state
from utils.config import t

st.set_page_config(page_title="AI Public Aréna", layout="wide")
init_state()

if "saved_gemini" not in st.session_state: st.session_state.saved_gemini = ""
if "saved_mistral" not in st.session_state: st.session_state.saved_mistral = ""
if "saved_nim" not in st.session_state: st.session_state.saved_nim = ""

with st.sidebar:
    def get_image_base64(path):
        try:
            with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
        except Exception: return ""

    cz_b64 = get_image_base64("cz.png")
    gb_b64 = get_image_base64("gb.png")
    
    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 10px; margin-bottom: 20px;">
            <img src="data:image/png;base64,{gb_b64}" width="30" style="border-radius: 3px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
            <img src="data:image/png;base64,{cz_b64}" width="30" style="border-radius: 3px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
        </div>
    """, unsafe_allow_html=True)

    lang_choice = st.radio(t("lang_name"), ["English", "Čeština"], index=0 if st.session_state.lang == "en" else 1, horizontal=True)
    st.session_state.lang = "en" if "English" in lang_choice else "cs"

    st.divider()
    st.header(t("api_keys"))
    
    temp_g = st.text_input(f"🔑 Gemini {t('api_keys')}:", type="password", value=st.session_state.saved_gemini, placeholder="AIzaSy...", autocomplete="off")
    st.session_state.saved_gemini = temp_g 
    
    temp_m = st.text_input(f"🔑 Mistral {t('api_keys')}:", type="password", value=st.session_state.saved_mistral, placeholder="...", autocomplete="off")
    st.session_state.saved_mistral = temp_m
    
    temp_n = st.text_input(f"🔑 NVIDIA {t('api_keys')}:", type="password", value=st.session_state.saved_nim, placeholder="nvapi-...", autocomplete="off")
    st.session_state.saved_nim = temp_n

    st.session_state.gemini_key = st.session_state.saved_gemini
    st.session_state.mistral_key = st.session_state.saved_mistral
    st.session_state.nim_key = st.session_state.saved_nim

    # --- NOVÝ BLOK PRO VLASTNÍ MODELY ---
    with st.expander("⚙️ Pokročilé: Vlastní modely"):
        st.caption("Zadejte přesný název modelu, který chcete preferovat. Pokud necháte prázdné, použije se výchozí seznam.")
        
        st.session_state.custom_gemini_model = st.text_input(
            "Vlastní model Gemini", 
            value=st.session_state.get("custom_gemini_model", ""), 
            placeholder="např. gemini-2.5-pro"
        )
        st.session_state.custom_mistral_model = st.text_input(
            "Vlastní model Mistral", 
            value=st.session_state.get("custom_mistral_model", ""), 
            placeholder="např. mistral-large-latest"
        )
        st.session_state.custom_nvidia_model = st.text_input(
            "Vlastní model NVIDIA NIM", 
            value=st.session_state.get("custom_nvidia_model", ""), 
            placeholder="např. meta/llama-3.1-405b-instruct"
        )
    # ------------------------------------

    st.caption(t("keys_warning"))
    
    if st.button(t("clear_keys"), use_container_width=True):
        st.session_state.saved_gemini = ""
        st.session_state.saved_mistral = ""
        st.session_state.saved_nim = ""
        st.session_state.gemini_key = ""
        st.session_state.mistral_key = ""
        st.session_state.nim_key = ""
        st.rerun()

    st.divider()
    st.caption("© 2026 Lukáš Buchvald")

pg = st.navigation([
    st.Page("app_pages/arena.py", title=t("nav_arena"), icon=":material/swords:"),
    st.Page("app_pages/setup.py", title=t("nav_setup"), icon=":material/settings:"),
    st.Page("app_pages/help.py", title=t("nav_help"), icon=":material/help:"),
])

pg.run()
