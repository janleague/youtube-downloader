"""Uygulama için temiz YouTube tarzı PNG ve çok boyutlu ICO üretir."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]


def create_icon(size: int = 1024) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin_x = int(size * 0.075)
    margin_y = int(size * 0.22)
    body = (
        margin_x,
        margin_y,
        size - margin_x,
        size - margin_y,
    )
    radius = int(size * 0.16)
    draw.rounded_rectangle(body, radius=radius, fill=(255, 0, 0, 255))

    center_x = size * 0.52
    center_y = size * 0.50
    triangle_w = size * 0.29
    triangle_h = size * 0.34
    draw.polygon(
        [
            (center_x - triangle_w * 0.48, center_y - triangle_h * 0.5),
            (center_x - triangle_w * 0.48, center_y + triangle_h * 0.5),
            (center_x + triangle_w * 0.55, center_y),
        ],
        fill=(255, 255, 255, 255),
    )
    return image


def main():
    icon = create_icon()
    icon.save(ROOT / "app_icon.png", optimize=True)
    icon.save(
        ROOT / "app_icon.ico",
        format="ICO",
        sizes=[
            (16, 16), (24, 24), (32, 32), (48, 48),
            (64, 64), (128, 128), (256, 256),
        ],
    )

    avatar_path = ROOT / "assets" / "janleague-avatar.png"
    if avatar_path.exists():
        avatar = Image.open(avatar_path).convert("RGBA")
        side = min(avatar.size)
        left = (avatar.width - side) // 2
        top = (avatar.height - side) // 2
        avatar = avatar.crop((left, top, left + side, top + side)).resize(
            (256, 256), Image.Resampling.LANCZOS,
        )
        mask = Image.new("L", avatar.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 255, 255), fill=255)
        avatar.putalpha(mask)
        avatar.save(ROOT / "assets" / "janleague-avatar-round.png", optimize=True)

    print("Generated application icon and rounded profile avatar")


if __name__ == "__main__":
    main()
