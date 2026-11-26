import requests
from bs4 import BeautifulSoup
import time
from db import init_db, insert_article, check_link_exists
import os
from atproto import Client as ATClient
from telethon import TelegramClient
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()
FETCHLAYER_API_KEY = os.getenv("FETCHLAYER_API_KEY")
REDDIT_SEARCH_TERMS = [
    "Ludhiana water garbage sewage drainage",
    "Ludhiana road, pothole, pollution",
    
]
reddit_cache = {}


# ==============================
# REDDIT USING FETCHLAYER
# ==============================

FETCHLAYER_API_KEY = os.getenv("FETCHLAYER_API_KEY")



reddit_cache = {}


def reddit_get_links():
    global reddit_cache

    reddit_cache = {}
    links = []

    if not FETCHLAYER_API_KEY:
        print("[Reddit] API key missing")
        return []

    headers = {
        "Authorization": f"Bearer {FETCHLAYER_API_KEY}",
        "Content-Type": "application/json"
    }

    CIVIC_KEYWORDS = [
        "water",
        "garbage",
        "waste",
        "sewage",
        "sewer",
        "drainage",
        "road",
        "pothole",
        "traffic",
        "pollution",
        "electricity",
        "power cut",
        "street light",
        "flood",
        "drinking water",
        "water supply",
        "sanitation",
        "municipal"
    ]

    for query in REDDIT_SEARCH_TERMS:

        print(f"\n[Reddit] Searching: {query}")

        payload = {
            "query": query,
            "sort": "new",
            "time": "month",
            "limit": 25,
            "pages": 1
        }

        try:
            response = requests.post(
                "https://api.fetchlayer.dev/reddit/search",
                headers=headers,
                json=payload,
                timeout=20
            )

            response.raise_for_status()
            data = response.json()

        except Exception as e:
            print(f"[Reddit] FetchLayer error: {e}")
            continue

        posts = data.get("items", [])

        print(f"[Reddit] Results returned: {len(posts)}")

        for post in posts:

            title = post.get("title", "") or ""
            preview = post.get("previewText", "") or ""

            text = f"{title} {preview}".lower()

            # Civic filtering
            if not any(keyword in text for keyword in CIVIC_KEYWORDS):
                print(f"   ❌ Non-civic: {title}")
                continue

            link = post.get("url")

            if not link:
                continue

            print(f"   ✅ Civic candidate: {title}")

            reddit_cache[link] = {
                "title": title,
                "content": preview,
                "subreddit": post.get("subreddit", ""),
                "score": post.get("score", 0),
                "comment_count": post.get("commentCount", 0),
                "created_at": post.get("createdAt", "")
            }

            links.append(link)

    print(f"\n[Reddit] Civic candidates found: {len(links)}")

    return links



def reddit_extract(link):

    data = reddit_cache.get(link)


    if not data:
        return None


    return {

        "title": data["title"],

        "link": link,

        "content": data["content"],

        "source": "Reddit"

    }
#using apify for facebook ludhiana live page



# client=ApifyClient(os.getenv("Apify"))
# run_input = {
#     "urls": [
#         "https://www.facebook.com/LudhianaLiveNews/"
#     ],
#     "maxResults": 5
# }


# run = client.actor(
#     "api-ninja/facebook-posts-scraper"
# ).call(
#     run_input=run_input
# )

# print("Run completed!")

# items = client.dataset(
#     run.default_dataset_id
# ).list_items().items

# print("Total posts:", len(items))
#un #it



# for item in items:

#     content = item.get("message")
#     link = item.get("url")

#     # Skip posts without text
#     if not content:
#         continue

#     # Avoid duplicate posts
#     if check_link_exists(link):
#         continue

#     headline = content[:200]
#     source = "Facebook - Ludhiana Live"

#     insert_article(
#         headline,
#         link,
#         content,
#         source
#     )

#     print("✅ Scraped post stored successfully:", headline)


# ==============================
# TWITTER (X) USING APIFY
# ==============================

APIFY_TWITTER_TOKEN = os.getenv("APIFY_TWITTER_TOKEN")

