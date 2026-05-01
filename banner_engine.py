from PIL import Image, ImageDraw, ImageFont
import os
import requests
from io import BytesIO
from skill_icons import get_skill_icon

CANVAS_W = 1536
CANVAS_H = 768
LEFT_W   = 700
DIVIDER  = 680
FONT_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")

COLOR_THEMES = {
    "light_blue": {
        "bg_left": (247, 250, 255), "accent": (15, 90, 200), "accent2": (255, 140, 0),
        "text_h": (10, 25, 60), "text_b": (50, 70, 110), "divider": (200, 215, 240),
        "cta_bg": (15, 90, 200), "cta_txt": (255, 255, 255),
        "check": (15, 90, 200), "tag_bg": (225, 235, 255), "tag_txt": (15, 90, 200),
        "icon_colors": [(15,90,200),(255,140,0),(0,160,130),(180,30,80),(100,60,200)],
    },
    "corporate_blue": {
        "bg_left": (245, 248, 255), "accent": (10, 55, 170), "accent2": (255, 110, 0),
        "text_h": (5, 18, 55), "text_b": (45, 65, 115), "divider": (190, 210, 245),
        "cta_bg": (10, 55, 170), "cta_txt": (255, 255, 255),
        "check": (10, 55, 170), "tag_bg": (220, 232, 255), "tag_txt": (10, 55, 170),
        "icon_colors": [(10,55,170),(255,110,0),(0,150,120),(160,20,70),(80,50,190)],
    },
    "warm_orange": {
        "bg_left": (255, 251, 246), "accent": (210, 75, 15), "accent2": (240, 170, 0),
        "text_h": (40, 20, 5), "text_b": (90, 60, 35), "divider": (250, 210, 170),
        "cta_bg": (210, 75, 15), "cta_txt": (255, 255, 255),
        "check": (210, 75, 15), "tag_bg": (255, 235, 210), "tag_txt": (210, 75, 15),
        "icon_colors": [(210,75,15),(240,170,0),(0,140,110),(150,20,80),(80,60,200)],
    },
    "tech_dark": {
    "bg_left": (240, 245, 255), "accent": (30, 90, 220), "accent2": (0, 180, 160),
    "text_h": (10, 25, 70), "text_b": (50, 75, 140), "divider": (180, 200, 240),
    "cta_bg": (30, 90, 220), "cta_txt": (255, 255, 255),
    "check": (30, 90, 220), "tag_bg": (220, 232, 255), "tag_txt": (30, 90, 220),
    "icon_colors": [(30,90,220),(0,180,160),(255,130,0),(180,50,220),(40,170,100)],
    },
    "green_fresh": {
        "bg_left": (245, 255, 248), "accent": (15, 145, 80), "accent2": (0, 180, 160),
        "text_h": (5, 40, 20), "text_b": (40, 90, 60), "divider": (180, 235, 200),
        "cta_bg": (15, 145, 80), "cta_txt": (255, 255, 255),
        "check": (15, 145, 80), "tag_bg": (210, 245, 225), "tag_txt": (15, 145, 80),
        "icon_colors": [(15,145,80),(0,180,160),(255,140,0),(180,30,80),(60,100,200)],
    },
}

ICON_SHAPES = ["circle", "rounded_rect", "diamond", "hexagon", "triangle"]


