import os
import base64
import requests
from PIL import Image
from io import BytesIO
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import random

def generate_variations(prompt):
    styles = [
        "cinematic ultra realistic",
        "high-end luxury photography",
        "futuristic tech aesthetic",
        "minimal clean corporate",
        "dark dramatic lighting",
        "vibrant modern style",
    ]

    angles = [
        "wide angle shot",
        "close-up shot",
        "top-down view",
        "over-the-shoulder view",
        "isometric perspective",
    ]

    variations = []

    for _ in range(4):  # 4 different prompts
        v = f"{prompt}, {random.choice(styles)}, {random.choice(angles)}, strong depth, professional composition"
        variations.append({"prompt": v})

    return variations

def _get_access_token() -> str:
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    credentials = service_account.Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token


def generate_background_image(prompt: str, aspect: str = "16:9") -> Image.Image:
    """
    Generate ONLY a background/scene image using Imagen.
    The prompt must NOT contain text instructions - no typography will be rendered here.
    All text will be added separately by banner_engine.py using Pillow.
    """
    project_id = os.getenv("PROJECT_ID")
    location = os.getenv("LOCATION", "us-central1")

    access_token = _get_access_token()

    url = (
        f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}"
        f"/locations/{location}/publishers/google/models/imagen-3.0-generate-002:predict"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    enforced_prompt = (
        prompt +
        ". ultra realistic corporate photography, real people, professional office environment, "
        "no abstract shapes, no 3D art, no concept art, no glowing particles, "
        "natural lighting, cinematic composition, depth of field"
    )
    style_boost = random.choice([
    "modern corporate office",
    "business meeting environment",
    "team collaboration workspace",
    "professional workplace setting",
    "enterprise office environment",
])
    enforced_prompt += f", {style_boost}"

    

    body = {
        "instances": [{"prompt": enforced_prompt}],
        "parameters": {
            "sampleCount": 4,
            "aspectRatio": aspect,
            "enhancePrompt": True,
        }
    }



    response = requests.post(url, headers=headers, json=body, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(f"Imagen API error {response.status_code}: {response.text}")

    result = response.json()
    preds = result["predictions"]
    choice = random.choice(preds)
    image_b64 = choice["bytesBase64Encoded"]

    return Image.open(BytesIO(base64.b64decode(image_b64))).convert("RGBA")