TWITTER_SEARCH_TERMS = [
    "Ludhiana garbage OR waste",
    "Ludhiana potholes OR damaged roads",
    "Ludhiana sewage OR drainage",
    "Ludhiana waterlogging OR water shortage",
    "Ludhiana pollution OR municipal corporation"
]

twitter_cache = {}


def twitter_get_links():
    global twitter_cache

    twitter_cache = {}
    links = []

    if not APIFY_TWITTER_TOKEN:
        print("[Twitter] Apify token missing")
        return []

    try:
        client = ApifyClient(APIFY_TWITTER_TOKEN)

        print("[Twitter] Starting Apify Actor...")

        run_input = {
            "searchTerms": TWITTER_SEARCH_TERMS,
            "maxItems": 10,
            "sort": "Latest"
        }

        run = client.actor(
            "apidojo/tweet-scraper"
        ).call(run_input=run_input)

        if not run:
            print("[Twitter] Actor run failed")
            return []

        if run.status != "SUCCEEDED":
            print(f"[Twitter] Actor status: {run.status}")
            return []

        items = client.dataset(
            run.default_dataset_id
        ).iterate_items()

        CIVIC_KEYWORDS = [
            "water", "garbage", "waste",
            "sewage", "sewer", "drainage",
            "road", "pothole", "traffic",
            "pollution", "electricity",
            "power cut", "street light",
            "flood", "water supply",
            "sanitation", "municipal"
        ]

        for tweet in items:

            content = tweet.get("text", "") or ""

            link = (
                tweet.get("url")
                or tweet.get("twitterUrl")
            )

            if not content or not link:
                continue

            # Basic civic keyword filtering
            if not any(
                word in content.lower()
                for word in CIVIC_KEYWORDS
            ):
                print(
                    f"   Non-civic: {content[:80]}"
                )
                continue

            title = content[:200]

            twitter_cache[link] = {
                "title": title,
                "content": content
            }

            links.append(link)

            print(
                f"   Civic candidate: {title[:80]}"
            )

        print(
            f"\n[Twitter] Civic candidates found: {len(links)}"
        )

    except Exception as e:
        print(f"[Twitter] Apify error: {e}")

    return links


def twitter_extract(link):

    data = twitter_cache.get(link)

    if not data:
        return None

    return {
        "title": data["title"],
        "link": link,
        "content": data["content"],
        "source": "X (Twitter)"
    }



# ==============================
# CONFIGURATION
# ==============================
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

DELAY = 1.5   # seconds between requests

# ==============================
# HELPER
# ==============================

def safe_get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"  [GET] Error: {url[:60]} — {e}")
        return None

def extract_paragraphs(soup, selectors):
    for selector in selectors:
        body = soup.find("div", class_=selector)
        if body:
            break
    else:
        body = soup

    paragraphs = body.find_all("p")
    content = " ".join(
        p.get_text(strip=True)
        for p in paragraphs
        if len(p.get_text(strip=True)) >= 40
        and "Subscribe" not in p.get_text()
    )
    return content

# ==============================
# 1. HINDUSTAN TIMES
# ==============================
def ht_get_links():
    r = safe_get("https://www.hindustantimes.com/topic/ludhiana")
    if not r: return []
    soup = BeautifulSoup(r.text, "html.parser")
    seen, links = set(), []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if h.startswith("https://www.hindustantimes.com/cities/") and "ludhiana" in h.lower() and h.endswith(".html"):
            if h not in seen:
                seen.add(h)
                links.append(h)
    print(f"  [HT] Found {len(links)} links")
    return links

def ht_extract(link):
    r = safe_get(link)
    if not r: return None
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else "No Title"
    content = extract_paragraphs(soup, ["detail", "story-details"])
    if len(content) < 100: return None
    return {"title": title, "link": link, "content": content, "source": "Hindustan Times"}

