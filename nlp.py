import json
import re
import unicodedata
from typing import Dict, List, Optional

# ==============================
# 1. TEXT CLEANING
# Removes noise only. Keeps headline, body, dates, numbers, localities,
# departments, road names. Hindi/Punjabi script is left untouched.
# ==============================
_TAG_RE      = re.compile(r"<[^>]+>")
_URL_RE      = re.compile(r"https?://\S+|www\.\S+")
_EMAIL_RE    = re.compile(r"\S+@\S+\.\S+")
_EMOJI_RE    = re.compile(
    "[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200d]+", flags=re.UNICODE
)
_WS_RE       = re.compile(r"[ \t\u00a0]+")
_NL_RE       = re.compile(r"\n{3,}")

# Boilerplate lines common on news sites (whole-line match, case-insensitive)
_BOILERPLATE = re.compile(
    r"^\s*(also read|read more|advertisement|follow us|subscribe|share this|"
    r"click here|download the app|join our|whatsapp|telegram|"
    r"sign up|newsletter|photo:|image:|file photo|representational image|"
    r"tags?:|topics?:|related:?|और पढ़ें|ਹੋਰ ਪੜ੍ਹੋ).*$",
    re.IGNORECASE | re.MULTILINE,
)


def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = _TAG_RE.sub(" ", text)
    text = _URL_RE.sub(" ", text)
    text = _EMAIL_RE.sub(" ", text)
    text = _EMOJI_RE.sub(" ", text)
    text = _BOILERPLATE.sub("", text)
    text = text.replace("\r", "\n")
    text = _WS_RE.sub(" ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = _NL_RE.sub("\n\n", text)
    return text.strip()


# ==============================
# 2. NER (rule-based)
# spaCy has no usable Hindi/Punjabi NER, and the entities we care about
# (Ludhiana localities, MC branches) are a closed vocabulary anyway.
# Extend LOCALITIES from your ZONE_MAP for full coverage.
# ==============================
LOCALITIES = [
    "Model Town", "Civil Lines", "BRS Nagar", "Sarabha Nagar", "Dugri",
    "Shimlapuri", "Jamalpur", "Focal Point", "Haibowal", "Gill Road",
    "Pakhowal Road", "Ferozepur Road", "Chandigarh Road", "Ghumar Mandi",
    "Rajguru Nagar", "Sherpur", "Tibba Road", "Salem Tabri", "Basant Avenue",
    "Bhai Randhir Singh Nagar", "Field Ganj", "Clock Tower", "Samrala Chowk",
    "Jagraon Bridge", "Bharat Nagar Chowk", "Millar Ganj", "Kitchlu Nagar",
    "Urban Estate", "Aggar Nagar", "Giaspura", "Mundian", "Ludhiana",
    "लुधियाना", "ਲੁਧਿਆਣਾ",
]
_LOC_RE = re.compile(
    "|".join(re.escape(l) for l in sorted(LOCALITIES, key=len, reverse=True)),
    re.IGNORECASE,
)

_DEPT_RE = re.compile(
    r"\b(Municipal Corporation|MC Ludhiana|MCL|Ludhiana Traffic Police|Traffic Police|"
    r"PSPCL|PPCB|PWD|NHAI|Health Department|Civil Surgeon|Improvement Trust|"
    r"Sewerage Board|Fire Brigade|Public Health|Building & Roads|B&R|O&M)\b"
    r"|नगर निगम|ਨਗਰ ਨਿਗਮ",
    re.IGNORECASE,
)

_ROAD_RE = re.compile(
    r"\b((?:[A-Z][\w\-]+\s){1,3}(?:Road|Rd|Chowk|Market|Marg|Colony|Nagar|"
    r"Enclave|Bypass|Flyover|Bridge|Park|Street|Lane|Mandi))\b"
)

_DATE_RE = re.compile(
    r"\b(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|"
    r"\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?,?\s?\d{0,4}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s\d{1,2},?\s?\d{0,4})\b",
    re.IGNORECASE,
)

_NUM_RE = re.compile(
    r"\b\d[\d,\.]*\s?(?:days?|weeks?|months?|years?|hours?|hrs?|residents?|families|"
    r"households?|houses?|shops?|streets?|lakh|crore|km|metres?|meters?|feet|ft|"
    r"%|per cent|complaints?|accidents?|deaths?|injured)\b",
    re.IGNORECASE,
)


def _uniq(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for s in seq:
        k = s.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(s.strip())
    return out


def extract_entities(text: str) -> Dict[str, List[str]]:
    return {
        "localities":  _uniq(m.group(0) for m in _LOC_RE.finditer(text)),
        "departments": _uniq(m.group(0) for m in _DEPT_RE.finditer(text)),
        "roads":       _uniq(m.group(1) for m in _ROAD_RE.finditer(text)),
        "dates":       _uniq(m.group(0) for m in _DATE_RE.finditer(text)),
        "numbers":     _uniq(m.group(0) for m in _NUM_RE.finditer(text)),
    }


# ==============================
# 3. SUMMARIZATION (extractive, no API call)
# Keeps the 3 most informative sentences in original order.
# A sentence scores higher for civic keywords, entities and numbers.
# ==============================
_SENT_SPLIT = re.compile(r"(?<=[.!?।])\s+|\n+")


def summarize(headline: str, body: str, entities: Dict[str, List[str]],
              max_sentences: int = 3, max_chars: int = 450) -> str:
    sentences = [s.strip() for s in _SENT_SPLIT.split(body) if len(s.strip()) > 25]
    if not sentences:
        return headline[:max_chars]

    ent_terms = [e.lower() for k in ("localities", "departments", "roads")
                 for e in entities[k]]
    scored = []
    for i, s in enumerate(sentences):
        low = s.lower()
        score = sum(2 for k in CIVIC_KEYWORDS if k in low)
        score += sum(2 for e in ent_terms if e in low)
        score += 1 if re.search(r"\d", s) else 0
        score += 3 if i == 0 else 0        # lead sentence usually carries the gist
        scored.append((score, i, s))

    top = sorted(sorted(scored, reverse=True)[:max_sentences], key=lambda t: t[1])
    summary = " ".join(s for _, _, s in top)
    return summary[:max_chars].rstrip()


# ==============================
# 4. PRE-FILTER CLASSIFICATION (cheap, HIGH RECALL)
# Goal: throw away obvious non-civic news so c.py only spends LLM calls on
# plausible candidates. It must never be stricter than c.py — when unsure,
# send it on. c.py stays the real decision-maker.
# ==============================
CIVIC_KEYWORDS = [
    # English
    "pothole", "road", "broken", "damaged", "sewer", "sewage", "manhole", "drain",
    "waterlog", "flood", "garbage", "waste", "dump", "stench", "sanitation",
    "street light", "streetlight", "dark", "water supply", "contaminated",
    "dirty water", "pipeline", "leak", "power cut", "outage", "transformer",
    "encroach", "traffic jam", "congestion", "signal", "hoarding", "mosquito",
    "dengue", "malaria", "residents", "complain", "demand", "unattended",
    "neglect", "municipal", "corporation", "civic", "park", "footpath", "open pit",
    # Hindi
    "गड्ढ", "सड़क", "सीवर", "नाली", "जलभराव", "कूड़ा", "कचरा", "बदबू", "स्ट्रीट लाइट",
    "पानी की सप्लाई", "दूषित", "बिजली कट", "अतिक्रमण", "जाम", "नगर निगम", "डेंगू",
    "मच्छर", "शिकायत", "लोग परेशान", "गंदगी",
    # Punjabi
    "ਟੋਏ", "ਸੜਕ", "ਸੀਵਰ", "ਨਾਲੀ", "ਪਾਣੀ ਭਰ", "ਕੂੜਾ", "ਗੰਦਗੀ", "ਬਿਜਲੀ", "ਕਬਜ਼",
    "ਜਾਮ", "ਨਗਰ ਨਿਗਮ", "ਡੇਂਗੂ", "ਸ਼ਿਕਾਇਤ", "ਪਰੇਸ਼ਾਨ",
]

# Clearly non-civic topics. Only used to lower the odds, never as a hard reject
# on their own if there is real civic signal.
NON_CIVIC_KEYWORDS = [
    "arrested", "murder", "theft", "robbery", "snatch", "fir registered", "chargesheet",
    "court", "bail", "smuggl", "drug peddler", "cricket", "match", "tournament",
    "wins gold", "medal", "election", "rally", "bjp", "congress", "aap", "akali",
    "bollywood", "film", "concert", "festival", "jayanti", "bhajan", "kirtan",
    "stock", "sensex", "iphone", "weather forecast",
    "गिरफ्तार", "हत्या", "चोरी", "लूट", "चुनाव", "क्रिकेट", "मैच",
    "ਗ੍ਰਿਫ਼ਤਾਰ", "ਕਤਲ", "ਚੋਰੀ", "ਚੋਣ", "ਕ੍ਰਿਕਟ",
]


def prefilter(headline: str, body: str, entities: Dict[str, List[str]]) -> Dict:
    text = f"{headline}\n{body}".lower()
    civic_hits = [k for k in CIVIC_KEYWORDS if k in text]
    neg_hits   = [k for k in NON_CIVIC_KEYWORDS if k in text]

    score = len(civic_hits)
    score += 1 if entities["departments"] else 0
    score += 1 if (entities["localities"] or entities["roads"]) else 0
    score -= 0.5 * len(neg_hits)

    # Very short / empty articles carry no signal: let c.py decide on headline.
    if len(body) < 80 and civic_hits:
        stage = "POTENTIAL_CIVIC"
    elif score >= 2 and civic_hits:
        stage = "POTENTIAL_CIVIC"
    else:
        stage = "GENERAL_NEWS"

    return {
        "stage":      stage,
        "civic_score": round(score, 2),
        "civic_hits": civic_hits[:8],
        "neg_hits":   neg_hits[:8],
    }


# ==============================
# DATABASE (MySQL connection imported from db.py)
# ==============================
from db import get_connection


def get_unprocessed(limit: Optional[int] = None) -> List[Dict]:
    """Fetch articles that have not yet gone through preprocessing."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT id, title, content
        FROM articles
        WHERE processed = FALSE OR processed IS NULL
        ORDER BY id ASC
    """

    if limit is not None:
        query += " LIMIT %s"
        cursor.execute(query, (int(limit),))
    else:
        cursor.execute(query)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def save_processed(article_id: int, rec: Dict):
    """
    Save only POTENTIAL_CIVIC articles in processed_articles.
    Mark both POTENTIAL_CIVIC and GENERAL_NEWS as processed in articles,
    so neither is fetched again by nlp.py.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if rec["stage"] == "POTENTIAL_CIVIC":
            cursor.execute("""
                INSERT INTO processed_articles
                    (article_id, cleaned_title, cleaned_content, entities,
                     summary, civic_score, matched_terms)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                article_id,
                rec["title"],
                rec["content"],
                json.dumps(rec["entities"], ensure_ascii=False),
                rec["summary"],
                rec["civic_score"],
                json.dumps(
                    {"civic": rec["civic_hits"], "neg": rec["neg_hits"]},
                    ensure_ascii=False
                ),
            ))

        # Mark the article only after the potential-civic insert succeeds,
        # or immediately for GENERAL_NEWS (which is intentionally not inserted).
        cursor.execute(
            "UPDATE articles SET processed = TRUE WHERE id = %s",
            (article_id,)
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


# ==============================
# PIPELINE
# ==============================
def process_article(article: Dict) -> Dict:
    title   = clean_text(article.get("title"))
    content = clean_text(article.get("content"))
    full    = f"{title}\n{content}"

    entities = extract_entities(full)
    summary  = summarize(title, content, entities)
    verdict  = prefilter(title, content, entities)

    return {
        "title": title, "content": content, "entities": entities,
        "summary": summary, **verdict,
    }


def preprocess_all(limit: Optional[int] = None):
    articles = get_unprocessed(limit)
    if not articles:
        print("✅ No new articles to pre-process.")
        return

    counts = {"POTENTIAL_CIVIC": 0, "GENERAL_NEWS": 0}
    for i, art in enumerate(articles, 1):
        try:
            rec = process_article(art)
            save_processed(art["id"], rec)
            counts[rec["stage"]] += 1
        except Exception as e:  # one bad article must not stop the batch
            print(f"  [{i}/{len(articles)}] article {art['id']} failed: {e}")

    print(f"\nPre-processed {len(articles)} articles")
    print(f"  → POTENTIAL_CIVIC (sent to c.py): {counts['POTENTIAL_CIVIC']}")
    print(f"  → GENERAL_NEWS (skipped)        : {counts['GENERAL_NEWS']}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Clean → NER → Summarize → Pre-filter")
    ap.add_argument("--limit", type=int)
    preprocess_all(ap.parse_args().limit)