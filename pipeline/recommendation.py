"""
pipeline/recommendation.py — Madame de la Grande Bouche
Exact RAG pipeline from rag_recommendation.ipynb:
  weather API → context → CLIP text embed → ChromaDB (category-balanced)
  → Groq Llama 3.3 70B → structured recommendation
"""
from __future__ import annotations
import json, re, datetime, requests
import torch


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY GROUPINGS  (from Cell 16 of rag_recommendation.ipynb)
# ─────────────────────────────────────────────────────────────────────────────

TOPS      = ["shirt, blouse", "top, t-shirt, sweatshirt", "sweater", "cardigan",
             "vest", "jacket", "coat", "dress", "jumpsuit"]
BOTTOMS   = ["pants", "shorts", "skirt", "tights, stockings"]
SHOES     = ["shoe"]
ACCYS     = ["glasses", "hat", "headband, head covering, hair accessory",
             "tie", "glove", "belt", "scarf", "bag, wallet"]

def _category_type(class_name: str) -> str:
    name = class_name.lower()
    for t in TOPS:
        if any(w in name for w in t.split(", ")): return "top"
    for b in BOTTOMS:
        if b in name: return "bottom"
    for s in SHOES:
        if s in name: return "shoes"
    for a in ACCYS:
        if any(w in name for w in a.split(", ")): return "accessory"
    return "other"


# ─────────────────────────────────────────────────────────────────────────────
# WEATHER  (Cell 14 of rag_recommendation.ipynb)
# ─────────────────────────────────────────────────────────────────────────────

def get_weather(city: str, api_key: str) -> dict:
    if not api_key or not api_key.strip():
        return _default_weather(city)
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key.strip()}&units=metric"
    )
    try:
        resp = requests.get(url, timeout=10)
        d    = resp.json()
        if resp.status_code != 200:
            return _default_weather(city, error=d.get("message"))

        temp = round(d["main"]["temp"])
        if   temp < 5:   warmth = "very cold — heavy coat and layers essential"
        elif temp < 12:  warmth = "cold — jacket or coat needed"
        elif temp < 18:  warmth = "cool — light jacket or sweater recommended"
        elif temp < 24:  warmth = "mild — comfortable in light layers"
        elif temp < 30:  warmth = "warm — light, breathable fabrics"
        else:            warmth = "hot — minimal, very breathable clothing"

        cond = d["weather"][0]["main"]
        rain = ""
        if cond in ("Rain", "Drizzle", "Thunderstorm"):
            rain = "Rain expected — avoid light fabrics, consider waterproof outerwear"
        elif cond == "Snow":
            rain = "Snow expected — warm waterproof layers essential"

        return {
            "city":         d["name"],
            "temp_c":       temp,
            "feels_like_c": round(d["main"]["feels_like"]),
            "humidity_pct": d["main"]["humidity"],
            "condition":    cond,
            "description":  d["weather"][0]["description"],
            "wind_kmh":     round(d["wind"]["speed"] * 3.6),
            "warmth_advice":warmth,
            "rain_advice":  rain,
            "icon_url":     f"https://openweathermap.org/img/wn/{d['weather'][0]['icon']}@2x.png",
            "live":         True,
            "error":        None,
        }
    except Exception as e:
        return _default_weather(city, error=str(e))


def _default_weather(city: str = "your city", error: str | None = None) -> dict:
    return {
        "city": city, "temp_c": 22, "feels_like_c": 22, "humidity_pct": 55,
        "condition": "Clear", "description": "Weather data unavailable — using defaults",
        "wind_kmh": 10, "warmth_advice": "mild — comfortable in light layers",
        "rain_advice": "", "icon_url": "", "live": False, "error": error,
    }


