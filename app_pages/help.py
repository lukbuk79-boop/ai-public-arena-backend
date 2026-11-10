import streamlit as st
from utils.config import t

st.title(t("h_title"))

# --- HLAVNÍ PŘEDSTAVENÍ ---
if st.session_state.lang == "cs":
    st.markdown("""
    ### Proč používat AI Public Arénu? (3 hlavní výhody)
    1. **Odstraňuje jednostranný pohled jedné AI:** Klasický chat Vám řekne jen jeden názor. Aréna postaví proti sobě různé agenty s odlišnými osobnostmi, což odhalí slabiny v argumentech mnohem lépe.
    2. **Objektivní rozhodčí a nezávislá kritika:** Po skončení debaty nastupuje nezávislá AI (rozhodčí), která vynese jasný verdikt. V pokročilém režimu si navíc můžete nechat vytvořit hloubkovou kritiku a přehledný souhrn.
    3. **Hluboká analýza a flexibilita:** Díky automatickému střídání replik a možnosti nahrát podkladové dokumenty jde o precizní nástroj pro analýzu složitých témat. Můžete také využít režim, kde se do debaty zapojíte Vy jako člověk.
    """)
else:
    st.markdown("""
    ### Why use AI Public Arena? (3 Main Benefits)
    1. **Removes single-AI bias:** A classic chat gives you only one perspective. The Arena pits different agents with distinct personas against each other, exposing weaknesses in arguments much better.
    2. **Objective Judge & Independent Critique:** After the debate ends, an independent AI (judge) steps in to deliver a clear verdict. In advanced mode, you can also generate an in-depth critique and a structured summary.
    3. **Deep analysis and flexibility:** Thanks to automatic turn-taking and the ability to upload supporting documents, it's a precise tool for analyzing complex topics. You can also join the debate yourself as a human.
    """)

st.divider()

# --- JEDNODUCHÁ VS POKROČILÁ DISKUZE ---
if st.session_state.lang == "cs":
    st.markdown("""
    ## 🚀 Dva režimy debaty
    Hned na úvodní stránce si můžete vybrat, jak náročnou debatu chcete:
    *   **Jednoduchá diskuze (AI vs AI):** Rychlý start. Zvolíte jen jména, poskytovatele a téma. Debata proběhne, rozhodčí vynese verdikt a soubory se uloží. (Není zde kritika ani souhrn).
    *   **Pokročilá diskuze:** Plná kontrola. Můžete nastavit pravidla, cíle, temperamenty, zapojit člověka, a po debatě si nechat vygenerovat **nezávislou kritiku** a **souhrn**.
    """)
else:
    st.markdown("""
    ## 🚀 Two debate modes
    Right on the home page, you can choose how complex the debate should be:
    *   **Simple Debate (AI vs AI):** Quick start. Just choose names, providers, and the topic. The debate runs, the judge gives a verdict, and files are saved. (No critique or summary).
    *   **Advanced Debate:** Full control. You can set rules, goals, temperaments, involve a human, and after the debate, generate an **independent critique** and a **summary**.
    """)

st.divider()

# --- JAK ZAČÍT A API KLÍČE ---
if st.session_state.lang == "cs":
    st.markdown("""
    ## 🔑 Jak začít a API klíče
    K provozu aplikace **bohatě stačí jeden API klíč**. Nemusíte zakládat účty u všech poskytovatelů.
    *   **Nejjednodušší volba je Google Gemini.** Pokud máte účet Google (Gmail), získáte klíč během 30 vteřin zdarma.
    *   **Důležité upozornění:** Z bezpečnostních důvodů se Vaše klíče **nikam neukládají**. Jsou pouze v dočasné paměti stránky. Jakmile zavřete kartu nebo obnovíte stránku, klíče zmizí a musíte je zadat znovu. Pro smazání klíčů kdykoliv během používání slouží tlačítko "Vymazat klíče z paměti".
    """)
