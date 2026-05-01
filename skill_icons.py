# skill_icons.py — Devicon CDN se real tech icons fetch karo
import os, requests
from PIL import Image
from io import BytesIO

ICON_CACHE = os.path.join(os.path.dirname(__file__), "assets", "skill_icons")

# skill keyword → devicon name
SKILL_MAP = {
    "python": "python", "java": "java", "javascript": "javascript",
    "js": "javascript", "typescript": "typescript", "ts": "typescript",
    "react": "react", "angular": "angularjs", "vue": "vuejs",
    "nodejs": "nodejs", "node": "nodejs", "node.js": "nodejs",
    "html": "html5", "css": "css3",
    "sql": "postgresql", "mysql": "mysql", "postgresql": "postgresql",
    "postgres": "postgresql", "mongodb": "mongodb", "redis": "redis",
    "docker": "docker", "kubernetes": "kubernetes", "k8s": "kubernetes",
    "aws": "amazonwebservices", "azure": "azure", "gcp": "googlecloud",
    "google cloud": "googlecloud", "terraform": "terraform",
    "tensorflow": "tensorflow", "pytorch": "pytorch",
    "git": "git", "github": "github", "linux": "linux",
    "php": "php", "ruby": "ruby", "go": "go", "golang": "go",
    "rust": "rust", "swift": "swift", "kotlin": "kotlin",
    "flutter": "flutter", "android": "android",
    "figma": "figma", "sketch": "sketch", "xd": "xd",
    "jira": "jira", "confluence": "confluence",
    "salesforce": "salesforce", "sap": "sap",
    "hadoop": "hadoop", "spark": "apachespark",
    "tableau": "tableau", "grafana": "grafana",
    "nginx": "nginx", "apache": "apache",
    "selenium": "selenium", "jenkins": "jenkins",
    "ansible": "ansible",
    # BPO/Business skills → fallback to custom drawn (return None)
}

def get_skill_icon(skill_name: str, size: int = 24) -> Image.Image | None:
    os.makedirs(ICON_CACHE, exist_ok=True)
    key = skill_name.lower().strip()

    # Exact match
    devicon = SKILL_MAP.get(key)

    # Partial match
    if not devicon:
        for k, v in SKILL_MAP.items():
            if k in key:
                devicon = v
                break

    if not devicon:
        return None

    cache_path = os.path.join(ICON_CACHE, f"{devicon}.png")
    if os.path.exists(cache_path):
        try:
            img = Image.open(cache_path).convert("RGBA")
            return img.resize((size, size), Image.LANCZOS)
        except Exception:
            pass

    # Try devicon CDN variants
    for variant in ["original", "plain", "original-wordmark"]:
        try:
            url = (
                f"https://cdn.jsdelivr.net/gh/devicons/devicon@latest"
                f"/icons/{devicon}/{devicon}-{variant}.png"
            )
            r = requests.get(url, timeout=6)
            if r.status_code == 200 and len(r.content) > 200:
                img = Image.open(BytesIO(r.content)).convert("RGBA")
                img.save(cache_path)
                return img.resize((size, size), Image.LANCZOS)
        except Exception:
            continue

    return None