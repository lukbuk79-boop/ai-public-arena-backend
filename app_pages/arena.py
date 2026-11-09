import streamlit as st
import streamlit.components.v1 as components
import time
import base64
from datetime import datetime
from google import genai
from google.genai import types
from openai import OpenAI

# Importy z našich nových modulů
from utils.config import t
from utils.state import init_state
from utils.ai_providers import (
    get_available_gemini_models, 
    get_available_mistral_models, 
    get_delay_for_provider, 
    enhance_role_prompt, 
    build_judge_prompt, 
    generate_filename_from_topic, 
    call_ai, 
    call_critique_api,
    NVIDIA_PREFERRED
)
from utils.pdf_export import generate_pdf
from utils.storage import get_next_counter, get_r2_client, save_critique_result, reset_critique_state

init_state()

# --- VYKRESLOVACÍ FUNKCE ---
def render_downloads():
    base_name = st.session_state.get("file_base_name", "debata")
    md_b64 = base64.b64encode(st.session_state.md_content.encode('utf-8')).decode('utf-8')
    pdf_b64 = base64.b64encode(st.session_state.pdf_bytes).decode('utf-8') if st.session_state.pdf_bytes else ""
    html_code = f"""
    <div style="display: flex; gap: 10px;">
        <a href="data:application/octet-stream;base64,{md_b64}" download="{base_name}.md" style="flex: 1; text-align: center; padding: 10px; background-color: #f0f2f6; color: #31333f; text-decoration: none; border-radius: 5px; border: 1px solid #d6d6d6; font-size: 16px;">{t('dl_md')}</a>
        <a href="data:application/pdf;base64,{pdf_b64}" download="{base_name}.pdf" style="flex: 1; text-align: center; padding: 10px; background-color: #ff4b4b; color: white; text-decoration: none; border-radius: 5px; font-size: 16px;">{t('dl_pdf')}</a>
    </div>
    """
    components.html(html_code, height=60)

