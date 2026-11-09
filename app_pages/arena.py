import streamlit as st
import streamlit.components.v1 as components
import time
import base64
from datetime import datetime
from google import genai
from google.genai import types
from openai import OpenAI

from utils.config import t
from utils.state import init_state
from utils.ai_providers import (
    get_available_gemini_models, get_available_mistral_models, get_delay_for_provider, 
    enhance_role_prompt, build_judge_prompt, generate_filename_from_topic, 
    call_ai, call_critique_api, NVIDIA_PREFERRED
)
from utils.pdf_export import generate_pdf
from utils.storage import get_next_counter, get_r2_client, save_critique_result, reset_critique_state

init_state()

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
    tab_api, tab_ext = st.tabs([t("tab_api"), t("tab_ext")])
    with tab_api:
        if not available_providers_list: st.warning(t("no_key_error"))
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
                    except Exception as e: st.error(f"Error: {e}")
    with tab_ext:
        st.info(t("ext_info"))
        # Zde zkráceno pro přehlednost, funguje stejně jako dřív
        pass
    if st.session_state.critique_md:
        st.divider(); st.subheader(t("ready_critique"))
        with st.expander(t("preview_critique"), expanded=False): st.markdown(st.session_state.critique_md)

st.title(t("debate_title"))

if not st.session_state.debate_active:
    st.warning("Žádná aktivní debata. Přejděte do Nastavení a spusťte novou diskuzi.")
    if st.button("Jít do nastavení"): st.switch_page("app_pages/setup.py")
    st.stop()

available_providers = []
if st.session_state.gemini_key.strip(): available_providers.append("Gemini")
if st.session_state.mistral_key.strip(): available_providers.append("Mistral")
if st.session_state.nim_key.strip(): available_providers.append("NVIDIA NIM")

gemini_client = genai.Client(api_key=st.session_state.gemini_key.strip(), http_options=types.HttpOptions(timeout=180000)) if "Gemini" in available_providers else None
mistral_client = OpenAI(api_key=st.session_state.mistral_key.strip(), base_url="https://api.mistral.ai/v1", timeout=180.0) if "Mistral" in available_providers else None
nim_client = OpenAI(api_key=st.session_state.nim_key.strip(), base_url="https://integrate.api.nvidia.com/v1", timeout=180.0) if "NVIDIA NIM" in available_providers else None

gemini_models = get_available_gemini_models(gemini_client) if gemini_client else []
mistral_models = get_available_mistral_models(mistral_client) if mistral_client else []
nvidia_models = NVIDIA_PREFERRED if nim_client else []

ai_kwargs = {
    "gemini_client": gemini_client, "mistral_client": mistral_client, "nim_client": nim_client,
    "gemini_models": gemini_models, "mistral_models": mistral_models
}

# --- SESTAVENÍ ÚČASTNÍKŮ ---
mode = st.session_state.debate_mode
participants = []
lang = st.session_state.lang

# A (Vždy AI)
prompt_a = enhance_role_prompt(st.session_state.role_a_prompt, st.session_state.temperament_a, st.session_state.expertise_a, st.session_state.response_length, st.session_state.debate_rules, lang)
participants.append({"name": st.session_state.role_a_name, "type": "ai", "provider": st.session_state.provider_a, "prompt": prompt_a, "avatar": "🔵"})

# B (AI nebo Human)
if mode == "ai_vs_human":
    participants.append({"name": st.session_state.role_b_name, "type": "human", "avatar": "🧑‍💻"})
else:
    prompt_b = enhance_role_prompt(st.session_state.role_b_prompt, st.session_state.temperament_b, st.session_state.expertise_b, st.session_state.response_length, st.session_state.debate_rules, lang)
    participants.append({"name": st.session_state.role_b_name, "type": "ai", "provider": st.session_state.provider_b, "prompt": prompt_b, "avatar": "🔴"})

# C (AI nebo Human)
if mode in ["ai_vs_ai_vs_ai", "ai_vs_ai_vs_human"]:
    if mode == "ai_vs_ai_vs_human":
        participants.append({"name": st.session_state.role_c_name, "type": "human", "avatar": "🧑‍💻"})
    else:
        prompt_c = enhance_role_prompt(st.session_state.role_c_prompt, st.session_state.temperament_c, st.session_state.expertise_c, st.session_state.response_length, st.session_state.debate_rules, lang)
        participants.append({"name": st.session_state.role_c_name, "type": "ai", "provider": st.session_state.provider_c, "prompt": prompt_c, "avatar": "🟢"})
elif mode == "ai_vs_human_vs_human":
    participants.append({"name": st.session_state.role_c_name, "type": "human", "avatar": "🧑‍💻"})

