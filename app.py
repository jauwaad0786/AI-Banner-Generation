"""
app.py - Flask REST API for AI Banner Generator
Run: python app.py
Endpoints:
  POST /generate  → generate banner
  GET  /banners   → list generated banners
  GET  /banner/<filename> → serve banner image
"""

import os
import uuid
import time
from flask import Flask, request, jsonify, send_from_directory, render_template
from dotenv import load_dotenv
from PIL import Image
from logo_fetcher import fetch_logo

load_dotenv()

from gemini_client import get_banner_content
from imagen_client import generate_background_image
from banner_engine import assemble_banner

app = Flask(__name__)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")

from flask import Flask, request, jsonify, send_from_directory, render_template, Response, stream_with_context
import json as _json

@app.route("/generate", methods=["POST"])
def generate():
    data         = request.get_json()
    company_name = data.get("company_name", "").strip()
    about        = data.get("about", "").strip()
    nature       = data.get("nature", "").strip()
    skills_raw   = data.get("skills", "")

    if not company_name:
        return jsonify({"error": "company_name is required"}), 400

    if isinstance(skills_raw, str):
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    else:
        skills = [str(s).strip() for s in skills_raw if str(s).strip()]

    def run():
        def emit(event, payload):
            yield f"event: {event}\ndata: {_json.dumps(payload)}\n\n"

        try:
            yield from emit("status", {"msg": "🔍 Fetching company logo...", "step": 1})
            logo_image = fetch_logo(company_name)

            yield from emit("status", {"msg": "🧠 Gemini crafting tagline & theme...", "step": 2})
            content = get_banner_content(company_name, about, nature, skills)

            yield from emit("status", {"msg": "🎨 Imagen generating background...", "step": 3})
            bg_image = generate_background_image(content["imagen_prompt"], aspect="16:9")

            yield from emit("status", {"msg": "⚡ Assembling banner...", "step": 4})
            banner = assemble_banner(
                bg_image=bg_image,
                company_name=company_name,
                tagline=content["tagline"],
                description=content["description"],
                skills=skills,
                cta=content["cta"],
                nature=nature,
                color_theme=content["color_theme"],
                logo_image=logo_image,
            )

            import time
            filename = f"banner_{company_name.lower().replace(' ', '_')}_{int(time.time())}.png"
            out_path = os.path.join(OUTPUT_DIR, filename)
            banner.save(out_path, "PNG", quality=95)

            yield from emit("done", {
                "success": True,
                "filename": filename,
                "url": f"/banner/{filename}",
                "meta": {
                    "tagline": content["tagline"],
                    "description": content["description"],
                    "color_theme": content["color_theme"],
                    "cta": content["cta"],
                }
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield from emit("error", {"error": str(e)})

    return Response(
        stream_with_context(run()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.route("/banner/<filename>")
def serve_banner(filename):
    return send_from_directory(OUTPUT_DIR, filename)


@app.route("/banners")
def list_banners():
    files = sorted(
        [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".png")],
        key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)),
        reverse=True
    )
    return jsonify({"banners": [{"filename": f, "url": f"/banner/{f}"} for f in files]})


if __name__ == "__main__":
    print("Banner Generator API running on http://localhost:5000")
    app.run(debug=True, port=5000)
