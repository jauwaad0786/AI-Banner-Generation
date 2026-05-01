# gemini_client.py
from google import genai
import json, os, re, random


# ═══════════════════════════════════════════════════
# 20+ DOMAIN → SCENE LIBRARY
# ═══════════════════════════════════════════════════

DOMAIN_SCENES = {
    "bpo": [
        "Indian female agent with headset smiling in modern call center, shallow depth of field",
        "aerial view of massive call center floor with hundreds of agents, overhead shot",
        "close-up emotional connection between agent and customer, warm lighting portrait",
        "multicultural team of agents in glass-walled operations room with city skyline",
        "night shift call center with neon-lit screens, cinematic blue atmosphere",
    ],
    "marketing": [
        "creative director presenting bold campaign on massive LED screen, dramatic shadows",
        "digital marketing war room with real-time campaign dashboards, neon glow",
        "aerial view of brand launch event, confetti, crowd energy, drone shot",
        "designer working on brand identity surrounded by mood boards, golden hour",
        "social media analytics on futuristic curved screens, purple-blue ambient light",
    ],
    "it": [
        "software engineers in futuristic server room with holographic code projections",
        "pair programming session, dual monitors with complex code, cinematic close-up",
        "data center corridor with blue server rack lighting, long exposure camera",
        "AI developer surrounded by floating neural network visualizations",
        "devops team monitoring live deployment on wall-sized status boards",
    ],
    "software": [
        "developer with multiple ultrawide monitors showing code, dark theme, neon glow",
        "agile sprint board in modern tech office, post-its and energy, wide angle",
        "abstract code waterfall visualization, matrix-style green on dark",
        "software architect sketching microservices diagram on glass wall",
    ],
    "sales": [
        "sales team celebrating record quarter, confetti, high-energy boardroom",
        "executive handshake deal in minimalist glass office, golden sunset",
        "sales funnel holographic projection in modern office, wide cinematic",
        "global sales map projection in dark operations room, data overlays",
    ],
    "fintech": [
        "financial trading floor with curved 4K monitors, market data streams",
        "blockchain network visualization, glowing nodes, dark cinematic",
        "banker in glass skyscraper office with city financial district view below",
        "abstract gold and black financial data waves, luxury aesthetic",
        "digital payment visualization — coins transforming into glowing data",
    ],
    "finance": [
        "executive reviewing financial dashboard in luxury high-rise office, city below",
        "stock market data visualization, green and red candles, dramatic lighting",
        "modern bank interior with marble floor and digital displays",
        "financial analysts in high-tech trading room, multiple screens",
    ],
    "education": [
        "modern university lecture hall with interactive holographic display",
        "e-learning setup — student with laptop in beautiful natural light",
        "teacher and diverse students in futuristic STEM lab",
        "aerial view of university campus in golden hour light",
        "library corridor with warm wooden shelves, bokeh lights",
    ],
    "healthcare": [
        "doctor using AI diagnostic tablet in modern hospital corridor",
        "surgical team in bright operating room, overhead lighting drama",
        "medical researcher in lab with glowing samples, blue light",
        "telemedicine doctor on screen with patient, warm home lighting",
        "hospital lobby, glass architecture, calming blue and white palette",
    ],
    "logistics": [
        "aerial drone shot of massive logistics warehouse at night, orange forklifts",
        "supply chain control center with world map, shipment tracking screens",
        "cargo port at golden hour — cranes, containers, dramatic scale",
        "delivery fleet lined up in geometric formation, top-down shot",
    ],
    "retail": [
        "luxury retail store interior, minimalist design, golden product lighting",
        "e-commerce fulfillment center, conveyor belts, wide angle fast motion",
        "fashion brand campaign set — models, lights, creative chaos",
        "digital shopping experience — AR overlay on physical store, futuristic",
    ],
    "hr": [
        "diverse team in collaborative open office, natural light, greenery",
        "HR team conducting interview in modern glass conference room",
        "employee recognition event, warm celebration lighting, genuine emotion",
        "people analytics dashboard in modern HR operations center",
    ],
    "consulting": [
        "strategy consultants around glass table with holographic business model",
        "management consultants presenting transformation roadmap in boardroom",
        "business analyst with data visualization on curved screen wall",
        "executive coaching session in minimalist luxury office, city view",
    ],
    "legal": [
        "law library with warm wood tones and floor-to-ceiling books",
        "attorneys reviewing contracts in sleek modern office, dramatic shadows",
        "courtroom visualization with dramatic ceiling lighting",
        "legal tech — AI document review on ultrawide curved display",
    ],
    "real_estate": [
        "architect reviewing 3D building projection in minimalist design studio",
        "luxury penthouse with panoramic city view, golden hour",
        "drone aerial shot of premium residential development",
        "property tech platform visualization — city map with AR overlays",
    ],
    "manufacturing": [
        "futuristic smart factory with robotic arms and holographic QC displays",
        "precision machining close-up, sparks and controlled chaos, cinematic",
        "automotive assembly line in dark dramatic factory lighting",
        "engineer inspecting 3D printed components in modern R&D facility",
    ],
}

