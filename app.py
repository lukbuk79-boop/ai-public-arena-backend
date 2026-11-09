import streamlit as st
import streamlit.components.v1 as components
import base64
import json
from utils.state import init_state
from utils.config import t

st.set_page_config(page_title="AI Public Aréna", layout="wide")
init_state()

def auto_save_keys():
    g = json.dumps(st.session_state.gemini_key)
    n = json.dumps(st.session_state.nim_key)
    m = json.dumps(st.session_state.mistral_key)
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
    
    # Přidán on_change=auto_save_keys pro okamžité uložení
    st.text_input(f"🔑 Gemini {t('api_keys')}:", type="password", key="gemini_key", placeholder="AIzaSy...", on_change=auto_save_keys)
    st.text_input(f"🔑 Mistral {t('api_keys')}:", type="password", key="mistral_key", placeholder="...", on_change=auto_save_keys)
    st.text_input(f"🔑 NVIDIA {t('api_keys')}:", type="password", key="nim_key", placeholder="nvapi-...", on_change=auto_save_keys)

    if st.button(t("save_keys"), use_container_width=True):
        auto_save_keys()
        st.success(t("save_keys_success"))

    st.divider()
    st.caption("© 2026 Lukáš Buchvalek")

pg = st.navigation([
    st.Page("app_pages/setup.py", title=t("nav_setup"), icon=":material/settings:"),
    st.Page("app_pages/arena.py", title=t("nav_arena"), icon=":material/swords:"),
    st.Page("app_pages/help.py", title=t("nav_help"), icon=":material/help:"),
])

pg.run()