def _load_font(name, size):
    path = os.path.join(FONT_DIR, name)
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    for fallback in [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if os.path.exists(fallback):
            try:
                return ImageFont.truetype(fallback, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap_text(text, font, max_width):
    dummy = Image.new("RGB", (1, 1))
    d = ImageDraw.Draw(dummy)
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = d.textbbox((0, 0), test, font=font)
        if bbox[2] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def _text_h(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def _draw_skill_icon(draw, shape_idx, x, y, size, color):
    """Draw a small decorative icon shape for skills."""
    s = size
    shape = ICON_SHAPES[shape_idx % len(ICON_SHAPES)]
    c = color

    if shape == "circle":
        draw.ellipse([x, y, x+s, y+s], fill=c)
        # inner white dot
        m = s // 3
        draw.ellipse([x+m, y+m, x+s-m, y+s-m], fill=(255,255,255,180))

    elif shape == "rounded_rect":
        draw.rounded_rectangle([x, y, x+s, y+s], radius=s//3, fill=c)
        # inner white line
        pw = max(1, s//6)
        draw.rectangle([x+pw*2, y+s//2-pw//2, x+s-pw*2, y+s//2+pw//2], fill=(255,255,255))

    elif shape == "diamond":
        cx, cy = x+s//2, y+s//2
        pts = [(cx, y), (x+s, cy), (cx, y+s), (x, cy)]
        draw.polygon(pts, fill=c)

    elif shape == "hexagon":
        import math
        cx, cy, r = x+s//2, y+s//2, s//2
        pts = [(int(cx + r*math.cos(math.radians(60*i-30))),
                int(cy + r*math.sin(math.radians(60*i-30)))) for i in range(6)]
        draw.polygon(pts, fill=c)

    elif shape == "triangle":
        pts = [(x+s//2, y), (x+s, y+s), (x, y+s)]
        draw.polygon(pts, fill=c)


def _draw_diagonal_divider(canvas, theme):
    overlay = Image.new("RGBA", canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    bg = theme["bg_left"]
    skew = 55
    pts = [(0,0),(DIVIDER+skew,0),(DIVIDER,CANVAS_H),(0,CANVAS_H)]
    draw.polygon(pts, fill=(*bg, 255))
    return Image.alpha_composite(canvas.convert("RGBA"), overlay)


def assemble_banner(bg_image, company_name, tagline, description,
                    skills, cta, nature, color_theme="light_blue", logo_image=None):

    theme = COLOR_THEMES.get(color_theme, COLOR_THEMES["light_blue"])
    icon_colors = theme["icon_colors"]

    # ── Canvas ──────────────────────────────────────────────────────
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (*theme["bg_left"], 255))

    # ── Right: background image ─────────────────────────────────────
    right_w = CANVAS_W - DIVIDER + 80
    bg_r = bg_image.resize((right_w, CANVAS_H), Image.LANCZOS).convert("RGBA")
    canvas.paste(bg_r, (DIVIDER - 40, 0))

    # ── Left zone solid ─────────────────────────────────────────────
    left_solid = Image.new("RGBA", (DIVIDER + 10, CANVAS_H), (*theme["bg_left"], 255))
    canvas.paste(left_solid, (0, 0))

    # ── Diagonal divider ────────────────────────────────────────────
    canvas = _draw_diagonal_divider(canvas, theme)
    draw = ImageDraw.Draw(canvas)

    # ── Fonts ────────────────────────────────────────────────────────
    f_name_lg  = _load_font("Poppins-Bold.ttf", 62)
    f_name_md  = _load_font("Poppins-Bold.ttf", 48)
    f_tag      = _load_font("Poppins-Bold.ttf", 30)
    f_desc     = _load_font("Poppins-Regular.ttf", 21)
    f_skill    = _load_font("Poppins-SemiBold.ttf", 20)
    f_nature   = _load_font("Poppins-Regular.ttf", 14)
    f_cta      = _load_font("Poppins-Bold.ttf", 20)
    f_pill     = _load_font("Poppins-SemiBold.ttf", 16)

    pad  = 48
    maxw = DIVIDER - pad - 30   # strict max text width — no overflow into right zone
    y    = 44

    # ── Company Logo (Clearbit) OR fallback dot ───────────────────────
    logo_h = 52
    if logo_image is not None and logo_image.size[0] >= 50:
        try:
            lw, lh = logo_image.size
            logo_h = 72                      # was 52 → bigger
            scale  = logo_h / lh
            logo_resized = logo_image.resize(
                (int(lw * scale), logo_h), Image.LANCZOS
            ).convert("RGBA")
            # Direct paste — no pill, banner bg already white
            canvas.paste(logo_resized, (pad, y), logo_resized)
            draw = ImageDraw.Draw(canvas)
            y += logo_h + 12
        except Exception:
            # Fallback dots
            draw.ellipse([pad, y + 18, pad + 16, y + 34], fill=theme["accent"])
            draw.ellipse([pad + 22, y + 22, pad + 32, y + 32], fill=theme["accent2"])
            y += 50
    else:
        
        y += 8

    # ── Company Name ─────────────────────────────────────────────────
    f_name = f_name_lg if len(company_name) <= 12 else f_name_md
    draw.text((pad, y), company_name.upper(), font=f_name, fill=theme["text_h"])
    bbox = draw.textbbox((pad, y), company_name.upper(), font=f_name)
    y = bbox[3] + 14    # bbox bottom + proper gap

    

    # ── Tagline (max 2 lines) ─────────────────────────────────────────
    tag_lines = _wrap_text(tagline, f_tag, maxw)
    for i, line in enumerate(tag_lines[:2]):
        col = theme["accent"] if i == 0 else theme["accent2"]
        draw.text((pad, y), line, font=f_tag, fill=col)
        y += _text_h(draw, line, f_tag) + 3
    y += 6

    # ── Description ───────────────────────────────────────────────────
    desc_lines = _wrap_text(description, f_desc, maxw)
    for line in desc_lines[:2]:
        draw.text((pad, y), line, font=f_desc, fill=theme["text_b"])
        y += _text_h(draw, line, f_desc) + 2
    y += 10

    # ── Divider line ─────────────────────────────────────────────────
    draw.rectangle([pad, y, pad + maxw, y+1], fill=theme["divider"])
    y += 14

    # ── Skills with ICONS ────────────────────────────────────────────
    icon_size = 30
    skill_gap = 42

    shown_skills   = skills[:4]
    overflow_skills = skills[4:]

    for i, skill in enumerate(shown_skills):
        ic = icon_colors[i % len(icon_colors)]

        # ── Try real devicon first ─────────────────────────────────
        real_icon = get_skill_icon(skill, size=icon_size)
        if real_icon:
            # White pill bg behind icon
            bg_icon = Image.new("RGBA", (icon_size + 4, icon_size + 4), (255, 255, 255, 180))
            canvas.paste(bg_icon, (pad - 2, y - 1), bg_icon)
            canvas.paste(real_icon, (pad, y + 1), real_icon)
            draw = ImageDraw.Draw(canvas)
        else:
            # Fallback to shape icon
            _draw_skill_icon(draw, i, pad, y + 1, icon_size, ic)

        # Skill text
        sx          = pad + icon_size + 10
        skill_maxw  = maxw - icon_size - 14
        skill_text  = skill
        while True:
            bbox = draw.textbbox((0, 0), skill_text, font=f_skill)
            if bbox[2] - bbox[0] <= skill_maxw or len(skill_text) < 5:
                break
            skill_text = skill_text[:-4] + "..."

        draw.text((sx, y + 3), skill_text, font=f_skill, fill=theme["text_h"])
        y += skill_gap

    y += 4

    # ── Extra skills as pills ────────────────────────────────────────
    if overflow_skills:
        tx = pad
        for skill in overflow_skills[:3]:
            f = f_pill
            bbox = draw.textbbox((0,0), skill, font=f)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            px, py = 10, 5
            rw = min(tw + px*2, maxw - tx + pad)
            if tx + rw > pad + maxw:
                break
            draw.rounded_rectangle([tx, y, tx+rw, y+th+py*2], radius=12, fill=theme["tag_bg"])
            draw.text((tx+px, y+py), skill, font=f, fill=theme["tag_txt"])
            tx += rw + 8
        y += th + py*2 + 8

    # ── Nature text (wrapped, clipped) ───────────────────────────────
    if nature:
        nat_text = f"Domain: {nature}"
        nat_lines = _wrap_text(nat_text, f_nature, maxw)
        for line in nat_lines[:2]:
            draw.text((pad, y), line, font=f_nature, fill=theme["text_b"])
            y += _text_h(draw, line, f_nature) + 2

    # ── CTA Bottom bar ───────────────────────────────────────────────
    cta_h  = 62
    cta_y  = CANVAS_H - cta_h
    bar_w  = DIVIDER + 20
    draw.rectangle([0, cta_y, bar_w, CANVAS_H], fill=theme["cta_bg"])

    # Accent strip at top of CTA
    draw.rectangle([0, cta_y, bar_w, cta_y+3], fill=theme["accent2"])

    cta_bbox = draw.textbbox((0,0), cta, font=f_cta)
    cta_th   = cta_bbox[3] - cta_bbox[1]
    cta_ty   = cta_y + (cta_h - cta_th) // 2
    draw.text((pad, cta_ty), cta, font=f_cta, fill=theme["cta_txt"])

    # Arrow icon (simple >)
    draw.text((pad + cta_bbox[2] - cta_bbox[0] + 16, cta_ty), ">", font=f_cta, fill=(*theme["cta_txt"][:3],))

    return canvas.convert("RGB").resize((CANVAS_W, CANVAS_H), Image.LANCZOS)