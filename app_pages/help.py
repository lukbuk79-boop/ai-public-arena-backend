import streamlit as st
from utils.config import t

st.title(t("h_title"))

# --- HLAVNÍ PŘEDSTAVENÍ ---
if st.session_state.lang == "cs":
    st.markdown("""
    ### Proč používat AI Public Arénu? (3 hlavní výhody)
    1. **Odstraňuje jednostranný pohled jedné AI:** Klasický chat Vám řekne jen jeden názor. Aréna postaví proti sobě až tři různé agenty s odlišnými osobnostmi, což odhalí slabiny v argumentech mnohem lépe.
    2. **Objektivní rozhodčí:** Po skončení debaty nastupuje nezávislá AI (rozhodčí), která má za úkol nestranně zvážit argumenty všech stran a vynést jasný verdikt, konsenzus, nebo popsat neshodu.
    3. **Hluboká analýza a flexibilita:** Díky automatickému střídání replik, možnosti nahrát podkladové dokumenty (PDF) a unikátní možnosti **zapojit do debaty i Vás (jako člověka)**, jde o precizní nástroj pro analýzu složitých témat.
    """)
else:
    st.markdown("""
    ### Why use AI Public Arena? (3 Main Benefits)
    1. **Removes the single-AI bias:** A classic chat gives you only one perspective. The Arena pits up to three different agents with distinct personas against each other, exposing weaknesses in arguments much better.
    2. **Objective Judge:** After the debate ends, an independent AI (judge) steps in to impartially weigh the arguments of all sides and deliver a clear verdict, consensus, or highlight disagreements.
    3. **Deep analysis and flexibility:** Thanks to automatic turn-taking, the ability to upload supporting documents (PDF), and the unique option to **join the debate yourself (as a human)**, it's a precise tool for analyzing complex topics.
    """)

st.divider()

# --- JAK ZAČÍT A API KLÍČE ---
if st.session_state.lang == "cs":
    st.markdown("""
    ## 🚀 Jak začít
    K provozu aplikace **bohatě stačí jeden API klíč**. Nemusíte zakládat účty u všech poskytovatelů.
    *   **Nejjednodušší volba je Google Gemini.** Pokud máte účet Google (Gmail), máte pravděpodobně přístup i do Google AI Studia, kde klíč získáte během 30 vteřin zdarma.
    *   Ostatní klíče (Mistral, NVIDIA) jsou zde jako alternativa pro specifické modely nebo jako záloha, pokud by Vám došly limity.
    *   **Tip:** V postranním panelu můžete kliknout na tlačítko "Uložit klíče do prohlížeče". Vaše klíče se bezpečně uloží do paměti vašeho prohlížeče a při příští návštěvě se automaticky vyplní.
    """)
else:
    st.markdown("""
    ## 🚀 How to start
    **One API key is more than enough** to run the app. You don't need to create accounts with all providers.
    *   **The easiest choice is Google Gemini.** If you have a Google account (Gmail), you likely have access to Google AI Studio, where you can get a free key in 30 seconds.
    *   Other keys (Mistral, NVIDIA) are here as an alternative for specific models or as a backup if you run out of limits.
    *   **Tip:** In the sidebar, you can click "Save Keys to Browser". Your keys will be securely saved in your browser's memory and automatically filled in on your next visit.
    """)

# --- ROZBALOVACÍ MENU PRO ZÍSKÁNÍ KLÍČŮ ---
with st.expander(t("exp_gemini")):
    if st.session_state.lang == "cs":
        st.markdown("""
        **Jak získat klíč:**
        1. Jděte na [Google AI Studio](https://aistudio.google.com/app/api-keys).
        2. Přihlaste se svým Google účtem.
        3. Klikněte na **Create API key**.
        4. Zkopírujte vygenerovaný klíč (začíná na `AIza...`) a vložte ho do postranního panelu.

        **Limity (Free tier):** Zcela zdarma. ~15 requestů za minutu, denní limit 500 - 1500 requestů.
        """)
    else:
        st.markdown("""
        **How to get the key:**
        1. Go to [Google AI Studio](https://aistudio.google.com/app/api-keys).
        2. Sign in with your Google account.
        3. Click on **Create API key**.
        4. Copy the generated key (starts with `AIza...`) and paste it into the sidebar.

        **Limits (Free tier):** Completely free. ~15 requests per minute, daily limit 500 - 1500 requests.
        """)

