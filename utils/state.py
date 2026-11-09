import streamlit as st

def init_state():
    if "lang" not in st.session_state: st.session_state.lang = "cs"
    
    # API klíče (vydrží, dokud nezavřete záložku)
    for key in ["gemini_key", "nim_key", "mistral_key"]:
        if key not in st.session_state: st.session_state[key] = ""

    form_defaults = {
        "debate_mode": "ai_vs_ai", "preset_select": "academic", 
        "response_length": "medium", "debate_goal": "verdict", "debate_rules": ["no_repeat", "cite_sources", "admit_ignorance"],
        "role_a_name": "", "role_a_prompt": "", "provider_a": "Gemini", "temperament_a": "neutral", "expertise_a": "professor", "input_type_a": "manual",
        "role_b_name": "", "role_b_prompt": "", "provider_b": "Gemini", "temperament_b": "neutral", "expertise_b": "professor", "input_type_b": "manual",
        "role_c_name": "", "role_c_prompt": "", "provider_c": "Gemini", "temperament_c": "neutral", "expertise_c": "professor", "input_type_c": "manual",
        "provider_mod": "Gemini", "max_rounds": 4, "memory_limit": 10,
        "topic_input_type": "manual", "topic_input": "", "topic_document_text": "", "uploaded_files_hash": "",
        "setup_step": 1, "debate_active": False, "debate_finished": False, "current_round": 0, "turn_index": 0,
        "full_history": [], "final_summary": "", "model_mod_used": "", "current_topic": "", 
        "md_content": "", "pdf_bytes": b"", "file_base_name": "debata",
        "critique_md": "", "critique_pdf": b"", "critique_base": "", "show_critique_ui": False
    }
    for key, default in form_defaults.items():
        if key not in st.session_state: st.session_state[key] = default