ARTISTIC_STYLES = [
    "cinematic wide-angle 35mm, shallow depth of field, anamorphic lens flare",
    "ultra-wide panoramic, architectural photography style, perfect symmetry",
    "close-up portrait composition, 85mm, f/1.4, bokeh background",
    "overhead bird's eye view, geometric patterns visible, drone photography",
    "dutch angle composition, dynamic tension, editorial style",
    "long exposure light trail photography, motion blur, professional",
    "high contrast noir with selective color accent, dramatic shadows",
    "documentary-style reportage photography, raw authentic moment",
]

LIGHTING_PRESETS = [
    "golden hour warm sunlight through floor-to-ceiling glass",
    "cool blue hour ambient — dusk exterior, interior glow",
    "dramatic single-source studio spotlight, deep shadows",
    "neon sign reflections, cyberpunk palette, wet surfaces",
    "soft north-facing natural daylight, fashion editorial quality",
    "cinematic orange-teal color grade, Hollywood blockbuster look",
    "high-key overexposed minimalist, pure white ambient",
    "bioluminescent blue-green lab glow, science fiction aesthetic",
]

QUALITY_SUFFIX = (
    "Ultra realistic 8K professional photography. "
    "Photorealistic render, no text, no logos, no letters, "
    "no watermarks, no signs. Pure visual storytelling."
)
DOMAIN_THEME_MAP = {
    "bpo":           "corporate_blue",
    "support":       "corporate_blue",
    "call center":   "corporate_blue",
    "it":            "tech_dark",
    "software":      "tech_dark",
    "technology":    "tech_dark",
    "cloud":         "tech_dark",
    "data":          "warm_orange",
    "analytics":     "warm_orange",
    "ai":            "tech_dark",
    "fintech":       "warm_orange",
    "finance":       "warm_orange",
    "banking":       "warm_orange",
    "insurance":     "warm_orange",
    "sales":         "warm_orange",
    "marketing":     "warm_orange",
    "education":     "green_fresh",
    "edtech":        "green_fresh",
    "healthcare":    "green_fresh",
    "wellness":      "green_fresh",
    "hr":            "green_fresh",
    "logistics":     "warm_orange",
    "retail":        "light_blue",
    "ecommerce":     "light_blue",
    "consulting":    "corporate_blue",
    "legal":         "corporate_blue",
    "manufacturing": "tech_dark",
    "real estate":   "warm_orange",
}

def _pick_theme(nature: str, about: str, skills: list = None) -> str:
    skills_str = " ".join(skills or [])
    text = (nature + " " + about + " " + skills_str).lower()
    for keyword, theme in DOMAIN_THEME_MAP.items():
        if keyword in text:
            return theme
    return random.choice(["light_blue", "corporate_blue", "warm_orange", "tech_dark", "green_fresh"])

