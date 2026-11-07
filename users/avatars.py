from io import BytesIO
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont


def generate_avatar(name):
    image = Image.new("RGB", (256, 256), "#DCE6F0")
    draw = ImageDraw.Draw(image)

    font_path = (
        settings.BASE_DIR
        / "static"
        / "fonts"
        / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
    )
    font = ImageFont.truetype(str(font_path), size=140)

    letter = name.strip()[0].upper()
    left, top, right, bottom = draw.textbbox((0, 0), letter, font=font)

    x = (256 - (right - left)) / 2 - left
    y = (256 - (bottom - top)) / 2 - top
    draw.text((x, y), letter, font=font, fill="#24364B")

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return ContentFile(
        buffer.getvalue(),
        name=f"avatar_{uuid4().hex}.png",
    )