"""Genera build/icon.ico para CajaPDF (documento PDF con esquina doblada)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


def make(size: int) -> Image.Image:
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Fondo redondeado teal
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.22), fill=(22, 160, 133, 255))

    # Documento blanco
    m = int(s * 0.26)
    doc = [m, int(s * 0.20), s - m, s - int(s * 0.16)]
    fold = int(s * 0.16)
    white = (255, 255, 255, 255)
    # cuerpo con esquina superior derecha doblada
    body = [doc[0], doc[1], doc[2], doc[3]]
    d.rounded_rectangle(body, radius=int(s * 0.03), fill=white)
    # esquina doblada
    d.polygon([(doc[2] - fold, doc[1]), (doc[2], doc[1] + fold), (doc[2] - fold, doc[1] + fold)],
              fill=(210, 225, 222, 255))
    d.polygon([(doc[2] - fold, doc[1]), (doc[2], doc[1]), (doc[2], doc[1] + fold)],
              fill=(22, 160, 133, 0))

    # Badge "PDF" rojo
    bh = int(s * 0.18)
    bw = int(s * 0.42)
    bx0 = doc[0] + int(s * 0.04)
    by1 = doc[3] - int(s * 0.06)
    d.rounded_rectangle([bx0, by1 - bh, bx0 + bw, by1], radius=int(s * 0.025),
                        fill=(230, 70, 60, 255))
    try:
        from PIL import ImageFont
        font = None
        for f in (r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"):
            if Path(f).is_file():
                font = ImageFont.truetype(f, int(bh * 0.62)); break
        if font:
            tb = d.textbbox((0, 0), "PDF", font=font)
            tw, th = tb[2] - tb[0], tb[3] - tb[1]
            d.text((bx0 + (bw - tw) / 2 - tb[0], by1 - bh + (bh - th) / 2 - tb[1]),
                   "PDF", fill=white, font=font)
    except Exception:  # noqa: BLE001
        pass

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    out = Path(__file__).with_name("icon.ico")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [make(sz) for sz in sizes]
    imgs[-1].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=imgs[:-1])
    make(256).save(Path(__file__).with_name("icon_preview.png"))
    print("Icono generado:", out)


if __name__ == "__main__":
    main()
