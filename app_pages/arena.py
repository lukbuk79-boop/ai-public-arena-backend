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
from utils.pdf_export import generate_pdf, extract_text_from_file
from utils.storage import get_next_counter, get_r2_client, save_critique_result, reset_critique_state

init_state()

if "input_type_a" not in st.session_state: st.session_state.input_type_a = "Ručně"
if "input_type_b" not in st.session_state: st.session_state.input_type_b = "Ručně"
if "input_type_c" not in st.session_state: st.session_state.input_type_c = "Ručně"
if "topic_input_type" not in st.session_state: st.session_state.topic_input_type = "Ručně"
if "debate_type" not in st.session_state: st.session_state.debate_type = "advanced"

if "summary_md" not in st.session_state: st.session_state.summary_md = ""
if "summary_pdf" not in st.session_state: st.session_state.summary_pdf = b""
if "summary_base_name" not in st.session_state: st.session_state.summary_base_name = ""

def get_display_name(name, temp_key, exp_key):
    if not name: return ""
    t_str = t(f"temperament_{temp_key}")
    e_str = t(f"expertise_{exp_key}")
    return f"{name} ({t_str}, {e_str})"

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
    
    if not st.session_state.get("show_critique_ui") and not st.session_state.critique_md:
        st.button(t("start_critique"), type="primary", use_container_width=True, on_click=start_critique)
    if not (st.session_state.get("show_critique_ui") or st.session_state.critique_md): return
    
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
        st.markdown(f'<a href="data:application/pdf;base64,{pdf_b64}" download="{st.session_state.file_base_name}.pdf" style="display:block; text-align:center; padding:10px; background:#ff4b4b; color:white; text-decoration:none; border-radius:6px; font-weight:600; margin-bottom: 15px;">{t("ext_step1")}</a>', unsafe_allow_html=True)

        st.markdown(f"**{t('ext_step2')}**")
        chats = {
            "ChatGPT": "https://chatgpt.com/", "Claude": "https://claude.ai/new",
            "Gemini": "https://gemini.google.com/app", "Perplexity": "https://www.perplexity.ai/",
            "DeepSeek": "https://chat.deepseek.com/", "Copilot": "https://copilot.microsoft.com/",
            "Le Chat (Mistral)": "https://chat.mistral.ai/chat"
        }
        cols = st.columns(4)
        for i, (name, url) in enumerate(chats.items()):
            cols[i % 4].markdown(f'<a href="{url}" target="_blank" style="display:block; text-align:center; padding:8px; background:#e2e8f0; color:#2d3748; text-decoration:none; border-radius:5px; margin-bottom:5px; font-size:14px;">{name}</a>', unsafe_allow_html=True)

        st.markdown(f"**{t('ext_step3')}**")
        if st.session_state.lang == "cs":
            prompt_for_ext = f"Přečti přiložené PDF s diskuzí na téma: '{st.session_state.current_topic}'. Proveď nezávislou kritiku: zhodnoť relevanci, kvalitu argumentace obou stran a recenzuj verdikt rozhodčího. Navrhni vyváženější verdikt, pokud s ním nesouhlasíš."
        else:
            prompt_for_ext = f"Read the attached PDF with the debate on the topic: '{st.session_state.current_topic}'. Provide an independent critique: evaluate the relevance, the quality of arguments on both sides, and review the judge's verdict. Propose a more balanced verdict if you disagree with it."
        st.code(prompt_for_ext, language=None)

        st.markdown(f"**{t('ext_step4')}**")
        pasted = st.text_area("Result:", height=150, key="critique_pasted_ext", label_visibility="collapsed", placeholder="Paste the critique result here...")
        if st.button(t("save_critique"), key="btn_save_ext"):
            if pasted.strip():
                ok, err, base_name = save_critique_result(pasted, "External AI (manual)")
                if ok: st.success(f"✅ Uloženo jako `{base_name}`.")
                else: st.warning(f"⚠️ Uloženo lokálně, R2 selhalo: {err}")
            else:
                st.error("Nejprve vložte text kritiky.")

    if st.session_state.critique_md:
        st.divider(); st.subheader(t("ready_critique"))
        md_b64 = base64.b64encode(st.session_state.critique_md.encode('utf-8')).decode('utf-8')
        pdf_b64 = base64.b64encode(st.session_state.critique_pdf).decode('utf-8')
        st.markdown(f'<div style="display:flex; gap:10px; margin:10px 0;"><a href="data:application/octet-stream;base64,{md_b64}" download="{st.session_state.critique_base}.md" style="flex:1; text-align:center; padding:10px; background:#f0f2f6; color:#31333f; text-decoration:none; border-radius:5px; border:1px solid #d6d6d6;">{t("dl_critique_md")}</a><a href="data:application/pdf;base64,{pdf_b64}" download="{st.session_state.critique_base}.pdf" style="flex:1; text-align:center; padding:10px; background:#ff4b4b; color:white; text-decoration:none; border-radius:5px;">{t("dl_critique_pdf")}</a></div>', unsafe_allow_html=True)
        with st.expander(t("preview_critique"), expanded=False): st.markdown(st.session_state.critique_md)