def render_critique_ui(available_providers_list):
    if not st.session_state.md_content: return
    st.divider(); st.subheader(t("critique_title")); st.caption(t("critique_caption"))
    
    def start_critique(): st.session_state.show_critique_ui = True
    
    if not st.session_state.show_critique_ui and not st.session_state.critique_md:
        st.button(t("start_critique"), type="primary", use_container_width=True, on_click=start_critique)
    if not (st.session_state.show_critique_ui or st.session_state.critique_md): return
    
    components.html("<script>setTimeout(function() { var main = window.parent.document.querySelector('.main'); if (main) { main.scrollTop = main.scrollHeight; } }, 50);</script>", height=0, width=0)
    tab_api, tab_ext = st.tabs([t("tab_api"), t("tab_ext")])

    with tab_api:
        if not available_providers_list:
            st.warning(t("no_key_error").replace("debate", "critique").replace("diskuze", "kritiky"))
        else:
            options = [f"{p} (API)" for p in available_providers_list]
            selected = st.selectbox(t("provider_select"), options, key="critique_api_provider")
            provider = selected.replace(" (API)", "")
            if st.button(f"{t('critique_gen')} {provider}", type="primary"):
                keys = {"gemini": st.session_state.gemini_key.strip(), "nim": st.session_state.nim_key.strip(), "mistral": st.session_state.mistral_key.strip()}
                with st.spinner(f"{provider}..."):
                    try:
                        critique_text, model_used = call_critique_api("Jsi nezávislý recenzent.", f"Zhodnoť diskuzi: {st.session_state.md_content}", provider, keys)
                        ok, err, base_name = save_critique_result(critique_text, model_used)
                        if ok: st.success(f"✅ Uloženo na R2.")
                        else: st.warning(f"⚠️ Uloženo lokálně, R2 selhalo: {err}")
                    except Exception as e: st.error(f"Error: {e}")

    with tab_ext:
        st.info(t("ext_info"))
        pdf_b64 = base64.b64encode(st.session_state.pdf_bytes).decode('utf-8') if st.session_state.pdf_bytes else ""
        st.markdown(f'<a href="data:application/pdf;base64,{pdf_b64}" download="{st.session_state.file_base_name}.pdf" style="display:block; text-align:center; padding:10px; background:#ff4b4b; color:white; text-decoration:none; border-radius:6px; font-weight:600;">{t("ext_step1")}</a>', unsafe_allow_html=True)
        st.markdown(f"**{t('ext_step2')}**")
        chats = {"ChatGPT": "https://chatgpt.com/", "Claude": "https://claude.ai/new", "Gemini": "https://gemini.google.com/app"}
        cols = st.columns(4)
        for i, (name, url) in enumerate(chats.items()): cols[i % 4].markdown(f'<a href="{url}" target="_blank" style="display:block; text-align:center; padding:8px; background:#e2e8f0; color:#2d3748; text-decoration:none; border-radius:5px; margin-bottom:5px; font-size:14px;">{name}</a>', unsafe_allow_html=True)
        st.markdown(f"**{t('ext_step3')}**")
        prompt_for_ext = f"Přečti přiložené PDF s diskuzí na téma: '{st.session_state.current_topic}'. Proveď nezávislou kritiku."
        st.code(prompt_for_ext, language=None)
        st.markdown(f"**{t('ext_step4')}**")
        pasted = st.text_area("Result:", height=150, key="critique_pasted_ext")
        if st.button(t("save_critique")):
            if pasted.strip():
                save_critique_result(pasted, "External AI (manual)")
                st.success("Uloženo.")

    if st.session_state.critique_md:
        st.divider(); st.subheader(t("ready_critique"))
        md_b64 = base64.b64encode(st.session_state.critique_md.encode('utf-8')).decode('utf-8')
        pdf_b64 = base64.b64encode(st.session_state.critique_pdf).decode('utf-8')
        st.markdown(f'<div style="display:flex; gap:10px; margin:10px 0;"><a href="data:application/octet-stream;base64,{md_b64}" download="{st.session_state.critique_base}.md" style="flex:1; text-align:center; padding:10px; background:#f0f2f6; color:#31333f; text-decoration:none; border-radius:5px; border:1px solid #d6d6d6;">{t("dl_critique_md")}</a><a href="data:application/pdf;base64,{pdf_b64}" download="{st.session_state.critique_base}.pdf" style="flex:1; text-align:center; padding:10px; background:#ff4b4b; color:white; text-decoration:none; border-radius:5px;">{t("dl_critique_pdf")}</a></div>', unsafe_allow_html=True)
        with st.expander(t("preview_critique"), expanded=False): st.markdown(st.session_state.critique_md)

# --- HLAVNÍ LOGIKA ARÉNY ---
st.title(t("debate_title"))

if not st.session_state.debate_active:
    st.warning("Žádná aktivní debata. Přejděte do Nastavení a spusťte novou diskuzi.")
    if st.button("Jít do nastavení"):
        st.switch_page("app_pages/setup.py")
    st.stop()

# Rekonstrukce dostupných providerů
available_providers = []
if st.session_state.gemini_key.strip(): available_providers.append("Gemini")
if st.session_state.mistral_key.strip(): available_providers.append("Mistral")
if st.session_state.nim_key.strip(): available_providers.append("NVIDIA NIM")

# Inicializace klientů
gemini_client = genai.Client(api_key=st.session_state.gemini_key.strip(), http_options=types.HttpOptions(timeout=180000)) if "Gemini" in available_providers else None
mistral_client = OpenAI(api_key=st.session_state.mistral_key.strip(), base_url="https://api.mistral.ai/v1", timeout=180.0) if "Mistral" in available_providers else None
nim_client = OpenAI(api_key=st.session_state.nim_key.strip(), base_url="https://integrate.api.nvidia.com/v1", timeout=180.0) if "NVIDIA NIM" in available_providers else None

