import streamlit as st
import random
from utils.config import t, PRESET_KEYS, TEMPERAMENT_KEYS, EXPERTISE_KEYS, LENGTH_KEYS, GOAL_KEYS, RULE_KEYS, MODE_KEYS, PRESETS
from utils.pdf_export import extract_text_from_file

def apply_preset_callback():
    preset = st.session_state.preset_select
    if preset == "custom" or preset not in PRESETS: return
    cfg = PRESETS[preset]
    st.session_state.temperament_a = cfg["temperament_a"]; st.session_state.expertise_a = cfg["expertise_a"]
    st.session_state.temperament_b = cfg["temperament_b"]; st.session_state.expertise_b = cfg["expertise_b"]
    st.session_state.temperament_c = cfg["temperament_a"]; st.session_state.expertise_c = cfg["expertise_a"] # C dedí z A
    st.session_state.response_length = cfg["response_length"]
    st.session_state.debate_goal = cfg["debate_goal"]
    st.session_state.debate_rules = list(cfg["debate_rules"])

def randomize_persona(prefix):
    st.session_state[f"temperament_{prefix}"] = random.choice(TEMPERAMENT_KEYS)
    st.session_state[f"expertise_{prefix}"] = random.choice(EXPERTISE_KEYS)

available_providers = []
if st.session_state.gemini_key.strip(): available_providers.append("Gemini")
if st.session_state.mistral_key.strip(): available_providers.append("Mistral")
if st.session_state.nim_key.strip(): available_providers.append("NVIDIA NIM")
select_options = available_providers if available_providers else ["(Zadejte klíč)"]

st.title(t("nav_setup"))

if st.session_state.setup_step == 1:
    st.subheader(t("setup_step1"))
    
    st.radio(t("mode_label"), options=MODE_KEYS, format_func=lambda k: t(f"mode_{k}"), key="debate_mode")
    st.divider()
    
    st.selectbox(t("preset_label"), options=PRESET_KEYS, format_func=lambda k: t(f"preset_{k}"), key="preset_select", on_change=apply_preset_callback, help=t("preset_help"))
    st.selectbox(t("response_length_label"), options=LENGTH_KEYS, format_func=lambda k: t(f"length_{k}"), key="response_length")
    st.radio(t("debate_goal_label"), options=GOAL_KEYS, format_func=lambda k: t(f"goal_{k}"), key="debate_goal")
    st.multiselect(t("rules_label"), options=RULE_KEYS, format_func=lambda k: t(f"rule_{k}"), key="debate_rules")

elif st.session_state.setup_step == 2:
    st.subheader(t("setup_step2"))
    mode = st.session_state.debate_mode
    if st.session_state.provider_a not in select_options: st.session_state.provider_a = select_options[0]
    if st.session_state.provider_b not in select_options: st.session_state.provider_b = select_options[0]
    if st.session_state.provider_c not in select_options: st.session_state.provider_c = select_options[0]
    if st.session_state.provider_mod not in select_options: st.session_state.provider_mod = select_options[0]

    # OSOBNOST A (Vždy AI)
    st.markdown(f"**{t('persona_a')} (AI)**")
    st.text_input(f"{t('name')} A", key="role_a_name")
    st.selectbox(f"{t('provider_select')} A:", select_options, key="provider_a")
    col_t, col_e = st.columns(2)
    with col_t: st.selectbox(t("temperament_label"), options=TEMPERAMENT_KEYS, format_func=lambda k: t(f"temperament_{k}"), key="temperament_a")
    with col_e: st.selectbox(t("expertise_label"), options=EXPERTISE_KEYS, format_func=lambda k: t(f"expertise_{k}"), key="expertise_a")
    st.button(t("random_button"), key="random_a", on_click=randomize_persona, args=("a",), use_container_width=True)
    st.radio(f"{t('input_type')} A:", options=["manual", "upload"], format_func=lambda x: t(x), key="input_type_a")
    if st.session_state.input_type_a == "manual": st.text_area(f"{t('instructions')} A", key="role_a_prompt")
    else:
        file_a = st.file_uploader(f"{t('upload')} A", type=["pdf", "md", "txt"], key="file_a")
        if file_a: st.session_state.role_a_prompt = extract_text_from_file(file_a)

    st.divider()

    # OSOBNOST B
    if mode in ["ai_vs_human", "ai_vs_ai_vs_human", "ai_vs_human_vs_human"]: # B je člověk
        st.markdown(f"**{t('persona_b')} (Člověk)**")
        st.text_input(t("human_name"), key="role_b_name")
    else: # B je AI
        st.markdown(f"**{t('persona_b')} (AI)**")
        st.text_input(f"{t('name')} B", key="role_b_name")
        st.selectbox(f"{t('provider_select')} B:", select_options, key="provider_b")
        col_t2, col_e2 = st.columns(2)
        with col_t2: st.selectbox(t("temperament_label"), options=TEMPERAMENT_KEYS, format_func=lambda k: t(f"temperament_{k}"), key="temperament_b")
        with col_e2: st.selectbox(t("expertise_label"), options=EXPERTISE_KEYS, format_func=lambda k: t(f"expertise_{k}"), key="expertise_b")
        st.button(t("random_button"), key="random_b", on_click=randomize_persona, args=("b",), use_container_width=True)
        st.radio(f"{t('input_type')} B:", options=["manual", "upload"], format_func=lambda x: t(x), key="input_type_b")
        if st.session_state.input_type_b == "manual": st.text_area(f"{t('instructions')} B", key="role_b_prompt")
        else:
            file_b = st.file_uploader(f"{t('upload')} B", type=["pdf", "md", "txt"], key="file_b")
            if file_b: st.session_state.role_b_prompt = extract_text_from_file(file_b)

    # OSOBNOST C
    if mode in ["ai_vs_ai_vs_ai", "ai_vs_ai_vs_human", "ai_vs_human_vs_human"]:
        st.divider()
        if mode == "ai_vs_ai_vs_human": # C je člověk
            st.markdown(f"**{t('persona_c')} (Člověk)**")
            st.text_input(t("human_name"), key="role_c_name")
        else: # C je AI
            st.markdown(f"**{t('persona_c')} (AI)**")
            st.text_input(f"{t('name')} C", key="role_c_name")
            st.selectbox(f"{t('provider_select')} C:", select_options, key="provider_c")
            col_t3, col_e3 = st.columns(2)
            with col_t3: st.selectbox(t("temperament_label"), options=TEMPERAMENT_KEYS, format_func=lambda k: t(f"temperament_{k}"), key="temperament_c")
            with col_e3: st.selectbox(t("expertise_label"), options=EXPERTISE_KEYS, format_func=lambda k: t(f"expertise_{k}"), key="expertise_c")
            st.button(t("random_button"), key="random_c", on_click=randomize_persona, args=("c",), use_container_width=True)
            st.radio(f"{t('input_type')} C:", options=["manual", "upload"], format_func=lambda x: t(x), key="input_type_c")
            if st.session_state.input_type_c == "manual": st.text_area(f"{t('instructions')} C", key="role_c_prompt")
            else:
                file_c = st.file_uploader(f"{t('upload')} C", type=["pdf", "md", "txt"], key="file_c")
                if file_c: st.session_state.role_c_prompt = extract_text_from_file(file_c)

    st.divider()
    st.markdown(f"**{t('moderator')}**")
    st.selectbox(f"{t('provider_select')}:", select_options, key="provider_mod")
    
    with st.expander(t("advanced_settings")):
        st.slider(t("rounds"), min_value=2, max_value=30, key="max_rounds")
        st.slider(t("memory_limit_label"), min_value=2, max_value=30, key="memory_limit")