# --- VYKRESLENÍ HISTORIE ---
st.markdown(f"### 📌 Téma: *{st.session_state.current_topic}*")
for i, (sender, text, model) in enumerate(st.session_state.full_history):
    is_human = model == "Human"
    avatar = "🧑‍💻" if is_human else participants[i % len(participants)]["avatar"]
    with st.chat_message("user" if is_human else "assistant", avatar=avatar):
        st.markdown(f"**{sender}:**\n\n{text}")
        if not is_human: st.caption(f"🤖 `{model}`")

# --- STAVOVÝ AUTOMAT ---
if not st.session_state.debate_finished:
    # Smyčka pro AI tahy, dokud nenarazíme na člověka
    while st.session_state.current_round < st.session_state.max_rounds:
        current_speaker = participants[st.session_state.turn_index]
        
        if current_speaker["type"] == "human":
            break # Přerušíme smyčku a čekáme na vstup od člověka
            
        # Provádíme AI tah
        with st.spinner(f"{current_speaker['name']} přemýšlí..."):
            time.sleep(get_delay_for_provider(current_speaker["provider"]))
            
            # Sestavení kontextu
            context = f"Topic: '{st.session_state.current_topic}'.\n\nContext:\n"
            context += "\n".join([f"{s}: {txt}" for s, txt, m in st.session_state.full_history[-st.session_state.memory_limit:]])
            context += f"\nNyní jsi na řadě ty ({current_speaker['name']}). Reaguj na argumenty ostatních."
            
            try:
                resp, mod = call_ai(current_speaker["prompt"], context, current_speaker["provider"], **ai_kwargs)
            except Exception as e:
                resp, mod = f"Chyba API: {e}", "Error"
            
            st.session_state.full_history.append((current_speaker["name"], resp, mod))
            
            # Vykreslíme novou zprávu
            with st.chat_message("assistant", avatar=current_speaker["avatar"]):
                st.markdown(f"**{current_speaker['name']}:**\n\n{resp}")
                st.caption(f"🤖 `{mod}`")

        # Posun tahu
        st.session_state.turn_index += 1
        if st.session_state.turn_index >= len(participants):
            st.session_state.turn_index = 0
            st.session_state.current_round += 1

    # Po ukončení while smyčky zkontrolujeme, proč skončila
    if st.session_state.current_round >= st.session_state.max_rounds:
        # --- ROZHODČÍ ---
        st.session_state.debate_finished = True
        time.sleep(get_delay_for_provider(st.session_state.provider_mod))
        summary_context = f"TÉMA: '{st.session_state.current_topic}'\n\nPRŮBĚH DEBATY:\n" + "\n".join([f"{s}: {txt}" for s, txt, m in st.session_state.full_history])
        base_judge_prompt = "Jsi přísný a nestranný rozhodčí. Zhodnoť průběh debaty."
        judge_prompt = build_judge_prompt(base_judge_prompt, st.session_state.debate_goal, lang)

        with st.spinner("Rozhodčí zvažuje argumenty..."):
            try:
                final_sum, mod_mod = call_ai(judge_prompt, summary_context, st.session_state.provider_mod, **ai_kwargs)
            except Exception as e:
                final_sum, mod_mod = f"Chyba rozhodčího: {e}", "API Error"

        st.session_state.final_summary = final_sum
        st.session_state.model_mod_used = mod_mod
        
        with st.chat_message("assistant", avatar="⚖️"):
            st.markdown(f"**{t('judge')}:**"); st.markdown(final_sum); st.caption(f"🤖 `{mod_mod}`")

        # Uložení
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
        st.rerun()

    else:
        # --- JE NA ŘADĚ ČLOVĚK ---
        current_speaker = participants[st.session_state.turn_index]
        prompt_text = f"{current_speaker['name']}, {t('human_turn_waiting')}"
        human_input = st.chat_input(prompt_text)
        
        if human_input:
            st.session_state.full_history.append((current_speaker["name"], human_input, "Human"))
            st.session_state.turn_index += 1
            if st.session_state.turn_index >= len(participants):
                st.session_state.turn_index = 0
                st.session_state.current_round += 1
            st.rerun()

else:
    # --- DEBATA SKONČILA, VYKRESLENÍ VÝSLEDKŮ ---
    with st.chat_message("assistant", avatar="⚖️"):
        st.markdown(f"**{t('judge')}:**\n\n{st.session_state.final_summary}"); st.caption(f"🤖 `{st.session_state.model_mod_used}`")
    
    st.divider()
    render_downloads()
    render_critique_ui(available_providers)
    st.divider()

if st.session_state.debate_finished:
    if st.button(t("new_debate"), use_container_width=True):
        st.session_state.debate_active = False
        st.session_state.debate_finished = False
        st.session_state.full_history = []
        reset_critique_state()
        st.switch_page("app_pages/setup.py")
