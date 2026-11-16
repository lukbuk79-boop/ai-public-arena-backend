import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, ParamValidationError
import streamlit as st
from datetime import datetime
from utils.pdf_export import generate_pdf
import json
import logging
import random
import threading
import time
import uuid
import concurrent.futures

logger = logging.getLogger(__name__)

COUNTER_KEY = "counter.txt"
ANALYTICS_PREFIX = "analytics/daily/"


@st.cache_resource
def get_r2_client():
    return boto3.client(
        service_name="s3",
        endpoint_url=f"https://{st.secrets['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=st.secrets["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            request_checksum_calculation="when_required",
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=5,
            read_timeout=20,
        ),
    )


def _error_code(e):
    return e.response.get("Error", {}).get("Code", "")


def _is_missing(e):
    return _error_code(e) in ("NoSuchKey", "404", "NotFound")


def _is_precondition_failed(e):
    status = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return _error_code(e) in ("PreconditionFailed", "412") or status == 412


def get_next_counter(max_attempts=8):
    """
    Vrátí další pořadové číslo debaty (např. '00042').

    - Chybějící counter.txt = první debata (začíná se od 1).
    - Jakákoli jiná chyba čtení (síť, práva, poškozený obsah) se NEPOHLTÍ: výjimka jde
      volajícímu, který použije jiný identifikátor. Dřív se při chybě čtení čítač
      tiše vynuloval a přepsal, takže se přepisovaly starší soubory.
    - Zápis je podmíněný (If-Match / If-None-Match), takže dvě souběžné debaty
      nikdy nedostanou stejné číslo; kdo prohraje, zkusí to znovu.
    """
    s3 = get_r2_client()
    bucket = st.secrets["R2_BUCKET_NAME"]

    for attempt in range(max_attempts):
        etag = None
        current = 0
        try:
            obj = s3.get_object(Bucket=bucket, Key=COUNTER_KEY)
            etag = obj.get("ETag")
            current = int(obj["Body"].read().decode("utf-8").strip())
        except ClientError as e:
            if not _is_missing(e):
                raise
            # counter.txt zatím neexistuje -> current = 0, etag = None

        next_val = current + 1
        body = str(next_val).encode("utf-8")
        try:
            if etag:
                s3.put_object(Bucket=bucket, Key=COUNTER_KEY, Body=body, IfMatch=etag)
            else:
                s3.put_object(Bucket=bucket, Key=COUNTER_KEY, Body=body, IfNoneMatch="*")
            return f"{next_val:05d}"
        except ClientError as e:
            if _is_precondition_failed(e):
                # Mezitím zapsala někdo jiný – krátká náhodná pauza a nové čtení
                time.sleep(random.uniform(0.05, 0.25) * (attempt + 1))
                continue
            raise
        except ParamValidationError:
            # Příliš stará verze boto3 nezná IfMatch/IfNoneMatch (je potřeba boto3 >= 1.36).
            logger.warning("boto3 nepodporuje podmíněné zápisy, čítač není chráněn proti souběhu.")
            s3.put_object(Bucket=bucket, Key=COUNTER_KEY, Body=body)
            return f"{next_val:05d}"

    raise RuntimeError("Nepodařilo se získat další číslo debaty (příliš mnoho souběžných zápisů).")


def log_debate_event(event_type, data):
    """
    Uloží jednu událost jako samostatný objekt (analytics/daily/<datum>/<čas>_<id>.jsonl).
    Žádné čtení a přepisování sdíleného souboru -> souběžné debaty se nemohou ztratit
    a zápis nezpomaluje s růstem dat. Agregace probíhá až v dashboardu.
    """
    try:
        s3 = get_r2_client()
        bucket = st.secrets["R2_BUCKET_NAME"]

        now = datetime.now()
        log_entry = {
            "timestamp": now.isoformat(),
            "event": event_type,
            **data
        }

        key = f"{ANALYTICS_PREFIX}{now.strftime('%Y-%m-%d')}/{now.strftime('%H%M%S')}_{uuid.uuid4().hex[:8]}.jsonl"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=(json.dumps(log_entry, ensure_ascii=False) + "\n").encode("utf-8"),
            ContentType="application/x-ndjson",
        )
    except Exception as e:
        logger.warning("Chyba při ukládání analytiky: %s", e)