# ==============================
# 2. THE TRIBUNE
# ==============================
def tribune_get_links():
    seen, links = set(), []
    # Removed the broken search URL, kept the working category URL
    for url in ["https://www.tribuneindia.com/ludhiana"]:
        r = safe_get(url)
        if not r: continue
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            h = a["href"]
            if ("/news/" in h or "/story/" in h) and "ludhiana" in h.lower():
                full = h if h.startswith("http") else "https://www.tribuneindia.com" + h
                if full not in seen:
                    seen.add(full)
                    links.append(full)
    print(f"  [Tribune] Found {len(links)} links")
    return links

def tribune_extract(link):
    r = safe_get(link)
    if not r: return None
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else "No Title"
    content = extract_paragraphs(soup, ["story-content", "article-content", "content-area"])
    if len(content) < 100: return None
    return {"title": title, "link": link, "content": content, "source": "The Tribune"}

# ==============================
# 3. TIMES OF INDIA
# ==============================
def toi_get_links():
    r = safe_get("https://timesofindia.indiatimes.com/city/ludhiana")
    if not r: return []
    soup = BeautifulSoup(r.text, "html.parser")
    seen, links = set(), []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "ludhiana" in h.lower() and h.endswith(".cms"):
            full = h if h.startswith("http") else "https://timesofindia.indiatimes.com" + h
            if full not in seen:
                seen.add(full)
                links.append(full)
    print(f"  [TOI] Found {len(links)} links")
    return links

def toi_extract(link):
    r = safe_get(link)
    if not r: return None
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else "No Title"
    content = extract_paragraphs(soup, ["ga-headlines", "article-body", "_s30J"])
    if len(content) < 100: return None
    return {"title": title, "link": link, "content": content, "source": "Times of India"}

# ==============================
# 4. JAGRAN
# ==============================
def jagran_get_links():
    r = safe_get("https://www.jagran.com/local/punjab_ludhiana-news-hindi.html")
    if not r: return []
    soup = BeautifulSoup(r.text, "html.parser")
    seen, links = set(), []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "jagran.com" in h and "ludhiana" in h.lower():
            full = h if h.startswith("http") else "https://www.jagran.com" + h
            if full not in seen:
                seen.add(full)
                links.append(full)
    print(f"  [Jagran] Found {len(links)} links")
    return links

def jagran_extract(link):
    r = safe_get(link)
    if not r: return None
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else "No Title"
    content = extract_paragraphs(soup, ["article-body", "content", "artbody"])
    if len(content) < 100: return None
    return {"title": title, "link": link, "content": content, "source": "Jagran"}

# ==============================
# 5. PUNJAB KESARI
# ==============================
def pk_get_links():
    r = safe_get("https://jagbani.punjabkesari.in/ludhiana")
    if not r: return []
    soup = BeautifulSoup(r.text, "html.parser")
    seen, links = set(), []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "punjabkesari.in" in h and "ludhiana" in h.lower():
            full = h if h.startswith("http") else "https://www.punjabkesari.in" + h
            if full not in seen:
                seen.add(full)
                links.append(full)
    print(f"  [PK] Found {len(links)} links")
    return links

def pk_extract(link):
    r = safe_get(link)
    if not r: return None
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else "No Title"
    content = extract_paragraphs(soup, ["article-detail", "content-area", "article-content"])
    if len(content) < 100: return None
    return {"title": title, "link": link, "content": content, "source": "Punjab Kesari"}
# ==============================
# 6. BLUESKY
# ==============================
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD")
BLUESKY_SEARCH_TERMS = ["Ludhiana"]   
_bluesky_client = None
_bluesky_cache = {}   # link -> {"title":..., "content":...}

def bluesky_login():
    global _bluesky_client
    if _bluesky_client is None:
        if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
            raise RuntimeError("Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD environment variables first.")
        _bluesky_client = ATClient()
        _bluesky_client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)
    return _bluesky_client