def get_time_context() -> dict:
    now   = datetime.datetime.now()
    h     = now.hour
    month = now.month
    tod   = "morning" if 5<=h<12 else "afternoon" if 12<=h<17 else "evening" if 17<=h<21 else "night"
    sea   = "winter" if month in (12,1,2) else "spring" if month in (3,4,5) else \
            "summer" if month in (6,7,8) else "autumn"
    return {"time_of_day": tod, "season": sea, "date": now.strftime("%A, %B %d %Y"), "hour": h}


def build_context(city: str, event: str, extra_notes: str = "", weather_api_key: str = "") -> dict:
    return {
        "weather":     get_weather(city, weather_api_key),
        "time":        get_time_context(),
        "event":       event,
        "extra_notes": extra_notes,
    }


# ─────────────────────────────────────────────────────────────────────────────
# RETRIEVAL  (category-balanced — Cell 16 of rag_recommendation.ipynb)
# ─────────────────────────────────────────────────────────────────────────────

def _build_query_text(context: dict) -> str:
    """Build a natural-language query for CLIP encoding (mirrors _build_query_text)."""
    w, t = context["weather"], context["time"]
    q = f"{context['event']} outfit for {t['season']} {t['time_of_day']}, "
    q += f"{w['temp_c']}°C {w['condition'].lower()} weather"
    if w.get("rain_advice"):  q += ", rainy conditions"
    if context.get("extra_notes"): q += f", {context['extra_notes']}"
    return q


def retrieve_wardrobe_items(
    chroma_collection,
    clip_model,
    clip_preprocess,
    context:         dict,
    device:          str,
    n_per_category:  int = 3,
) -> dict[str, list[dict]]:
    """
    Category-balanced retrieval from ChromaDB.
    Returns {category_type: [items]} — mirrors retrieve_wardrobe_items() from your notebook.
    """
    import clip as clip_lib

    total = chroma_collection.count()
    if total == 0:
        return {}

    query_text = _build_query_text(context)
    tokens = clip_lib.tokenize([query_text]).to(device)
    with torch.no_grad():
        text_feat = clip_model.encode_text(tokens)
        text_feat = text_feat / text_feat.norm(dim=-1, keepdim=True)
    query_vec = text_feat.cpu().numpy()[0].tolist()

    # broad retrieval first, then group
    n = min(total, max(20, n_per_category * 8))
    raw = chroma_collection.query(
        query_embeddings=[query_vec],
        n_results=n,
        include=["metadatas", "documents", "distances"],
    )

    grouped: dict[str, list[dict]] = {}
    if raw.get("metadatas") and raw["metadatas"][0]:
        for meta, doc, dist in zip(
            raw["metadatas"][0], raw["documents"][0], raw["distances"][0]
        ):
            item = dict(meta)
            item["document"]         = doc
            item["similarity_score"] = round(float(1 - dist), 3)

            cat = _category_type(item.get("class_name", ""))
            if cat not in grouped:
                grouped[cat] = []
            if len(grouped[cat]) < n_per_category:
                grouped[cat].append(item)

    return grouped


def flatten_items(grouped: dict[str, list[dict]]) -> list[dict]:
    """Flatten category-grouped items into a flat list for the LLM prompt."""
    return [item for items in grouped.values() for item in items]


# ─────────────────────────────────────────────────────────────────────────────
# LLM REASONING  (Cell 18 / Cell 20 of rag_recommendation.ipynb)
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are Madame de la Grande Bouche — an expert personal fashion stylist with deep knowledge
of outfit coordination, color theory, dress codes, and weather-appropriate dressing.

Your job is to recommend the best outfit from the user's wardrobe based on:
- The weather conditions (temperature, condition, humidity)
- The event or occasion
- The time of day and season
- The available clothing items and their attributes
- Color coordination and style compatibility

You must ONLY recommend items explicitly listed in the wardrobe.
Be specific, warm, and helpful. Explain WHY each item was chosen.
If the wardrobe is limited, make the best of what's available and say so kindly.

