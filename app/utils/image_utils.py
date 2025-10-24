import os
from PIL import Image, ImageDraw, ImageFont
from .constants import AVATAR_SIZE

def make_rounded_avatar(img: Image.Image) -> Image.Image:
    img = img.resize((AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, AVATAR_SIZE, AVATAR_SIZE), fill=255)
    img.putalpha(mask)
    return img

def generate_letter_avatar(letter: str, bg_color=(100, 100, 200)) -> Image.Image:
    letter = letter[0].upper() if letter else "?"
    img = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), color=bg_color)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    w, h = draw.textbbox((0, 0), letter, font=font)[2:]
    draw.text(((AVATAR_SIZE - w) / 2, (AVATAR_SIZE - h) / 2), letter, fill="white", font=font)
    return make_rounded_avatar(img)