# Objekty s událostmi se nikdy nemění, proto stačí každý stáhnout jednou.
# Klíčem je (key, ETag), takže se správně zachází i se starými denními soubory,
# které se mohly měnit.
_OBJECT_CACHE = {}
_OBJECT_CACHE_LOCK = threading.Lock()
_OBJECT_CACHE_MAX = 20000


def _fetch_object_text(s3, bucket, key, etag):
    cache_key = (key, etag)
    with _OBJECT_CACHE_LOCK:
        cached = _OBJECT_CACHE.get(cache_key)
    if cached is not None:
        return cached
    try:
        text = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
    except Exception as e:
        logger.warning("Nelze stáhnout %s: %s", key, e)
        return ""
    with _OBJECT_CACHE_LOCK:
        if len(_OBJECT_CACHE) >= _OBJECT_CACHE_MAX:
            _OBJECT_CACHE.clear()
        _OBJECT_CACHE[cache_key] = text
    return text


@st.cache_data(ttl=300, show_spinner=False)
def rebuild_totals_from_files():
    """Stáhne nové soubory s událostmi z R2 (už stažené se berou z paměti) a vytvoří agregované statistiky."""
    s3 = get_r2_client()
    bucket = st.secrets["R2_BUCKET_NAME"]

    # 1. Seznam všech souborů s událostmi (nové i původní denní)
    paginator = s3.get_paginator('list_objects_v2')
    all_objects = []
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=ANALYTICS_PREFIX):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".jsonl"):
                    all_objects.append((obj["Key"], obj.get("ETag", "")))
    except Exception as e:
        logger.warning("Nelze vypsat analytiku: %s", e)
        return None

    if not all_objects:
        return None

    # 2. Stáhneme (zatím nestažené) soubory paralelně
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        contents = list(executor.map(lambda ko: _fetch_object_text(s3, bucket, ko[0], ko[1]), all_objects))

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


def read_daily_entries(date_str):
    """Všechny události jednoho dne (nové samostatné soubory i původní denní soubor), seřazené podle času."""
    s3 = get_r2_client()
    bucket = st.secrets["R2_BUCKET_NAME"]

    keys = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=f"{ANALYTICS_PREFIX}{date_str}/"):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".jsonl"):
                keys.append((obj["Key"], obj.get("ETag", "")))

    # původní formát: jeden soubor na den
    legacy_key = f"{ANALYTICS_PREFIX}debates_{date_str}.jsonl"
    try:
        head = s3.head_object(Bucket=bucket, Key=legacy_key)
        keys.append((legacy_key, head.get("ETag", "")))
    except ClientError as e:
        if not _is_missing(e):
            raise

    entries = []
    for key, etag in keys:
        for line in _fetch_object_text(s3, bucket, key, etag).strip().split("\n"):
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                continue
    entries.sort(key=lambda e: e.get("timestamp", ""))
    return entries


def generate_critique_md(critique_text, model_used, topic):
    ts = datetime.now().strftime('%d.%m.%Y %H:%M')
    return f"# Nezávislá kritika diskuze\n\n**Téma:** {topic}  \n**Datum:** {ts}  \n**Model kritika:** {model_used}\n\n---\n\n{critique_text}\n"


def save_critique_to_r2(base_name, md_content, pdf_bytes):
    try:
        s3 = get_r2_client()
        bucket = st.secrets["R2_BUCKET_NAME"]
        s3.put_object(Bucket=bucket, Key=f"VERDICT/markdown/{base_name}.md", Body=md_content.encode("utf-8"), ContentType="text/markdown")
        # Když se PDF nepodařilo vygenerovat (prázdné bajty), neukládáme prázdný soubor.
        if pdf_bytes:
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
