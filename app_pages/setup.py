import streamlit as st
import random
from utils.config import t, PRESET_KEYS, TEMPERAMENT_KEYS, EXPERTISE_KEYS, LENGTH_KEYS, GOAL_KEYS, RULE_KEYS, MODE_KEYS, PRESETS
from utils.pdf_export import extract_text_from_file

def update_state(widget_key, state_key):
    st.session_state[state_key] = st.session_state[widget_key]

def apply_preset_callback():
    preset = st.session_state.w_preset
    st.session_state.preset_select = preset
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
    new_t = random.choice(TEMPERAMENT_KEYS)
    new_e = random.choice(EXPERTISE_KEYS)
    st.session_state[f"temperament_{prefix}"] = new_t
    st.session_state[f"expertise_{prefix}"] = new_e
    st.session_state[f"w_temperament_{prefix}"] = new_t
    st.session_state[f"w_expertise_{prefix}"] = new_e

def go_next():
    st.session_state.setup_step += 1
    for k in list(st.session_state.keys()):
        if k.startswith("w_"): del st.session_state[k]
    st.rerun()

def go_back():
    st.session_state.setup_step -= 1
    for k in list(st.session_state.keys()):
        if k.startswith("w_"): del st.session_state[k]
    st.rerun()

available_providers = []
if st.session_state.gemini_key.strip(): available_providers.append("Gemini")
if st.session_state.mistral_key.strip(): available_providers.append("Mistral")
if st.session_state.nim_key.strip(): available_providers.append("NVIDIA NIM")
select_options = available_providers if available_providers else ["(Zadejte klíč)"]

st.title(t("nav_setup"))

if st.session_state.setup_step == 1:
    st.subheader(t("setup_step1"))
    
    if "w_mode" not in st.session_state: st.session_state.w_mode = st.session_state.debate_mode
    if "w_preset" not in st.session_state: st.session_state.w_preset = st.session_state.preset_select
    if "w_length" not in st.session_state: st.session_state.w_length = st.session_state.response_length
    if "w_goal" not in st.session_state: st.session_state.w_goal = st.session_state.debate_goal
    if "w_rules" not in st.session_state: st.session_state.w_rules = st.session_state.debate_rules

    st.radio(t("mode_label"), options=MODE_KEYS, format_func=lambda k: t(f"mode_{k}"), key="w_mode", on_change=update_state, args=("w_mode", "debate_mode"))
    st.divider()
    st.selectbox(t("preset_label"), options=PRESET_KEYS, format_func=lambda k: t(f"preset_{k}"), key="w_preset", on_change=apply_preset_callback, help=t("preset_help"))
    st.selectbox(t("response_length_label"), options=LENGTH_KEYS, format_func=lambda k: t(f"length_{k}"), key="w_length", on_change=update_state, args=("w_length", "response_length"))
    st.radio(t("debate_goal_label"), options=GOAL_KEYS, format_func=lambda k: t(f"goal_{k}"), key="w_goal", on_change=update_state, args=("w_goal", "debate_goal"))
    st.multiselect(t("rules_label"), options=RULE_KEYS, format_func=lambda k: t(f"rule_{k}"), key="w_rules", on_change=update_state, args=("w_rules", "debate_rules"))