else:
    st.markdown("""
    ## 🔑 How to start & API Keys
    **One API key is more than enough** to run the app. You don't need to create accounts with all providers.
    *   **The easiest choice is Google Gemini.** If you have a Google account (Gmail), you can get a free key in 30 seconds.
    *   **Important notice:** For security reasons, your keys are **not saved anywhere**. They are only kept in temporary page memory. As soon as you close the tab or refresh the page, the keys disappear, and you must enter them again. You can use the "Clear keys from memory" button at any time.
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

# --- NASTAVENÍ DEBATY ---
if st.session_state.lang == "cs":
    st.markdown("""
    ## ⚙️ Jak funguje nastavení Arény?
    Nastavení je rozděleno do **3 přehledných kroků**:
    *   **Krok 1: Režim a pravidla (jen pokročilá).** Vyberete, kdo bude debatovat (AI vs AI, AI vs člověk atd.). Můžete zvolit **Preset** (Akademická, Agresivní, Hledání konsenzu...), který automaticky nastaví vhodný temperament a pravidla. Cíl debaty určuje, zda má rozhodčí vybrat vítěze, najít shodu, nebo popsat neshodu.
    *   **Krok 2: Osobnosti.** Zde nastavíte jména. U AI osobností můžete změnit **Temperament** a **Expertízu**. Můžete je nechat náhodně vygenerovat tlačítkem 🎲, nebo zvolit "Nedefinováno" (pokud chcete, aby se AI chovala striktně podle instrukcí). Maximální počet kol debaty je **7**.
    *   **Krok 3: Téma a spuštění.** Zadejte téma nebo nahrajte podklady. Pokud hrajete v režimu s člověkem, aplikace se při Vašem tahu zastaví a dole na Vás bude čekat textové pole pro Váš argument.
    """)
else:
    st.markdown("""
    ## ⚙️ How does the Arena setup work?
    The setup is divided into **3 clear steps**:
    *   **Step 1: Mode & Rules (advanced only).** Choose who will debate (AI vs AI, AI vs Human, etc.). You can select a **Preset** (Academic, Aggressive, Consensus seeking...), which will automatically set the appropriate temperament and rules. The Debate Goal determines whether the judge should pick a winner, find common ground, or just highlight disagreements.
    *   **Step 2: Personas.** Set the names here. For AI personas, you can change their **Temperament** and **Expertise**. You can randomly generate them with the 🎲 button, or choose "Undefined" (if you want the AI to strictly follow the instructions). The maximum number of debate rounds is **7**.
    *   **Step 3: Topic & Start.** Enter the topic or upload materials. If you are playing in a mode with a human, the app will pause on your turn and a text input field will appear at the bottom for your argument.
    """)

st.divider()

# --- PRÁCE SE SOUBORY ---
if st.session_state.lang == "cs":
    st.markdown("""
    ## 📄 Práce se soubory (Markdown a TXT)
    Pro zajištění nejlepší kvality a spolehlivosti **podporujeme pouze formáty `.md` (Markdown) a `.txt`**. Formát PDF jsme odstranili, protože u naskenovaných dokumentů často selhává čtení textu.
    *   **Instrukce pro osobnosti:** Limit je **10 000 znaků** (cca 5 stran). Kratší instrukce pomáhají AI lépe se držet role.
    *   **Téma / Podklady pro diskuzi:** Limit je **45 000 znaků** (cca 25 stran). Pokud nahrajete delší soubor, aplikace vás upozorní a automaticky text zkrátí.
    """)
else:
    st.markdown("""
    ## 📄 Working with files (Markdown & TXT)
    To ensure the best quality and reliability, **we only support `.md` (Markdown) and `.txt` formats**. We have removed PDF because text extraction often fails with scanned documents.
    *   **Persona instructions:** Limit is **10,000 characters** (approx. 5 pages). Shorter instructions help the AI stay in character better.
    *   **Topic / Debate materials:** Limit is **45,000 characters** (approx. 25 pages). If you upload a longer file, the app will warn you and automatically truncate the text.
    """)

st.divider()

# --- NEZÁVISLÁ KRITIKA A SOUHRN ---
with st.expander(t("exp_crit")):
    if st.session_state.lang == "cs":
        st.markdown("""
        V **Pokročilé diskuzi** můžete po skončení debaty nechat diskuzi a verdikt rozhodčího posoudit další AI:
        
        *   **Přímé API:** Pokud máte v aplikaci klíč, kritika a souhrn budou vygenerovány přímo serverem a uloženy na Cloudflare R2 do složky `summary` nebo `critique`.
        *   **Externí chat:** Pokud chcete použít lepší model (např. placený ChatGPT Plus nebo Claude), stáhněte si PDF s diskuzí, otevřete odkaz na chat a vložte připravený prompt. Poté zkopírujte výsledek zpět do aplikace a uložte ho.
        """)
    else:
        st.markdown("""
        In **Advanced Debate**, after the debate ends, you can have the debate and the judge's verdict evaluated by another AI:
        
        *   **Direct API:** If you have a key in the app, the critique and summary will be generated directly by the server and saved to Cloudflare R2 in the `summary` or `critique` folder.
        *   **External chat:** If you want to use a better model (e.g., paid ChatGPT Plus or Claude), download the debate PDF, open the chat link, and paste the prepared prompt. Then copy the result back into the app and save it.
        """)