def bluesky_get_links():
    global _bluesky_cache
    _bluesky_cache = {}
    links = []
    try:
        client = bluesky_login()
        for term in BLUESKY_SEARCH_TERMS:
            results = client.app.bsky.feed.search_posts({"q": term, "limit": 25})
            for post in results.posts:
                text = getattr(post.record, "text", "") or ""
                if len(text) < 30:
                    continue
                handle = post.author.handle
                rkey = post.uri.split("/")[-1]
                web_link = f"https://bsky.app/profile/{handle}/post/{rkey}"
                if web_link not in _bluesky_cache:
                    title = text[:80] + ("..." if len(text) > 80 else "")
                    _bluesky_cache[web_link] = {"title": title, "content": text}
                    links.append(web_link)
    except Exception as e:
        print(f"  [Bluesky] Error: {e}")
    print(f"  [Bluesky] Found {len(links)} posts")
    return links

def bluesky_extract(link):
    data = _bluesky_cache.get(link)
    if not data:
        return None
    return {
        "title": data["title"],
        "link": link,
        "content": data["content"],
        "source": "Bluesky"
    }
# ==============================
# TELEGRAM
# ==============================

TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID"))
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH")
TELEGRAM_PHONE = os.environ.get("TELEGRAM_PHONE")


telegram_client = TelegramClient(
    "telegram_session",
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH
)


TELEGRAM_CHANNELS = [
    "Official5dariyanews"
]
def telegram_get_links():

    links = []

    async def fetch():

        await telegram_client.start(
            phone=TELEGRAM_PHONE
        )

        for channel in TELEGRAM_CHANNELS:

            async for message in telegram_client.iter_messages(
                channel,
                limit=50
            ):

                text = message.text

                if not text:
                    continue


                if "ludhiana" in text.lower():

                    link = (
                      f"https://t.me/{channel}/{message.id}"
                    )

                    telegram_cache[link] = {
                        "title": text[:80],
                        "content": text
                    }

                    links.append(link)


    with telegram_client:
        telegram_client.loop.run_until_complete(fetch())


    print(
       f"[Telegram] Found {len(links)} posts"
    )

    return links

telegram_cache={}


def telegram_extract(link):

    data = telegram_cache.get(link)

    if not data:
        return None


    return {

        "title": data["title"],

        "link": link,

        "content": data["content"],

        "source": "Telegram"

    }

# ==============================
# ALL SOURCES REGISTRY
# ==============================
SOURCES = [
    {"name": "Hindustan Times", "get_links": ht_get_links,      "extract": ht_extract},
    {"name": "The Tribune",     "get_links": tribune_get_links,  "extract": tribune_extract},
    {"name": "Times of India",  "get_links": toi_get_links,      "extract": toi_extract},
    {"name": "Jagran",          "get_links": jagran_get_links,   "extract": jagran_extract},
    {"name": "Punjab Kesari",   "get_links": pk_get_links,       "extract": pk_extract},
    {"name": "Bluesky",         "get_links": bluesky_get_links,  "extract": bluesky_extract},
    {"name": "Telegram",        "get_links": telegram_get_links,   "extract": telegram_extract},
    {"name": "Reddit",          "get_links": reddit_get_links,      "extract": reddit_extract},
    {"name": "X (Twitter)", "get_links": twitter_get_links, "extract": twitter_extract},
    

]

# ==============================
# MAIN SCRAPER
# ==============================
def scrape_all(limit_per_source=10):
    init_db()
    total = 0

    for source in SOURCES:
        print(f"\n{'─'*40}")
        print(f"  Scraping: {source['name']}")
        print(f"{'─'*40}")

        links = source["get_links"]()
        if not links:
            print(f"  No links found.")
            continue

        count = 0
        for link in links:
            if count >= limit_per_source:
                break
                
            # Skip if already in database (saves bandwidth and time)
            if check_link_exists(link):
                continue
                
            print(f"  [NEW](http://googleusercontent.com/map_location_reference/0)...")
            article = source["extract"](link)
            
            if article:
                insert_article(
                    title=article["title"],
                    link=article["link"],
                    content=article["content"],
                    source=article["source"]
                )
                count += 1
            time.sleep(DELAY)

        print(f"  ✅ Saved {count} new articles from {source['name']}")
        total += count

    print(f"\n🎉 Total new articles saved to DB: {total}")

if __name__ == "__main__":
    scrape_all(limit_per_source=10)