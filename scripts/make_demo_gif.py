"""Assemble le GIF de démonstration du README à partir de captures de l'interface.

    uv run python scripts/make_demo_gif.py capture1.jpg capture2.jpg ... --out docs/demo.gif

Chaque capture est recadrée sur l'interface, reçoit une légende, et reste affichée le temps de la lire.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CROP = (60, 0, 580, 460)  # la zone de l'interface dans les captures (800 x 608)
CAPTION_HEIGHT = 44
STEPS = [  # (légende, durée d'affichage en millisecondes)
    ("Une question sur les guides de l'ANSSI", 1500),
    ("Une question sur les guides de l'ANSSI", 1800),
    ("Recherche dans les 45 guides…", 1200),
    ("Réponse citée : guide, page, passage exact", 4500),
    ("Hors des guides : « je ne sais pas », sans inventer", 3000),
    ("Tentative d'injection de prompt : refusée", 3500),
]


def caption_font(size: int) -> ImageFont.ImageFont:
    for name in ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def frame(path: Path, caption: str) -> Image.Image:
    shot = Image.open(path).convert("RGB").crop(CROP)
    canvas = Image.new("RGB", (shot.width, shot.height + CAPTION_HEIGHT), "white")
    canvas.paste(shot, (0, CAPTION_HEIGHT))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, canvas.width, CAPTION_HEIGHT), fill=(30, 41, 59))
    draw.text((16, 11), caption, fill="white", font=caption_font(18))
    return canvas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("captures", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=Path("docs/demo.gif"))
    args = parser.parse_args()
    if len(args.captures) != len(STEPS):
        raise SystemExit(f"il faut {len(STEPS)} captures, une par étape")

    frames = [frame(p, caption) for p, (caption, _) in zip(args.captures, STEPS, strict=True)]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        args.out,
        save_all=True,
        append_images=frames[1:],
        duration=[ms for _, ms in STEPS],
        loop=0,  # rejouer sans fin
        optimize=True,
    )
    print(f"{args.out} : {len(frames)} images, {args.out.stat().st_size / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
