import time
import re
from google import genai
from google.genai import types
from openai import OpenAI
from utils.config import TEMPERAMENT_PROMPTS, EXPERTISE_PROMPTS, LENGTH_PROMPTS, RULE_PROMPTS, JUDGE_GOAL_PROMPTS

GEMINI_PREFERRED = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash"]
NVIDIA_PREFERRED = ["nvidia/nemotron-3-ultra-550b-a55b"]
MISTRAL_PREFERRED = ["ministral-3b-2512", "ministral-8b-2512", "codestral-2508", "mistral-large-2512"]

def get_available_gemini_models(client):
    try:
        models = client.models.list()
        available = [m.name.replace('models/', '') for m in models if 'generateContent' in getattr(m, 'supported_generation_methods', [])]
        verified = [m for m in GEMINI_PREFERRED if m in available]
        return verified if verified else (available if available else GEMINI_PREFERRED)
    except Exception: return GEMINI_PREFERRED

def get_available_mistral_models(client):
    try:
        all_models = client.models.list()
        available_ids = [m.id for m in all_models.data if m.id]
        verified = [m for m in MISTRAL_PREFERRED if m in available_ids]
        return verified if verified else (available_ids[:3] if available_ids else MISTRAL_PREFERRED)
    except Exception: return MISTRAL_PREFERRED

def get_delay_for_provider(provider):
    if provider == "NVIDIA NIM": return 2.0
    if provider == "Gemini": return 6.0  # Zvýšeno na 6s kvůli rate limitům (15 RPM)
    if provider == "Mistral": return 3.0
    return 2.0

def enhance_role_prompt(base_prompt, temperament, expertise, length, rules, lang):
    parts = [base_prompt]
    if t_prompt := TEMPERAMENT_PROMPTS[lang].get(temperament, ""): parts.append(t_prompt)
    if e_prompt := EXPERTISE_PROMPTS[lang].get(expertise, ""): parts.append(e_prompt)
    if l_prompt := LENGTH_PROMPTS[lang].get(length, ""): parts.append(l_prompt)
    for rule in rules:
        if r_prompt := RULE_PROMPTS[lang].get(rule, ""): parts.append(r_prompt)
    return "\n\n".join(parts)

def build_judge_prompt(base_prompt, goal, lang):
    parts = [base_prompt]
    if goal in ("consensus", "dissenter"):
        if goal_prompt := JUDGE_GOAL_PROMPTS[lang].get(goal, ""): parts.append(goal_prompt)
    return "\n\n".join(parts)

def generate_filename_from_topic(topic, call_ai_func, available_providers, **kwargs):
    priority = [p for p in ["Gemini", "Mistral", "NVIDIA NIM"] if p in available_providers]
    if not priority: return "debata"
    prompt = f"Based on the topic, generate a short filename (max 7 words, no diacritics, only letters/numbers/underscores). Topic: '{topic}'"
    system_prompt = "Reply only with the filename, nothing else."
    for provider in priority:
        try:
            raw_name, _ = call_ai_func(system_prompt, prompt, provider, **kwargs)
            clean = re.sub(r"[^a-z0-9_]+", "_", raw_name.strip().lower())
            clean = re.sub(r"_+", "_", clean).strip("_")
            if clean: return "_".join(clean.split("_")[:7])
        except Exception: continue
    return "debata"

# Univerzální funkce pro volání AI
def call_ai(system_prompt, user_prompt, provider, gemini_client=None, mistral_client=None, nim_client=None, gemini_models=None, mistral_models=None):
    full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
    if provider == "Gemini" and gemini_client:
        for model_name in (gemini_models or GEMINI_PREFERRED):
            for attempt in range(2):
                try:
                    response = gemini_client.models.generate_content(model=model_name, contents=full_prompt, config=types.GenerateContentConfig())
                    if response.text and response.text.strip(): return response.text, model_name
                except Exception as e:
                    if getattr(e, 'code', None) in [503, 429] and attempt == 0: time.sleep(2)
                    else: break
        raise Exception("All Gemini models failed.")
    elif provider == "Mistral" and mistral_client:
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        for model_name in (mistral_models or MISTRAL_PREFERRED):
            for attempt in range(2):
                try:
                    response = mistral_client.chat.completions.create(model=model_name, messages=messages, temperature=0.7)
                    if response.choices[0].message.content: return response.choices[0].message.content, model_name
                except Exception:
                    if attempt == 0: time.sleep(2)
                    else: break
        raise Exception("All Mistral models failed.")
    elif provider == "NVIDIA NIM" and nim_client:
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        for model_name in NVIDIA_PREFERRED:
            for attempt in range(2):
                try:
                    response = nim_client.chat.completions.create(model=model_name, messages=messages, temperature=0.7, extra_body={"chat_template_kwargs":{"enable_thinking":True}})
                    if response.choices[0].message.content: return response.choices[0].message.content, model_name
                except Exception:
                    if attempt == 0: time.sleep(2)
                    else: break
        raise Exception("All NVIDIA models failed.")
    raise Exception(f"Provider {provider} není dostupný nebo chybí klient.")

def call_critique_api(system_prompt, user_prompt, provider, keys):
    if provider == "Gemini":
        client = genai.Client(api_key=keys["gemini"], http_options=types.HttpOptions(timeout=180000))
        for model in get_available_gemini_models(client):
            try:
                r = client.models.generate_content(model=model, contents=f"{system_prompt}\n\n---\n\n{user_prompt}", config=types.GenerateContentConfig())
                if r.text and r.text.strip(): return r.text, model
            except Exception: pass
        raise Exception("Kritika přes Gemini selhala.")
    elif provider == "Mistral":
        client = OpenAI(api_key=keys["mistral"], base_url="https://api.mistral.ai/v1", timeout=180.0)
        for model in get_available_mistral_models(client):
            try:
                r = client.chat.completions.create(model=model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.7)
                if r.choices[0].message.content: return r.choices[0].message.content, model
            except Exception: pass
        raise Exception("Kritika přes Mistral selhala.")
    elif provider == "NVIDIA NIM":
        client = OpenAI(api_key=keys["nim"], base_url="https://integrate.api.nvidia.com/v1", timeout=180.0)
        for model in NVIDIA_PREFERRED:
            try:
                r = client.chat.completions.create(model=model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.7)
                if r.choices[0].message.content: return r.choices[0].message.content, model
            except Exception: pass
        raise Exception("Kritika přes NVIDIA selhala.")
    raise Exception("Neznámý poskytovatel.")
