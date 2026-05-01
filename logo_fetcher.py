# logo_fetcher.py — Fully dynamic logo fetcher (any company, no hardcoding)
import os, re, requests
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse, quote

LOGO_CACHE = os.path.join(os.path.dirname(__file__), "assets", "logos")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


# ═══════════════════════════════════════════════════
# STEP 1: Company ka domain auto-discover karo
# ═══════════════════════════════════════════════════

def _discover_domain(company_name: str) -> list[str]:
    """
    DuckDuckGo Instant Answers API se official domain dhundo.
    Phir common TLD guesses append karo as fallback.
    """
    slug  = re.sub(r"[^a-z0-9]", "", company_name.lower())   # "wns global" → "wnsglobal"
    slug2 = company_name.lower().strip().replace(" ", "-")    # "wns global" → "wns-global"
    found = []

    # ── DuckDuckGo Instant Answers (free, no key) ──────────────────
    try:
        ddg_url = (
            f"https://api.duckduckgo.com/?q={quote(company_name + ' company official site')}"
            f"&format=json&no_redirect=1&no_html=1"
        )
        r = requests.get(ddg_url, timeout=6, headers=HEADERS)
        data = r.json()

        for key in ["AbstractURL", "OfficialSite"]:
            val = data.get(key, "")
            if val:
                d = urlparse(val).netloc.replace("www.", "").strip()
                if d and "wikipedia" not in d and "duckduckgo" not in d:
                    found.append(d)

        # Infobox URLs
        for item in data.get("Infobox", {}).get("content", []):
            val = item.get("value", "")
            if val.startswith("http"):
                d = urlparse(val).netloc.replace("www.", "").strip()
                if d and "wikipedia" not in d:
                    found.append(d)

    except Exception as e:
        print(f"  DDG domain search failed: {e}")

    # ── Wikipedia API — company page → official URL ────────────────
    try:
        wiki_url = (
            f"https://en.wikipedia.org/api/rest_v1/page/summary/"
            f"{quote(company_name)}"
        )
        r = requests.get(wiki_url, timeout=6, headers=HEADERS)
        if r.status_code == 200:
            page = r.json()
            # Wikipedia infobox sometimes has website
            desc = page.get("extract", "")
            urls = re.findall(r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-z]{2,})', desc)
            for d in urls:
                if "wikipedia" not in d and "wikimedia" not in d:
                    found.append(d)
    except Exception:
        pass

    # ── Common TLD guesses ─────────────────────────────────────────
    skip_tlds = {"wikipedia.org", "linkedin.com", "facebook.com",
                 "twitter.com", "glassdoor.com", "indeed.com"}
    for tld in [".com", ".io", ".co", ".net", ".org", ".in", ".co.in"]:
        for s in [slug, slug2]:
            candidate = s + tld
            if candidate not in skip_tlds:
                found.append(candidate)

    # Deduplicate while preserving order
    return list(dict.fromkeys(found))


# ═══════════════════════════════════════════════════
# STEP 2: Domain se logo fetch karo (4 sources)
# ═══════════════════════════════════════════════════

def _try_clearbit(domain: str) -> Image.Image | None:
    try:
        r = requests.get(
            f"https://logo.clearbit.com/{domain}?size=200",
            timeout=6, headers=HEADERS
        )
        if r.status_code == 200 and "image" in r.headers.get("content-type", "") \
                and len(r.content) > 800:
            return Image.open(BytesIO(r.content)).convert("RGBA")
    except Exception:
        pass
    return None


def _try_brandfetch(domain: str) -> Image.Image | None:
    """Brandfetch CDN — free tier, no auth needed for many brands"""
    try:
        r = requests.get(
            f"https://cdn.brandfetch.io/{domain}/w/200/h/200",
            timeout=6, headers=HEADERS
        )
        if r.status_code == 200 and "image" in r.headers.get("content-type", "") \
                and len(r.content) > 800:
            return Image.open(BytesIO(r.content)).convert("RGBA")
    except Exception:
        pass
    return None


def _try_wikipedia_thumb(company_name: str) -> Image.Image | None:
    """Wikipedia page thumbnail — often the official company logo"""
    try:
        wiki_url = (
            f"https://en.wikipedia.org/api/rest_v1/page/summary/"
            f"{quote(company_name)}"
        )
        r = requests.get(wiki_url, timeout=6, headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            thumb = data.get("originalimage") or data.get("thumbnail")
            if thumb:
                img_url = thumb.get("source", "")
                if img_url:
                    r2 = requests.get(img_url, timeout=6, headers=HEADERS)
                    if r2.status_code == 200:
                        img = Image.open(BytesIO(r2.content)).convert("RGBA")
                        # Wikipedia thumbnails are sometimes photos, not logos.
                        # Accept only if roughly square (logo-like aspect ratio)
                        w, h = img.size
                        if 0.4 < w / h < 2.5:
                            return img
    except Exception:
        pass
    return None


def _try_google_favicon(domain: str) -> Image.Image | None:
    """Google S2 favicon — low quality but always works as last resort"""
    try:
        r = requests.get(
            f"https://www.google.com/s2/favicons?domain={domain}&sz=128",
            timeout=5, headers=HEADERS
        )
        if r.status_code == 200 and len(r.content) > 200:
            img = Image.open(BytesIO(r.content)).convert("RGBA")
            # Favicon too small / generic — only use if bigger than 32px
            if img.size[0] >= 64:
                return img
    except Exception:
        pass
    return None


# ═══════════════════════════════════════════════════
# MAIN PUBLIC FUNCTION
# ═══════════════════════════════════════════════════

def fetch_logo(company_name: str) -> Image.Image | None:
    os.makedirs(LOGO_CACHE, exist_ok=True)

    slug       = re.sub(r"[^a-z0-9]", "", company_name.lower())
    cache_path = os.path.join(LOGO_CACHE, f"{slug}.png")

    # ── Serve from cache ──────────────────────────────────────────
    if os.path.exists(cache_path):
        try:
            print(f"  ✓ Logo from cache: {slug}")
            return Image.open(cache_path).convert("RGBA")
        except Exception:
            os.remove(cache_path)

    # ── Discover domain ───────────────────────────────────────────
    print(f"  🔍 Searching domain for: {company_name}")
    domains = _discover_domain(company_name)
    print(f"  → Candidates: {domains[:5]}")

    # ── Try Wikipedia logo first (best quality for known companies) ─
    wiki_logo = _try_wikipedia_thumb(company_name)
    if wiki_logo:
        wiki_logo.save(cache_path)
        print(f"  ✓ Logo via Wikipedia: {company_name}")
        return wiki_logo

    # ── Try each domain with each source ──────────────────────────
    for domain in domains[:8]:   # max 8 domain candidates
        print(f"     trying: {domain}")

        for source_fn in [_try_clearbit, _try_brandfetch, _try_google_favicon]:
            img = source_fn(domain)
            if img:
                img.save(cache_path)
                print(f"  ✓ Logo found via {source_fn.__name__}: {domain}")
                return img

    print(f"  ✗ No logo found for: {company_name} — using None")
    return None