elif st.session_state.setup_step == 3:
    st.subheader(t("setup_step3"))
    st.radio(t("topic_type"), options=["manual", "upload"], format_func=lambda x: t(x), key="topic_input_type")
    if st.session_state.topic_input_type == "manual":
        st.text_input(t("topic_text"), key="topic_input")
        st.session_state.topic_document_text = ""
    else:
        st.text_input(t("topic_file"), key="topic_input")
        topic_files = st.file_uploader(t("upload_topic"), type=["pdf", "md", "txt"], accept_multiple_files=True)
        if topic_files:
            file_names = "_".join([f.name for f in topic_files])
            if st.session_state.uploaded_files_hash != file_names:
                full_text = ""
                for f in topic_files: full_text += f"--- Document: {f.name} ---\n" + extract_text_from_file(f) + "\n\n"
                st.session_state.topic_document_text = full_text
                st.session_state.uploaded_files_hash = file_names
                st.success(f"✅ Načteno {len(topic_files)} dokumentů.")

st.divider()
col1, col2 = st.columns([1, 1])
with col1:
    if st.session_state.setup_step > 1:
        if st.button(t("back"), use_container_width=True):
            st.session_state.setup_step -= 1
            st.rerun()
with col2:
    if st.session_state.setup_step < 3:
        if st.button(t("next"), type="primary", use_container_width=True):
            st.session_state.setup_step += 1
            st.rerun()
    else:
        if st.button(t("start"), type="primary", use_container_width=True):
            # Validace
            is_valid = True
            if not st.session_state.topic_input.strip() or not st.session_state.role_a_name.strip(): is_valid = False
            if st.session_state.debate_mode != "ai_vs_human" and not st.session_state.role_b_name.strip(): is_valid = False
            if st.session_state.debate_mode in ["ai_vs_ai_vs_ai", "ai_vs_ai_vs_human", "ai_vs_human_vs_human"] and not st.session_state.role_c_name.strip(): is_valid = False

            if not is_valid:
                st.error("Vyplňte prosím všechna povinná pole (jména a téma).")
            elif st.session_state.topic_input_type == "upload" and not st.session_state.topic_document_text:
                st.error("Nahrajte prosím alespoň jeden dokument.")
            else:
                st.session_state.debate_active = True
                st.session_state.debate_finished = False
                st.session_state.current_round = 0
                st.session_state.turn_index = 0
                st.session_state.full_history = []
                st.session_state.current_topic = st.session_state.topic_input
                st.session_state.setup_step = 1 # Reset pro příště
                st.switch_page("app_pages/arena.py")