# Model listy
gemini_models = get_available_gemini_models(gemini_client) if gemini_client else []
mistral_models = get_available_mistral_models(mistral_client) if mistral_client else []
nvidia_models = NVIDIA_PREFERRED if nim_client else []

# Obalení pro snadné volání (předáváme klienty a modely jako parametry)
ai_kwargs = {
    "gemini_client": gemini_client, 
    "mistral_client": mistral_client, 
    "nim_client": nim_client,
    "gemini_models": gemini_models, 
    "mistral_models": mistral_models
}

# Pokud debata ještě není vygenerovaná (přišli jsme ze setupu), spustíme ji
if not st.session_state.full_history:
    lang = st.session_state.lang
    enhanced_prompt_a = enhance_role_prompt(st.session_state.role_a_prompt, st.session_state.temperament_a, st.session_state.expertise_a, st.session_state.response_length, st.session_state.debate_rules, lang)
    enhanced_prompt_b = enhance_role_prompt(st.session_state.role_b_prompt, st.session_state.temperament_b, st.session_state.expertise_b, st.session_state.response_length, st.session_state.debate_rules, lang)

    st.markdown(f"### 📌 Téma: *{st.session_state.current_topic}*")
    chat_container = st.container()
    progress_bar = st.progress(0)
    memory_limit = st.session_state.memory_limit

    # 1. Shrnutí dokumentů
    if st.session_state.topic_input_type == "upload" and st.session_state.topic_document_text:
        with st.spinner("Analýza dokumentů..."):
            summary_prompt = "Jsi expert na analýzu dokumentů. Vytvoř strukturovaný souhrn."
            for p in [p for p in ["Gemini", "Mistral", "NVIDIA NIM"] if p in available_providers]:
                try:
                    st.session_state.topic_summary, _ = call_ai(summary_prompt, st.session_state.topic_document_text, p, **ai_kwargs)
                    break
                except: pass
        st.info(st.session_state.topic_summary)

    debate_context_intro = f"Topic: '{st.session_state.current_topic}'.\n\n"
    if st.session_state.topic_summary: debate_context_intro += f"Summary:\n{st.session_state.topic_summary}\n\n"

    # 2. První argument (A)
    with chat_container.chat_message("user", avatar="🔵"):
        st.markdown(f"**{st.session_state.role_a_name}:**")
        with st.spinner("Startuji..."):
            resp_a, mod_a = call_ai(enhanced_prompt_a, debate_context_intro + "Zahaj diskuzi.", st.session_state.provider_a, **ai_kwargs)
        st.markdown(resp_a); st.caption(f"🤖 `{mod_a}`")
    st.session_state.full_history.append((st.session_state.role_a_name, resp_a, mod_a))

    # 3. Smyčka
    for r in range(st.session_state.max_rounds):
        progress_bar.progress((r + 1) / st.session_state.max_rounds)
        time.sleep(get_delay_for_provider(st.session_state.provider_b))
        
        context_b = debate_context_intro + "Context:\n" + "\n".join([f"{s}: {txt}" for s, txt, m in st.session_state.full_history[-memory_limit:]]) + f"\nNyní jsi na řadě ty ({st.session_state.role_b_name})."
        with chat_container.chat_message("assistant", avatar="🔴"):
            st.markdown(f"**{st.session_state.role_b_name}:**")
            with st.spinner("Reaguji..."):
                resp_b, mod_b = call_ai(enhanced_prompt_b, context_b, st.session_state.provider_b, **ai_kwargs)
            st.markdown(resp_b); st.caption(f"🤖 `{mod_b}`")
        st.session_state.full_history.append((st.session_state.role_b_name, resp_b, mod_b))

        if r < st.session_state.max_rounds - 1:
            time.sleep(get_delay_for_provider(st.session_state.provider_a))
            context_a = debate_context_intro + "Context:\n" + "\n".join([f"{s}: {txt}" for s, txt, m in st.session_state.full_history[-memory_limit:]]) + f"\nNyní jsi na řadě ty ({st.session_state.role_a_name})."
            with chat_container.chat_message("user", avatar="🔵"):
                st.markdown(f"**{st.session_state.role_a_name}:**")
                with st.spinner("Reaguji..."):
                    resp_a, mod_a = call_ai(enhanced_prompt_a, context_a, st.session_state.provider_a, **ai_kwargs)
                st.markdown(resp_a); st.caption(f"🤖 `{mod_a}`")
            st.session_state.full_history.append((st.session_state.role_a_name, resp_a, mod_a))

    # 4. Rozhodčí
    progress_bar.progress(1.0)
    time.sleep(get_delay_for_provider(st.session_state.provider_mod))
    summary_context = f"TÉMA: '{st.session_state.current_topic}'\n\n" + "\n".join([f"{s}: {txt}" for s, txt, m in st.session_state.full_history])
    base_judge_prompt = "Jsi přísný a nestranný rozhodčí. Zhodnoť průběh debaty."
    judge_prompt = build_judge_prompt(base_judge_prompt, st.session_state.debate_goal, lang)

    with st.spinner("Rozhodčí zvažuje argumenty..."):
        try:
            final_sum, mod_mod = call_ai(judge_prompt, summary_context, st.session_state.provider_mod, **ai_kwargs)
        except Exception as e:
            final_sum = f"Chyba rozhodčího: {e}"; mod_mod = "API Error"

    st.session_state.final_summary = final_sum
    st.session_state.model_mod_used = mod_mod
    
    with chat_container.chat_message("assistant", avatar="⚖️"):
        st.markdown(f"**{t('judge')}:**"); st.markdown(final_sum); st.caption(f"🤖 `{mod_mod}`")

    # 5. Uložení na R2
    with st.spinner("Ukládám..."):
        md_history = "".join([f"### {s}\n{txt}\n\n<small>Model: {m}</small>\n\n---\n\n" for s, txt, m in st.session_state.full_history])
        st.session_state.md_content = f"# Debate: {st.session_state.current_topic}\n\n" + md_history + f"### {t('judge')}\n{final_sum}"
        st.session_state.pdf_bytes = generate_pdf(st.session_state.md_content)
        
        try: counter = get_next_counter()
        except: counter = "00000"
            
        filename_base = generate_filename_from_topic(st.session_state.current_topic, call_ai, available_providers, **ai_kwargs)
        full_base = f"{counter}_{filename_base}"
        st.session_state.file_base_name = full_base

        try:
            s3 = get_r2_client(); bucket = st.secrets["R2_BUCKET_NAME"]
            s3.put_object(Bucket=bucket, Key=f"markdown/{full_base}.md", Body=st.session_state.md_content.encode("utf-8"))
            s3.put_object(Bucket=bucket, Key=f"pdf/{full_base}.pdf", Body=st.session_state.pdf_bytes)
            st.success("✅ Uloženo na R2.")
        except Exception as e: st.error(f"R2 Error: {e}")

    st.rerun() # Pro jistotu obnovení

else:
    # Pokud už je historie vygenerovaná (např. při refreshi), jen vykreslíme
    st.markdown(f"### 📌 Téma: *{st.session_state.current_topic}*")
    if st.session_state.topic_summary:
        st.info(st.session_state.topic_summary)
    for i, (sender, text, model) in enumerate(st.session_state.full_history):
        with st.chat_message("user" if i % 2 == 0 else "assistant", avatar="🔵" if i % 2 == 0 else "🔴"):
            st.markdown(f"**{sender}:**\n\n{text}"); st.caption(f"🤖 `{model}`")
    with st.chat_message("assistant", avatar="⚖️"):
        st.markdown(f"**{t('judge')}:**\n\n{st.session_state.final_summary}"); st.caption(f"🤖 `{st.session_state.model_mod_used}`")

st.divider()
render_downloads()
render_critique_ui(available_providers)
st.divider()

if st.button(t("new_debate"), use_container_width=True):
    st.session_state.debate_active = False
    st.session_state.full_history = []
    reset_critique_state()
    st.switch_page("app_pages/setup.py")
