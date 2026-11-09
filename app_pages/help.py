import streamlit as st
from utils.config import t

st.title(t("h_title"))
st.markdown(f"## {t('h_sub')}")
st.markdown(f"1. {t('h_p1')}")
st.markdown(f"2. {t('h_p2')}")
st.markdown(f"3. {t('h_p3')}")
st.divider()
st.markdown(t("h_start"))
st.markdown(t("h_start_gemini"))
st.markdown(t("h_start_other"))
st.markdown(t("h_start_save"))

with st.expander(t("exp_gemini")):
    st.markdown("""
    **How to get the key:**
    1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
    2. Sign in with your Google account.
    3. Click on **Create API key**.
    4. Copy the generated key (starts with `AIza...`) and paste it into the sidebar.
    """)
with st.expander(t("exp_mistral")):
    st.markdown("""
    **How to get the key:**
    1. Go to [Mistral Console](https://console.mistral.ai/).
    2. Register.
    3. Go to **API Keys** -> **Create new key**.
    """)
with st.expander(t("exp_nvidia")):
    st.markdown("""
    **How to get the key:**
    1. Go to [NVIDIA Build](https://build.nvidia.com/).
    2. Register.
    3. Click on your name in the top right -> **API Keys**.
    4. Generate a new key (starts with `nvapi-...`).
    """)
with st.expander(t("exp_crit")):
    st.markdown("""
    After the debate ends, you can have the debate and the judge's verdict evaluated by another AI:
    *   **Direct API:** If you have a key in the app, the critique will be generated directly by the server and saved to R2.
    *   **External chat:** If you want to use a better model, download the debate PDF, open the chat link, and paste the prepared prompt.
    """)
