"""
setup_fonts.py
Run once to download Poppins fonts for the banner engine.
Usage: python setup_fonts.py
"""

import os
import urllib.request

FONTS = {
    "Poppins-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "Poppins-SemiBold.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf",
    "Poppins-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf",
    "Poppins-Medium.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Medium.ttf",
}

font_dir = os.path.join(os.path.dirname(__file__), "assets", "fonts")
os.makedirs(font_dir, exist_ok=True)

print("Downloading Poppins fonts...")
for name, url in FONTS.items():
    path = os.path.join(font_dir, name)
    if os.path.exists(path):
        print(f"  ✓ {name} (already exists)")
        continue
    print(f"  ↓ Downloading {name}...")
    try:
        urllib.request.urlretrieve(url, path)
        print(f"  ✓ {name}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")

print("\nAll fonts ready! Now run: python app.py")
