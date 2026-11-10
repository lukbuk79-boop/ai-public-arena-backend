import streamlit as st
import streamlit.components.v1 as components

def init_state():
    if "lang" not in st.session_state: st.session_state.lang = "en"
    
    _restored_any_key = False
    if "g_key" in st.query_params: st.session_state.saved_gemini = st.query_params["g_key"]; _restored_any_key = True
    if "n_key" in st.query_params: st.session_state.saved_nim = st.query_params["n_key"]; _restored_any_key = True
    if "m_key" in st.query_params: st.session_state.saved_mistral = st.query_params["m_key"]; _restored_any_key = True
    if _restored_any_key: st.query_params.clear()

    for key in ["saved_gemini", "saved_nim", "saved_mistral"]:
        if key not in st.session_state: st.session_state[key] = ""

    if "local_storage_checked" not in st.session_state:
        if not st.session_state.saved_gemini and not st.session_state.saved_nim and not st.session_state.saved_mistral:
            components.html("""
            <script>
                try {
                    const g = localStorage.getItem('arena_gemini');
                    const n = localStorage.getItem('arena_nim');
                    const m = localStorage.getItem('arena_mistral');
                    if (g || n || m) {
                        const url = new URL(window.location.href);
                        if (g) url.searchParams.set('g_key', g); else url.searchParams.delete('g_key');
                        if (n) url.searchParams.set('n_key', n); else url.searchParams.delete('n_key');
                        if (m) url.searchParams.set('m_key', m); else url.searchParams.delete('m_key');
                        window.location.href = url.toString();
                    }
                } catch(e) { console.error("LocalStorage blocked", e); }
            </script>
            """, height=0)
        st.session_state.local_storage_checked = True

    form_defaults = {
        "debate_mode": "ai_vs_ai", "preset_select": "academic", 
        "response_length": "medium", "debate_goal": "verdict", "debate_rules": ["no_repeat", "cite_sources", "admit_ignorance"],
        "role_a_name": "", "role_a_prompt": "", "provider_a": "Gemini", "temperament_a": "neutral", "expertise_a": "professor", "input_type_a": "manual",
        "role_b_name": "", "role_b_prompt": "", "provider_b": "Gemini", "temperament_b": "neutral", "expertise_b": "professor", "input_type_b": "manual",
        "role_c_name": "", "role_c_prompt": "", "provider_c": "Gemini", "temperament_c": "neutral", "expertise_c": "professor", "input_type_c": "manual",
        "provider_mod": "Gemini", "max_rounds": 4, "memory_limit": 10,
        "topic_input_type": "manual", "topic_input": "", "topic_document_text": "", "topic_summary": "", "uploaded_files_hash": "",
        "setup_step": 1, "debate_active": False, "debate_finished": False, "current_round": 0, "turn_index": 0,
        "full_history": [], "final_summary": "", "model_mod_used": "", "current_topic": "", 
        "md_content": "", "pdf_bytes": b"", "file_base_name": "debata",
        "critique_md": "", "critique_pdf": b"", "critique_base": "", "show_critique_ui": False
    }
    for key, default in form_defaults.items():
        if key not in st.session_state: st.session_state[key] = default
