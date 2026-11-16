import hmac
import json
from datetime import datetime

import streamlit as st

from utils.storage import get_r2_client, rebuild_totals_from_files

st.title("📊 Analytika Arény")

# --- Ochrana heslem ---
# Žádné výchozí heslo: když DASHBOARD_PASSWORD chybí v secrets, dashboard zůstane zavřený.
expected_password = st.secrets.get("DASHBOARD_PASSWORD")
if not expected_password:
    st.error("Dashboard není nakonfigurován (chybí DASHBOARD_PASSWORD v secrets).")
    st.stop()

# Po úspěšném přihlášení si to pamatujeme v session, aby se heslo nezadávalo
# znovu po každém kliknutí na tlačítko.
if not st.session_state.get("dash_ok"):
    heslo = st.text_input("Zadejte heslo pro přístup k analytice:", type="password")
    if not heslo:
        st.stop()
    if not hmac.compare_digest(heslo.encode("utf-8"), str(expected_password).encode("utf-8")):
        st.error("Špatné heslo.")
        st.stop()
    st.session_state.dash_ok = True
    st.rerun()

# Načtení dat (používá cache z storage.py)
agg_data = rebuild_totals_from_files()

if not agg_data:
    st.info("Zatím nejsou k dispozici žádná data. Spusťte první debatu!")
    st.stop()

# --- Horní souhrn ---
col1, col2, col3 = st.columns(3)
col1.metric("📈 Celkem dokončených debat", agg_data["total_debates"])
avg_dur = agg_data["total_duration_sec"] / max(agg_data["total_debates"], 1) / 60
col2.metric("⏱️ Průměrná délka", f"{avg_dur:.1f} min")

top_lang = "cs" if agg_data["by_lang"].get("cs", 0) >= agg_data["by_lang"].get("en", 0) else "en"
col3.metric("🌐 Dominantní jazyk", "CS" if top_lang == "cs" else "EN")

st.divider()

# --- Graf: Debaty po dnech ---
st.subheader("📅 Počet debat po dnech")
if agg_data["by_date"]:
    # Seřadíme data podle data pro správné zobrazení
    sorted_dates = dict(sorted(agg_data["by_date"].items()))
    st.bar_chart(sorted_dates)
else:
    st.info("Zatím žádná data.")

st.divider()

# --- Grafy: Rozdělení ---
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("🎭 Typy debat")
    st.bar_chart(agg_data["by_mode"])
with col_b:
    st.subheader("🤖 Použité modely")
    st.bar_chart(agg_data["by_provider"])

st.divider()

# --- Tlačítko pro vynucení obnovení cache ---
if st.button("🔄 Obnovit data (vymazat cache)"):
    rebuild_totals_from_files.clear()
    st.rerun()

st.caption("💡 Data se automaticky obnovují každých 5 minut. Pro okamžité obnovení použijte tlačítko výše.")

# --- Poslední záznamy (detail) ---
st.divider()
st.subheader("📋 Detail posledního dne")
if st.button("Načíst detailní historii dnešního dne"):
    try:
        s3 = get_r2_client()
        bucket = st.secrets["R2_BUCKET_NAME"]
        date_str = datetime.now().strftime("%Y-%m-%d")
        key = f"analytics/daily/debates_{date_str}.jsonl"
        obj = s3.get_object(Bucket=bucket, Key=key)
        lines = obj["Body"].read().decode("utf-8").strip().split("\n")
        entries = [json.loads(line) for line in lines if line]
        st.dataframe(entries)
    except Exception as e:
        st.error(f"Nelze načíst detail: {e}")