elif st.session_state.setup_step == 2:
    st.subheader(t("setup_step2"))
    mode = st.session_state.debate_mode
    
    if st.session_state.provider_a not in select_options: st.session_state.provider_a = select_options[0]
    if st.session_state.provider_b not in select_options: st.session_state.provider_b = select_options[0]
    if st.session_state.provider_c not in select_options: st.session_state.provider_c = select_options[0]
    if st.session_state.provider_mod not in select_options: st.session_state.provider_mod = select_options[0]

    for p in ["a", "b", "c"]:
        if f"w_role_{p}_name" not in st.session_state: st.session_state[f"w_role_{p}_name"] = st.session_state[f"role_{p}_name"]
        if f"w_provider_{p}" not in st.session_state: st.session_state[f"w_provider_{p}"] = st.session_state[f"provider_{p}"]
        if f"w_temperament_{p}" not in st.session_state: st.session_state[f"w_temperament_{p}"] = st.session_state[f"temperament_{p}"]
        if f"w_expertise_{p}" not in st.session_state: st.session_state[f"w_expertise_{p}"] = st.session_state[f"expertise_{p}"]
        if f"w_input_type_{p}" not in st.session_state: st.session_state[f"w_input_type_{p}"] = st.session_state[f"input_type_{p}"]
        if f"w_role_{p}_prompt" not in st.session_state: st.session_state[f"w_role_{p}_prompt"] = st.session_state[f"role_{p}_prompt"]
    
    if "w_provider_mod" not in st.session_state: st.session_state.w_provider_mod = st.session_state.provider_mod
    if "w_max_rounds" not in st.session_state: st.session_state.w_max_rounds = st.session_state.max_rounds
    if "w_memory_limit" not in st.session_state: st.session_state.w_memory_limit = st.session_state.memory_limit

    st.markdown(f"**{t('persona_a')} (AI)**")
    st.text_input(f"{t('name')} A", key="w_role_a_name", on_change=update_state, args=("w_role_a_name", "role_a_name"))
    st.selectbox(f"{t('provider_select')} A:", select_options, key="w_provider_a", on_change=update_state, args=("w_provider_a", "provider_a"))
    
    col_t, col_e = st.columns(2)
    with col_t: st.selectbox(t("temperament_label"), options=TEMPERAMENT_KEYS, format_func=lambda k: t(f"temperament_{k}"), key="w_temperament_a", on_change=update_state, args=("w_temperament_a", "temperament_a"))
    with col_e: st.selectbox(t("expertise_label"), options=EXPERTISE_KEYS, format_func=lambda k: t(f"expertise_{k}"), key="w_expertise_a", on_change=update_state, args=("w_expertise_a", "expertise_a"))
    
    st.button(t("random_button"), key="random_a", on_click=randomize_persona, args=("a",), use_container_width=True)
    
    st.radio(f"{t('input_type')} A:", options=["manual", "upload"], format_func=lambda x: t(x), key="w_input_type_a", on_change=update_state, args=("w_input_type_a", "input_type_a"))
    if st.session_state.w_input_type_a == "manual": 
        st.text_area(f"{t('instructions')} A", key="w_role_a_prompt", on_change=update_state, args=("w_role_a_prompt", "role_a_prompt"))
    else:
        file_a = st.file_uploader(f"{t('upload')} A", type=["pdf", "md", "txt"], key="file_a")
        if file_a: 
            st.session_state.w_role_a_prompt = extract_text_from_file(file_a)
            st.session_state.role_a_prompt = st.session_state.w_role_a_prompt

    st.divider()

    if mode in ["ai_vs_human", "ai_vs_human_vs_human"]:
        st.markdown(f"**{t('persona_b')} (Člověk)**")
        st.text_input(t("human_name"), key="w_role_b_name", on_change=update_state, args=("w_role_b_name", "role_b_name"))
    else:
        st.markdown(f"**{t('persona_b')} (AI)**")
        st.text_input(f"{t('name')} B", key="w_role_b_name", on_change=update_state, args=("w_role_b_name", "role_b_name"))
        st.selectbox(f"{t('provider_select')} B:", select_options, key="w_provider_b", on_change=update_state, args=("w_provider_b", "provider_b"))
        
        col_t2, col_e2 = st.columns(2)
        with col_t2: st.selectbox(t("temperament_label"), options=TEMPERAMENT_KEYS, format_func=lambda k: t(f"temperament_{k}"), key="w_temperament_b", on_change=update_state, args=("w_temperament_b", "temperament_b"))
        with col_e2: st.selectbox(t("expertise_label"), options=EXPERTISE_KEYS, format_func=lambda k: t(f"expertise_{k}"), key="w_expertise_b", on_change=update_state, args=("w_expertise_b", "expertise_b"))
        
        st.button(t("random_button"), key="random_b", on_click=randomize_persona, args=("b",), use_container_width=True)
        st.radio(f"{t('input_type')} B:", options=["manual", "upload"], format_func=lambda x: t(x), key="w_input_type_b", on_change=update_state, args=("w_input_type_b", "input_type_b"))
        
        if st.session_state.w_input_type_b == "manual": 
            st.text_area(f"{t('instructions')} B", key="w_role_b_prompt", on_change=update_state, args=("w_role_b_prompt", "role_b_prompt"))
        else:
            file_b = st.file_uploader(f"{t('upload')} B", type=["pdf", "md", "txt"], key="file_b")
            if file_b: 
                st.session_state.w_role_b_prompt = extract_text_from_file(file_b)
                st.session_state.role_b_prompt = st.session_state.w_role_b_prompt

    if mode in ["ai_vs_ai_vs_ai", "ai_vs_ai_vs_human", "ai_vs_human_vs_human"]:
        st.divider()
        if mode in ["ai_vs_ai_vs_human", "ai_vs_human_vs_human"]:
            st.markdown(f"**{t('persona_c')} (Člověk)**")
            st.text_input(t("human_name"), key="w_role_c_name", on_change=update_state, args=("w_role_c_name", "role_c_name"))
        else:
            st.markdown(f"**{t('persona_c')} (AI)**")
            st.text_input(f"{t('name')} C", key="w_role_c_name", on_change=update_state, args=("w_role_c_name", "role_c_name"))
            st.selectbox(f"{t('provider_select')} C:", select_options, key="w_provider_c", on_change=update_state, args=("w_provider_c", "provider_c"))
            
            col_t3, col_e3 = st.columns(2)
            with col_t3: st.selectbox(t("temperament_label"), options=TEMPERAMENT_KEYS, format_func=lambda k: t(f"temperament_{k}"), key="w_temperament_c", on_change=update_state, args=("w_temperament_c", "temperament_c"))
            with col_e3: st.selectbox(t("expertise_label"), options=EXPERTISE_KEYS, format_func=lambda k: t(f"expertise_{k}"), key="w_expertise_c", on_change=update_state, args=("w_expertise_c", "expertise_c"))
            
            st.button(t("random_button"), key="random_c", on_click=randomize_persona, args=("c",), use_container_width=True)
            st.radio(f"{t('input_type')} C:", options=["manual", "upload"], format_func=lambda x: t(x), key="w_input_type_c", on_change=update_state, args=("w_input_type_c", "input_type_c"))
            
            if st.session_state.w_input_type_c == "manual": 
                st.text_area(f"{t('instructions')} C", key="w_role_c_prompt", on_change=update_state, args=("w_role_c_prompt", "role_c_prompt"))
            else:
                file_c = st.file_uploader(f"{t('upload')} C", type=["pdf", "md", "txt"], key="file_c")
                if file_c: 
                    st.session_state.w_role_c_prompt = extract_text_from_file(file_c)
                    st.session_state.role_c_prompt = st.session_state.w_role_c_prompt

    st.divider()
    st.markdown(f"**{t('moderator')}**")
    st.selectbox(f"{t('provider_select')}:", select_options, key="w_provider_mod", on_change=update_state, args=("w_provider_mod", "provider_mod"))
    
    with st.expander(t("advanced_settings")):
        st.slider(t("rounds"), min_value=2, max_value=30, key="w_max_rounds", on_change=update_state, args=("w_max_rounds", "max_rounds"))
        st.slider(t("memory_limit_label"), min_value=2, max_value=30, key="w_memory_limit", on_change=update_state, args=("w_memory_limit", "memory_limit"))

elif st.session_state.setup_step == 3:
    st.subheader(t("setup_step3"))
    
    if "w_topic_input_type" not in st.session_state: st.session_state.w_topic_input_type = st.session_state.topic_input_type
    if "w_topic_input" not in st.session_state: st.session_state.w_topic_input = st.session_state.topic_input

    st.radio(t("topic_type"), options=["manual", "upload"], format_func=lambda x: t(x), key="w_topic_input_type", on_change=update_state, args=("w_topic_input_type", "topic_input_type"))
    
    if st.session_state.w_topic_input_type == "manual":
        st.text_input(t("topic_text"), key="w_topic_input", on_change=update_state, args=("w_topic_input", "topic_input"))
        st.session_state.topic_document_text = ""
    else:
        st.text_input(t("topic_file"), key="w_topic_input", on_change=update_state, args=("w_topic_input", "topic_input"))
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
        st.button(t("back"), use_container_width=True, on_click=go_back)
with col2:
    if st.session_state.setup_step < 3:
        st.button(t("next"), type="primary", use_container_width=True, on_click=go_next)
    else:
        if st.button(t("start"), type="primary", use_container_width=True):
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
                st.session_state.setup_step = 1
                st.switch_page("app_pages/arena.py")