Respond ONLY with a JSON object matching this exact schema (no markdown fences, no preamble):
{
  "outfit": ["brief description of piece 1", "brief description of piece 2", ...],
  "recommended_ids": ["item_id_1", "item_id_2", ...],
  "reasoning": "2-3 sentences explaining why this outfit works",
  "styling_tips": "2-3 specific practical tips (layering, accessories, shoes)",
  "weather_note": "One sentence about weather-specific considerations",
  "confidence": 0.85
}""".strip()


def _format_wardrobe_for_prompt(grouped: dict[str, list[dict]]) -> str:
    """Mirrors _format_wardrobe_for_prompt() from your notebook."""
    lines = []
    for cat, items in grouped.items():
        lines.append(f"\n{cat.upper()}S:")
        for i, item in enumerate(items, 1):
            # collect attribute labels
            attr_labels = []
            for k, v in item.items():
                if k.startswith("attr_") and not k.endswith("_conf") and v:
                    attr_labels.append(f"{k[5:].replace('_',' ')}: {v}")
            attr_str = ", ".join(attr_labels[:4]) if attr_labels else ""
            lines.append(
                f"  {i}. [item_id: {item.get('item_id','?')}] "
                f"{item.get('class_name','item')} — "
                f"color: {item.get('color_name','')} "
                f"| similarity: {item.get('similarity_score',0):.2f}"
                + (f" | {attr_str}" if attr_str else "")
            )
    return "\n".join(lines) or "  (no items available)"


def _format_context_for_prompt(context: dict) -> str:
    """Mirrors _format_context_for_prompt() from your notebook."""
    w, t = context["weather"], context["time"]
    return (
        f"Date & Time : {t['date']}, {t['time_of_day']}\n"
        f"Season      : {t['season']}\n"
        f"Location    : {w['city']}\n"
        f"Temperature : {w['temp_c']}°C (feels like {w['feels_like_c']}°C)\n"
        f"Condition   : {w['description']}\n"
        f"Humidity    : {w['humidity_pct']}%\n"
        f"Wind        : {w['wind_kmh']} km/h\n"
        f"Advice      : {w['warmth_advice']}"
        + (f"\nRain note   : {w['rain_advice']}" if w.get("rain_advice") else "")
        + (f"\nUser notes  : {context['extra_notes']}" if context.get("extra_notes") else "")
    )


def get_groq_recommendation(
    groq_client,
    context:  dict,
    grouped:  dict[str, list[dict]],
    model:    str = "llama-3.3-70b-versatile",
) -> dict:
    """
    Full reasoning layer — mirrors generate_recommendation() from your notebook.
    """
    wardrobe_text = _format_wardrobe_for_prompt(grouped)
    context_text  = _format_context_for_prompt(context)
    all_items     = flatten_items(grouped)

    user_msg = (
        f"Please recommend an outfit for the following situation:\n\n"
        f"CONTEXT:\n{context_text}\n\n"
        f"EVENT: {context['event']}\n\n"
        f"AVAILABLE WARDROBE:\n{wardrobe_text}\n\n"
        f"Recommend a complete, weather-appropriate, occasion-suitable outfit "
        f"using ONLY the items listed above."
    )

    try:
        resp = groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=900,
            temperature=0.65,
        )
        raw = resp.choices[0].message.content.strip()
        m   = re.search(r"\{[\s\S]*\}", raw)
        payload = json.loads(m.group() if m else raw)

        payload.setdefault("outfit",          [])
        payload.setdefault("recommended_ids", [])
        payload.setdefault("reasoning",       "")
        payload.setdefault("styling_tips",    "")
        payload.setdefault("weather_note",    "")
        payload.setdefault("confidence",      0.8)
        payload["context"]   = context
        payload["all_items"] = all_items
        payload["error"]     = None
        return payload

    except Exception as e:
        return {
            "outfit": ["Could not generate recommendation"],
            "recommended_ids": [], "reasoning": f"Error: {e}",
            "styling_tips": "", "weather_note": "", "confidence": 0.0,
            "context": context, "all_items": all_items, "error": str(e),
        }
