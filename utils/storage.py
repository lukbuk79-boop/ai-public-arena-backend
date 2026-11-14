import boto3
from botocore.client import Config
import streamlit as st
from datetime import datetime
from utils.pdf_export import generate_pdf
import json
import concurrent.futures

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

def log_debate_event(event_type, data):
    """Uloží záznam do denního souboru. Agregace probíhá až v dashboardu."""
    try:
        s3 = get_r2_client()
        bucket = st.secrets["R2_BUCKET_NAME"]
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **data
        }
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        key = f"analytics/daily/debates_{date_str}.jsonl"
        
        try:
            existing = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
        except Exception:
            existing = ""
        
        new_content = existing + json.dumps(log_entry, ensure_ascii=False) + "\n"
        s3.put_object(Bucket=bucket, Key=key, Body=new_content.encode("utf-8"))
    except Exception as e:
        print(f"Chyba při ukládání analytiky: {e}")
        pass

@st.cache_data(ttl=300, show_spinner=False)
def rebuild_totals_from_files():
    """Stáhne všechny denní soubory z R2 a vytvoří agregované statistiky."""
    s3 = get_r2_client()
    bucket = st.secrets["R2_BUCKET_NAME"]
    
    # 1. Získáme seznam všech denních souborů
    paginator = s3.get_paginator('list_objects_v2')
    all_keys = []
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix="analytics/daily/"):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".jsonl"):
                    all_keys.append(obj["Key"])
    except Exception:
        return None
    
    if not all_keys:
        return None
    
    # 2. Stáhneme všechny soubory paralelně
    def fetch(key):
        try:
            return s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
        except Exception:
            return ""
    
    contents = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        contents = list(executor.map(fetch, all_keys))
    
    # 3. Agregujeme data
    agg = {
        "total_debates": 0,
        "total_duration_sec": 0,
        "by_mode": {},
        "by_lang": {},
        "by_provider": {},
        "by_date": {}
    }
    
    for content in contents:
        for line in content.strip().split("\n"):
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            
            if entry.get("event") == "debate_completed":
                agg["total_debates"] += 1
                agg["total_duration_sec"] += entry.get("duration_sec", 0)
                
                mode = entry.get("mode", "unknown")
                agg["by_mode"][mode] = agg["by_mode"].get(mode, 0) + 1
                
                lang = entry.get("lang", "unknown")
                agg["by_lang"][lang] = agg["by_lang"].get(lang, 0) + 1
                
                for p in entry.get("providers", []):
                    agg["by_provider"][p] = agg["by_provider"].get(p, 0) + 1
                
                date_str = entry.get("timestamp", "")[:10]
                agg["by_date"][date_str] = agg["by_date"].get(date_str, 0) + 1
    
    return agg

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
