import boto3
from botocore.client import Config
import streamlit as st
from datetime import datetime
from utils.pdf_export import generate_pdf
import json

@st.cache_resource
def get_r2_client():
    return boto3.client(
        service_name="s3",
        endpoint_url=f"https://{st.secrets['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=st.secrets["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(signature_version="s3v4", request_checksum_calculation="when_required"),
    )

def get_next_counter():
    s3 = get_r2_client()
    bucket = st.secrets["R2_BUCKET_NAME"]
    current = 0
    try:
        obj = s3.get_object(Bucket=bucket, Key="counter.txt")
        current = int(obj["Body"].read().decode("utf-8").strip())
    except Exception: pass
    next_val = current + 1
    s3.put_object(Bucket=bucket, Key="counter.txt", Body=str(next_val).encode("utf-8"))
    return f"{next_val:05d}"

# --- NOVÁ FUNKCE PRO ANALYTIKU ---
def log_debate_event(event_type, data):
    """Uloží jednoduchý analytický záznam do R2 (do složky analytics/)."""
    try:
        s3 = get_r2_client()
        bucket = st.secrets["R2_BUCKET_NAME"]
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **data
        }
        
        # Ukládáme do souboru pojmenovaného podle dne (např. debates_2026-11-14.jsonl)
        date_str = datetime.now().strftime("%Y-%m-%d")
        key = f"analytics/debates_{date_str}.jsonl"
        
        # Zkusíme načíst existující soubor pro daný den
        try:
            existing = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
        except Exception:
            existing = ""
            
        # Přidáme nový řádek a uložíme
        new_content = existing + json.dumps(log_entry, ensure_ascii=False) + "\n"
        s3.put_object(Bucket=bucket, Key=key, Body=new_content.encode("utf-8"))
    except Exception as e:
        # Analytika nesmí nikdy shodit aplikaci
        print(f"Chyba při ukládání analytiky: {e}")
        pass
# --------------------------------

def generate_critique_md(critique_text, model_used, topic):
    ts = datetime.now().strftime('%d.%m.%Y %H:%M')
    return f"# Nezávislá kritika diskuze\n\n**Téma:** {topic}  \n**Datum:** {ts}  \n**Model kritika:** {model_used}\n\n---\n\n{critique_text}\n"

def save_critique_to_r2(base_name, md_content, pdf_bytes):
    try:
        s3 = get_r2_client()
        bucket = st.secrets["R2_BUCKET_NAME"]
        s3.put_object(Bucket=bucket, Key=f"VERDICT/markdown/{base_name}.md", Body=md_content.encode("utf-8"), ContentType="text/markdown")
        s3.put_object(Bucket=bucket, Key=f"VERDICT/pdf/{base_name}.pdf", Body=pdf_bytes, ContentType="application/pdf")
        return True, None
    except Exception as e: return False, str(e)

def save_critique_result(critique_text, model_used):
    base_name = f"{st.session_state.file_base_name}_kritika"
    md_content = generate_critique_md(critique_text, model_used, st.session_state.current_topic)
    pdf_bytes = generate_pdf(md_content)
    st.session_state.critique_md = md_content
    st.session_state.critique_pdf = pdf_bytes
    st.session_state.critique_base = base_name
    ok, err = save_critique_to_r2(base_name, md_content, pdf_bytes)
    return ok, err, base_name

def reset_critique_state():
    st.session_state.critique_md = ""
    st.session_state.critique_pdf = b""
    st.session_state.critique_base = ""
    st.session_state.show_critique_ui = False