def _build_imagen_prompt(nature: str, company_name: str) -> str:
    """Build a richly varied, domain-specific Imagen prompt entirely locally."""
    n = nature.lower()

    # Domain matching — pick best scene library
    scene_list = None
    for key, scenes in DOMAIN_SCENES.items():
        if key in n:
            scene_list = scenes
            break

    # Fallback: abstract or generic corporate
    if not scene_list:
        scene_list = [
            "modern global headquarters exterior, glass architecture, dramatic sky",
            "executive boardroom with panoramic city view, powerful composition",
            "abstract data visualization sculpture in corporate lobby",
            "innovation lab with open collaboration spaces and greenery",
        ]

    scene       = random.choice(scene_list)
    art_style   = random.choice(ARTISTIC_STYLES)
    lighting    = random.choice(LIGHTING_PRESETS)

    # 25% chance of pure abstract / concept art instead of realistic scene
    

    return (
        f"Professional corporate business environment. "
        f"Scene: {scene}. "
        f"Include real professionals (men/women) working naturally in office environment. "
        f"Modern workplace with laptops, meetings, teamwork, realistic human interaction. "
        f"No abstract visuals, no artistic shapes, no concept art. "
        f"Only real-world business scenarios. "
        f"Camera: {art_style}. "
        f"Lighting: {lighting}. "
        f"{QUALITY_SUFFIX}"
    )


def get_banner_content(
    company_name: str, about: str, nature: str,
    skills: list[str]
) -> dict:

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    skills_str = ", ".join(skills)

    # ── Gemini only returns TEXT fields (not imagen_prompt) ─────────
    prompt = f"""
You are a professional AI prompt engineer and branding expert.

Analyze the company details and generate a premium banner content.

Company Name: {company_name}
About: {about}
Industry/Nature: {nature}
Skills/Services: {skills}

Tasks:
1. Create a strong professional tagline (5-8 words)
2. Create a short description (max 12 words)
3. Create a powerful CTA (3-6 words)
4. Select best visual theme
5. Generate a HIGH-QUALITY Imagen prompt

STRICT RULES:
- No generic outputs
- No repetition
- Make it corporate, modern, realistic
- Avoid abstract or artistic scenes

Return ONLY JSON:

{{
  "tagline": "...",
  "description": "...",
  "cta": "...",
  "color_theme": "corporate_blue | tech_dark | warm_orange | green_fresh",
  "imagen_prompt": "A professional corporate environment showing {nature} industry, real employees working, modern office, realistic lighting, depth, teamwork, no abstract, no artistic visuals, ultra realistic, 8k"
}}
"""
    for attempt in range(3):
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config={"max_output_tokens": 4000, "temperature": 0.9},
        )

        # Debug: reason kya hai
        raw = None
        try:
            raw = response.text
        except Exception:
            pass

        if not raw:
            # Candidate se manually extract karo
            try:
                raw = response.candidates[0].content.parts[0].text
            except Exception:
                pass

        if not raw:
            reason = "unknown"
            try:
                reason = str(response.candidates[0].finish_reason)
            except Exception:
                pass
            print(f"  ⚠ Gemini None (reason={reason}), retry {attempt+1}/3...")
            # Safety block hai to prompt thoda soften karo
            prompt = prompt.replace("creative director", "marketing expert")
            continue

        break
    else:
        raise RuntimeError("Gemini blocked after 3 retries — check API key/quota")

    raw = raw.strip()

    
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```", "", raw)
    

    result = json.loads(raw.strip())

    # ── Theme locally assigned (not Gemini) ──
    result["color_theme"] = _pick_theme(nature, about, skills)

    # ── Build imagen_prompt locally ──
    result["imagen_prompt"] = _build_imagen_prompt(nature, company_name)

    return result