with st.expander(t("exp_mistral")):
    if st.session_state.lang == "cs":
        st.markdown("""
        **Jak získat klíč:**
        1. Jděte na [Mistral Console](https://console.mistral.ai/).
        2. Zaregistrujte se.
        3. Jděte do **API Keys** -> **Create new key**.
        """)
    else:
        st.markdown("""
        **How to get the key:**
        1. Go to [Mistral Console](https://console.mistral.ai/).
        2. Register.
        3. Go to **API Keys** -> **Create new key**.
        """)

with st.expander(t("exp_nvidia")):
    if st.session_state.lang == "cs":
        st.markdown("""
        **Jak získat klíč:**
        1. Jděte na [NVIDIA Build](https://build.nvidia.com/).
        2. Zaregistrujte se.
        3. Klikněte na své jméno vpravo nahoře -> **API Keys**.
        4. Vygenerujte nový klíč (začíná na `nvapi-...`).

        **Limity (Free tier):** Štědré limity (~40 requestů za minutu), skvělé pro dlouhé texty.
        """)
    else:
        st.markdown("""
        **How to get the key:**
        1. Go to [NVIDIA Build](https://build.nvidia.com/).
        2. Register.
        3. Click on your name in the top right -> **API Keys**.
        4. Generate a new key (starts with `nvapi-...`).

        **Limits (Free tier):** Generous limits (~40 requests per minute), great for long texts.
        """)

st.divider()

# --- NOVÉ SEKCE PRO NASTAVENÍ A REŽIMY ---
if st.session_state.lang == "cs":
    st.markdown("""
    ## ⚙️ Jak funguje nastavení Arény?
    Nastavení je rozděleno do **3 přehledných kroků**:
    *   **Krok 1: Režim a pravidla.** Zde si vyberete, kdo bude debatovat (AI vs AI, AI vs člověk atd.). Můžete zvolit některý z **Presetů** (Akademická, Agresivní, Hledání konsenzu...), které za vás automaticky nastaví vhodný temperament a pravidla. Cíl debaty určuje, zda má rozhodčí vybrat vítěze, najít shodu, nebo jen popsat neshodu.
    *   **Krok 2: Osobnosti.** Zde nastavíte jména. U AI osobností můžete změnit **Temperament** (např. agresivní, empatický) a **Expertízu** (laik, profesor...). Tlačítkem 🎲 je můžete nechat náhodně vygenerovat.
    *   **Krok 3: Téma a spuštění.** Zadejte téma nebo nahrajte podklady. Pokud hrajete v režimu s člověkem, aplikace se při Vašem tahu zastaví a dole na Vás bude čekat textové pole pro Váš argument.
    """)
else:
    st.markdown("""
    ## ⚙️ How does the Arena setup work?
    The setup is divided into **3 clear steps**:
    *   **Step 1: Mode & Rules.** Choose who will debate (AI vs AI, AI vs Human, etc.). You can select one of the **Presets** (Academic, Aggressive, Consensus seeking...), which will automatically set the appropriate temperament and rules for you. The Debate Goal determines whether the judge should pick a winner, find common ground, or just highlight disagreements.
    *   **Step 2: Personas.** Set the names here. For AI personas, you can change their **Temperament** (e.g., aggressive, empathetic) and **Expertise** (layman, professor...). The 🎲 button will randomly generate them.
    *   **Step 3: Topic & Start.** Enter the topic or upload materials. If you are playing in a mode with a human, the app will pause on your turn and a text input field will appear at the bottom for your argument.
    """)

st.divider()

# --- NEZÁVISLÁ KRITIKA ---
with st.expander(t("exp_crit")):
    if st.session_state.lang == "cs":
        st.markdown("""
        Po skončení debaty můžete nechat diskuzi a verdikt rozhodčího ohodnotit další AI:
        
        *   **Přímé API:** Pokud máte v aplikaci klíč, kritika bude vygenerována přímo serverem a uložena na R2.
        *   **Externí chat:** Pokud chcete použít lepší model (např. placený ChatGPT Plus nebo Claude), stáhněte si PDF s diskuzí, otevřete odkaz na chat a vložte připravený prompt. Poté zkopírujte výsledek zpět do aplikace.
        """)
    else:
        st.markdown("""
        After the debate ends, you can have the debate and the judge's verdict evaluated by another AI:
        
        *   **Direct API:** If you have a key in the app, the critique will be generated directly by the server and saved to R2.
        *   **External chat:** If you want to use a better model (e.g., paid ChatGPT Plus or Claude), download the debate PDF, open the chat link, and paste the prepared prompt. Then copy the result back into the app.
        """)
