import streamlit as st
import streamlit.components.v1 as components

def init_state():
    if "lang" not in st.session_state: st.session_state.lang = "cs"
    
    _restored_any_key = False
    if "g_key" in st.query_params: st.session_state.gemini_key = st.query_params["g_key"]; _restored_any_key = True
    if "n_key" in st.query_params: st.session_state.nim_key = st.query_params["n_key"]; _restored_any_key = True
    if "m_key" in st.query_params: st.session_state.mistral_key = st.query_params["m_key"]; _restored_any_key = True
    if _restored_any_key: st.query_params.clear()

    for key in ["gemini_key", "nim_key", "mistral_key"]:
        if key not in st.session_state: st.session_state[key] = ""

    if "local_storage_checked" not in st.session_state:
        if not st.session_state.gemini_key and not st.session_state.nim_key and not st.session_state.mistral_key:
            components.html("""
            <script>
                const g = localStorage.getItem('arena_gemini');
                const n = localStorage.getItem('arena_nim');
                const m = localStorage.getItem('arena_mistral');
                if (g || n || m) {
                    const url = new URL(window.parent.location.href);
                    if (g) url.searchParams.set('g_key', g); else url.searchParams.delete('g_key');
                    if (n) url.searchParams.set('n_key', n); else url.searchParams.delete('n_key');
                    if (m) url.searchParams.set('m_key', m); else url.searchParams.delete('m_key');
                    window.parent.location.href = url.toString();
                }
            </script>
            """, height=0)
        st.session_state.local_storage_checked = True

    form_defaults = {
        "role_a_name": "", "role_a_prompt": "", "provider_a": "Gemini", "input_type_a": "manual", "temperament_a": "neutral", "expertise_a": "professor",
        "role_b_name": "", "role_b_prompt": "", "provider_b": "Gemini", "input_type_b": "manual", "temperament_b": "neutral", "expertise_b": "professor",
        "role_c_name": "", "role_c_prompt": "", "provider_c": "Gemini", "input_type_c": "manual", "temperament_c": "neutral", "expertise_c": "professor",
        "debate_mode": "ai_vs_ai",
        "provider_mod": "Gemini", "topic_input": "", "max_rounds": 4,
        "topic_input_type": "manual", "topic_document_text": "", "topic_summary": "",
        "uploaded_files_hash": "", "preset_select": "academic",
        "response_length": "medium", "debate_goal": "verdict", "debate_rules": ["no_repeat", "cite_sources", "admit_ignorance"],
        "memory_limit": 10, "setup_step": 1, 
        "debate_active": False, "debate_finished": False, "current_round": 0, "turn_index": 0,
        "full_history": [], "final_summary": "", "model_mod_used": "", "current_topic": "", 
        "md_content": "", "pdf_bytes": b"", "file_base_name": "debata",
        "critique_md": "", "critique_pdf": b"", "critique_base": "", "show_critique_ui": False,
        
        # Skrytá paměť pro zachování stavu:
        "cached_debate_mode": None, "cached_preset_select": None, "cached_debate_rules": None, "cached_debate_goal": None, "cached_response_length": None,
        "cached_role_a_name": None, "cached_role_a_prompt": None, "cached_provider_a": None, "cached_temperament_a": None, "cached_expertise_a": None, "cached_input_type_a": None,
        "cached_role_b_name": None, "cached_role_b_prompt": None, "cached_provider_b": None, "cached_temperament_b": None, "cached_expertise_b": None, "cached_input_type_b": None,
        "cached_role_c_name": None, "cached_role_c_prompt": None, "cached_provider_c": None, "cached_temperament_c": None, "cached_expertise_c": None, "cached_input_type_c": None,
        "cached_provider_mod": None, "cached_max_rounds": None, "cached_memory_limit": None,
        "cached_topic_input_type": None, "cached_topic_input": None, "cached_topic_document_text": None, "cached_uploaded_files_hash": None,
    }
    for key, default in form_defaults.items():
        if key not in st.session_state: st.session_state[key] = default