def save_summary_to_state_and_r2(summary_text, model_name="External AI"):
    st.session_state.summary_md = f"# Souhrn debaty: {st.session_state.current_topic}\n\n**Datum:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n{summary_text}\n\n<small>Použitý model: {model_name}</small>"
    st.session_state.summary_pdf = generate_pdf(st.session_state.summary_md)
    
    base_name = st.session_state.get("file_base_name", "debata")
    base = f"{base_name}_souhrn"
    st.session_state.summary_base_name = base
    
    try:
        s3 = get_r2_client()
        bucket = st.secrets["R2_BUCKET_NAME"]
        s3.put_object(Bucket=bucket, Key=f"summary/{base}.md", Body=st.session_state.summary_md.encode("utf-8"))
        s3.put_object(Bucket=bucket, Key=f"summary/{base}.pdf", Body=st.session_state.summary_pdf)
        return True, base
    except Exception as e:
        return False, str(e)

def render_summary_ui(available_providers_list):
    if not st.session_state.md_content: return
    
    st.divider()
    st.subheader("📝 Souhrn debaty")
    st.caption("Vytvořte stručný souhrn hlavních shod, neshod a závěru. Pokud je k dispozici nezávislá kritika, bude do souhrnu automaticky zahrnuta.")
    
    has_critique = bool(st.session_state.get("critique_md"))
    
    tab_api, tab_ext = st.tabs(["Přímé API (automatické)", "Externí AI chat (manuální)"])

    with tab_api:
        if not available_providers_list:
            st.warning("Pro generování souhrnu musíte mít v menu zadaný alespoň jeden API klíč.")
        else:
            selected = st.selectbox("Poskytovatel pro souhrn:", available_providers_list, key="summary_api_provider")
            
            if has_critique:
                st.info("ℹ️ Nezávislá kritika byla nalezena a bude do souhrnu zahrnuta.")
            else:
                st.info("ℹ️ Nezávislá kritika zatím není k dispozici. Souhrn bude vytvořen pouze z průběhu debaty.")

            if st.button(f"Generovat souhrn pomocí {selected}", type="primary"):
                with st.spinner("Vytvářím souhrn debaty..."):
                    sys_prompt = (
                        "Jsi odborník na analýzu a sumarizaci textu. Na základě průběhu debaty vytvoř "
                        "strukturovaný souhrn. Výstup by měl obsahovat tyto sekce:\n"
                        "### Hlavní shody\n"
                        "### Hlavní neshody\n"
                        "### Závěr\n"
                        "Buď stručný, ale výstižný. Zmiň klíčové argumenty diskutujících."
                    )
                    
                    context_text = "PRŮBĚH DEBATY:\n" + st.session_state.md_content
                    
                    if has_critique:
                        context_text += "\n\nNEZÁVISLÁ KRITIKA:\n" + st.session_state.critique_md
                        sys_prompt += " Zohledni také nezávislou kritiku a zapracuj její postřehy do závěru."

                    try:
                        ai_kwargs = {
                            "gemini_client": st.session_state.get("gemini_client"),
                            "mistral_client": st.session_state.get("mistral_client"),
                            "nim_client": st.session_state.get("nim_client"),
                            "gemini_models": st.session_state.get("gemini_models"),
                            "mistral_models": st.session_state.get("mistral_models")
                        }
                        
                        summary_text, model_used = call_ai(sys_prompt, context_text, selected, **ai_kwargs)
                        
                        ok, res = save_summary_to_state_and_r2(summary_text, model_used)
                        if ok:
                            st.success(f"✅ Souhrn vygenerován a uložen na R2 jako `{res}.md` a `{res}.pdf`.")
                        else:
                            st.warning(f"⚠️ Souhrn vygenerován, ale nepodařilo se nahrát na R2: {res}")
                            
                    except Exception as e:
                        st.error(f"Chyba při generování souhrnu: {e}")

    with tab_ext:
        st.info("Zkopírujte si průběh debaty, nechte ho shrnout externí AI (např. ChatGPT) a výsledek vložte sem. Souhrn se uloží na R2.")
        
        pdf_b64 = base64.b64encode(st.session_state.pdf_bytes).decode('utf-8') if st.session_state.pdf_bytes else ""
        st.markdown(f'<a href="data:application/pdf;base64,{pdf_b64}" download="{st.session_state.file_base_name}.pdf" style="display:block; text-align:center; padding:10px; background:#ff4b4b; color:white; text-decoration:none; border-radius:6px; font-weight:600; margin-bottom: 15px;">1. Stáhnout PDF s debatou</a>', unsafe_allow_html=True)

        st.markdown("**2. Otevřete váš oblíbený AI chat:**")
        chats = {
            "ChatGPT": "https://chatgpt.com/", "Claude": "https://claude.ai/new",
            "Gemini": "https://gemini.google.com/app", "Perplexity": "https://www.perplexity.ai/",
            "DeepSeek": "https://chat.deepseek.com/", "Copilot": "https://copilot.microsoft.com/",
            "Le Chat (Mistral)": "https://chat.mistral.ai/chat"
        }
        cols = st.columns(4)
        for i, (name, url) in enumerate(chats.items()):
            cols[i % 4].markdown(f'<a href="{url}" target="_blank" style="display:block; text-align:center; padding:8px; background:#e2e8f0; color:#2d3748; text-decoration:none; border-radius:5px; margin-bottom:5px; font-size:14px;">{name}</a>', unsafe_allow_html=True)

        st.markdown("**3. Použijte tento prompt (vložte ho i s PDF):**")
        prompt_for_ext = f"Přečti přiložené PDF s diskuzí na téma: '{st.session_state.current_topic}'. Vytvoř strukturovaný souhrn s těmito sekcemi: Hlavní shody, Hlavní neshody, Závěr. Buď stručný a výstižný."
        if has_critique:
            prompt_for_ext += " Zohledni také nezávislou kritiku, která je součástí PDF, a zapracuj její postřehy do závěru."
        st.code(prompt_for_ext, language=None)

        st.markdown("**4. Vložte výsledný souhrn sem:**")
        pasted_summary = st.text_area("Výsledek ze externí AI:", height=150, key="summary_pasted_ext", label_visibility="collapsed", placeholder="Sem vložte text souhrnu...")
        
        if st.button("Uložit externí souhrn na R2", key="btn_save_ext_summary", type="primary"):
            if pasted_summary.strip():
                ok, res = save_summary_to_state_and_r2(pasted_summary, "External AI (manual)")
                if ok: 
                    st.success(f"✅ Externí souhrn uložen jako `{res}.md` a `{res}.pdf`.")
                    st.rerun()
                else: 
                    st.warning(f"⚠️ Uloženo lokálně, R2 selhalo: {res}")
            else:
                st.error("Nejprve vložte text souhrnu.")

    if st.session_state.get("summary_md"):
        st.markdown("---")
        st.subheader("✅ Hotový souhrn")
        with st.expander("Náhled souhrnu", expanded=True):
            st.markdown(st.session_state.summary_md)
        
        md_b64 = base64.b64encode(st.session_state.summary_md.encode('utf-8')).decode('utf-8')
        pdf_b64 = base64.b64encode(st.session_state.summary_pdf).decode('utf-8')
        base = st.session_state.summary_base_name
        
        st.markdown(f'<div style="display:flex; gap:10px; margin:10px 0;"><a href="data:application/octet-stream;base64,{md_b64}" download="{base}.md" style="flex:1; text-align:center; padding:10px; background:#f0f2f6; color:#31333f; text-decoration:none; border-radius:5px; border:1px solid #d6d6d6;">📥 Stáhnout souhrn (.md)</a><a href="data:application/pdf;base64,{pdf_b64}" download="{base}.pdf" style="flex:1; text-align:center; padding:10px; background:#ff4b4b; color:white; text-decoration:none; border-radius:5px;">📄 Stáhnout souhrn (.pdf)</a></div>', unsafe_allow_html=True)


# HLAVNÍ TITULEK
st.title(t("debate_title"))

# --- ÚVODNÍ STRÁNKA S VOLBOU ---
if not st.session_state.debate_active:
    if st.session_state.lang == "cs":
        st.markdown("""
        <div style="background-color: #e0f2fe; padding: 20px; border-radius: 10px; border-left: 5px solid #0284c7; margin-bottom: 20px;">
            <h4 style="margin-top: 0; color: #0369a1;">💡 Tip: K provozu arény bohatě stačí jeden API klíč.</h4>
            <p style="margin-bottom: 0; font-size: 16px; color: #0c4a6e;">
                Pokud žádný nemáte, nejjednodušší je <a href="https://aistudio.google.com/app/api-keys" target="_blank" style="font-weight: bold; color: #0284c7;">Google Gemini</a> 
                (stačí vám k tomu jen běžný Google účet).
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color: #e0f2fe; padding: 20px; border-radius: 10px; border-left: 5px solid #0284c7; margin-bottom: 20px;">
            <h4 style="margin-top: 0; color: #0369a1;">💡 Tip: One API key is enough to run the arena.</h4>
            <p style="margin-bottom: 0; font-size: 16px; color: #0c4a6e;">
                If you don't have one, the easiest is <a href="https://aistudio.google.com/app/api-keys" target="_blank" style="font-weight: bold; color: #0284c7;">Google Gemini</a> 
                (all you need is a standard Google account).
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    st.caption(t("debate_caption"))
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Jednoduchá diskuze (AI vs AI)", type="primary", use_container_width=True):
            st.session_state.debate_type = "simple"
            st.switch_page("app_pages/setup.py")
    with col2:
        if st.button("⚙️ Pokročilá diskuze", use_container_width=True):
            st.session_state.debate_type = "advanced"
            st.switch_page("app_pages/setup.py")
            
    st.stop()

# --- POKUD DEBATA BĚŽÍ, POKRAČUJE ZDE ---
is_simple = st.session_state.get("debate_type", "advanced") == "simple"
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

st.session_state.gemini_client = gemini_client
st.session_state.mistral_client = mistral_client
st.session_state.nim_client = nim_client
st.session_state.gemini_models = gemini_models
st.session_state.mistral_models = mistral_models

ai_kwargs = {
    "gemini_client": gemini_client, "mistral_client": mistral_client, "nim_client": nim_client,
    "gemini_models": gemini_models, "mistral_models": mistral_models
}

mode = "ai_vs_ai" if is_simple else st.session_state.debate_mode
participants = []
lang = st.session_state.lang

name_a_display = get_display_name(st.session_state.role_a_name, st.session_state.temperament_a, st.session_state.expertise_a)
prompt_a = enhance_role_prompt(st.session_state.role_a_prompt, st.session_state.temperament_a, st.session_state.expertise_a, st.session_state.response_length, st.session_state.debate_rules, lang)
participants.append({"name": name_a_display, "type": "ai", "provider": st.session_state.provider_a, "prompt": prompt_a, "avatar": "🔵"})

if mode in ["ai_vs_human", "ai_vs_human_vs_human"]:
    participants.append({"name": st.session_state.role_b_name, "type": "human", "avatar": "🧑‍💻"})
else:
    name_b_display = get_display_name(st.session_state.role_b_name, st.session_state.temperament_b, st.session_state.expertise_b)
    prompt_b = enhance_role_prompt(st.session_state.role_b_prompt, st.session_state.temperament_b, st.session_state.expertise_b, st.session_state.response_length, st.session_state.debate_rules, lang)
    participants.append({"name": name_b_display, "type": "ai", "provider": st.session_state.provider_b, "prompt": prompt_b, "avatar": "🔴"})

if mode in ["ai_vs_ai_vs_ai", "ai_vs_ai_vs_human", "ai_vs_human_vs_human"] and not is_simple:
    if mode in ["ai_vs_ai_vs_human", "ai_vs_human_vs_human"]:
        participants.append({"name": st.session_state.role_c_name, "type": "human", "avatar": "🧑‍💻"})
    else:
        name_c_display = get_display_name(st.session_state.role_c_name, st.session_state.temperament_c, st.session_state.expertise_c)
        prompt_c = enhance_role_prompt(st.session_state.role_c_prompt, st.session_state.temperament_c, st.session_state.expertise_c, st.session_state.response_length, st.session_state.debate_rules, lang)
        participants.append({"name": name_c_display, "type": "ai", "provider": st.session_state.provider_c, "prompt": prompt_c, "avatar": "🟢"})

st.markdown(f"### 📌 Téma: *{st.session_state.current_topic}*")

if st.session_state.get("topic_summary"):
    st.info(st.session_state.topic_summary)

for i, (sender, text, model) in enumerate(st.session_state.full_history):
    is_human = model == "Human"
    avatar = next((p["avatar"] for p in participants if p["name"] == sender), "🔵")
    with st.chat_message("user" if is_human else "assistant", avatar=avatar):
        st.markdown(f"**{sender}:**\n\n{text}")
        if not is_human: st.caption(f"🤖 `{model}`")

if not st.session_state.debate_finished:
    while st.session_state.current_round < st.session_state.max_rounds:
        current_speaker = participants[st.session_state.turn_index]
        
        if current_speaker["type"] == "human":
            break
            
        with st.spinner(f"{current_speaker['name']} přemýšlí..."):
            time.sleep(get_delay_for_provider(current_speaker["provider"]))
            
            context = f"Topic: '{st.session_state.current_topic}'.\n\nContext:\n"
            context += "\n".join([f"{s}: {txt}" for s, txt, m in st.session_state.full_history[-st.session_state.memory_limit:]])
            context += f"\nNyní jsi na řadě ty ({current_speaker['name']}). Reaguj na argumenty ostatních."
            
            try:
                resp, mod = call_ai(current_speaker["prompt"], context, current_speaker["provider"], **ai_kwargs)
            except Exception as e:
                resp, mod = f"Chyba API: {e}", "Error"
            
            st.session_state.full_history.append((current_speaker["name"], resp, mod))
            
            with st.chat_message("assistant", avatar=current_speaker["avatar"]):
                st.markdown(f"**{current_speaker['name']}:**\n\n{resp}")
                st.caption(f"🤖 `{mod}`")

        st.session_state.turn_index += 1
        if st.session_state.turn_index >= len(participants):
            st.session_state.turn_index = 0
            st.session_state.current_round += 1

    if st.session_state.current_round >= st.session_state.max_rounds:
        st.session_state.debate_finished = True
        time.sleep(get_delay_for_provider(st.session_state.provider_mod))
        
        summary_context = f"TÉMA: '{st.session_state.current_topic}'\n\nPRŮBĚH DEBATY:\n" + "\n".join([f"{s}: {txt}" for s, txt, m in st.session_state.full_history])
        base_judge_prompt = "Jsi přísný a nestranný rozhodčí. Zhodnoť průběh debaty."
        judge_prompt = build_judge_prompt(base_judge_prompt, st.session_state.debate_goal, lang)

        with st.spinner("Rozhodčí zvažuje argumenty..."):
            try:
                final_sum, mod_mod = call_ai(judge_prompt, summary_context, st.session_state.provider_mod, **ai_kwargs)
            except Exception as e:
                final_sum = f"Chyba rozhodčího: {e}"
                mod_mod = "API Error"

        st.session_state.final_summary = final_sum
        st.session_state.model_mod_used = mod_mod
        
        with st.chat_message("assistant", avatar="⚖️"):
            st.markdown(f"**{t('judge')}:**"); st.markdown(final_sum); st.caption(f"🤖 `{mod_mod}`")

        with st.spinner("Ukládám..."):
            md_history = "".join([f"### {s}\n{txt}\n\n<small>Model: {m}</small>\n\n---\n\n" for s, txt, m in st.session_state.full_history])
            st.session_state.md_content = f"# Debate: {st.session_state.current_topic}\n\n" + md_history + f"### {t('judge')}\n{final_sum}"
            st.session_state.pdf_bytes = generate_pdf(st.session_state.md_content)
            
            try: counter = get_next_counter()
            except: counter = "00000"
            
            st.session_state.file_counter = counter
                
            filename_base = generate_filename_from_topic(st.session_state.current_topic, call_ai, available_providers, **ai_kwargs)
            full_base = f"{counter}_{filename_base}"
            st.session_state.file_base_name = full_base

            try:
                s3 = get_r2_client(); bucket = st.secrets["R2_BUCKET_NAME"]
                
                # ROZLIŠENÍ CESTY PRO R2
                if is_simple:
                    md_path = f"simply_discussion/md/{full_base}.md"
                    pdf_path = f"simply_discussion/pdf/{full_base}.pdf"
                else:
                    md_path = f"markdown/{full_base}.md"
                    pdf_path = f"pdf/{full_base}.pdf"
                    
                s3.put_object(Bucket=bucket, Key=md_path, Body=st.session_state.md_content.encode("utf-8"))
                s3.put_object(Bucket=bucket, Key=pdf_path, Body=st.session_state.pdf_bytes)
                st.success("✅ Uloženo na R2.")
            except Exception as e: st.error(f"R2 Error: {e}")

        st.rerun()

    else:
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
    with st.chat_message("assistant", avatar="⚖️"):
        st.markdown(f"**{t('judge')}:**\n\n{st.session_state.final_summary}"); st.caption(f"🤖 `{st.session_state.model_mod_used}`")
    
    st.divider()
    render_downloads()
    
    # ZOBRAZENÍ KRITIKY A SOUHRNU JEN PRO POKROČILOU DISKUZI
    if not is_simple:
        render_critique_ui(available_providers)
        render_summary_ui(available_providers)
    
    st.divider()

if st.session_state.debate_finished:
    if st.button(t("new_debate"), use_container_width=True):
        st.session_state.debate_active = False
        st.session_state.debate_finished = False
        st.session_state.full_history = []
        st.session_state.summary_md = ""
        reset_critique_state()
        st.rerun()
