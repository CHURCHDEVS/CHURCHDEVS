#!/usr/bin/env python3
"""Genera la foto de perfil y la portada del perfil de GitHub de CHURCHDEVS.

Uso:  uv run --with pillow --with fonttools --with brotli python -I herramientas/generar_imagenes.py RUTA_VOZ_BARRIO
Salida: assets/avatar.png (1000×1000) y assets/portada.png (1600×500).
La portada dibuja los 56 barrios reales de Ciénaga con su color (datos de Voz de Barrio, propios).
"""
import io
import json
import re
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
VB = Path(sys.argv[1]).resolve()
SALIDA = RAIZ / "assets"
SALIDA.mkdir(exist_ok=True)

NOCHE, TEAL_HONDO, TEAL, SOL, ARENA = "#052A30", "#073A42", "#0C7B8A", "#F7A825", "#FBF6EC"


def fuente(woff2: Path, peso: int, tam: int) -> ImageFont.FreeTypeFont:
    """WOFF2 variable → TTF en memoria, con el peso pedido."""
    f = TTFont(str(woff2))
    f.flavor = None
    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    letra = ImageFont.truetype(buf, tam)
    try:
        letra.set_variation_by_axes([peso])
    except OSError:
        pass
    return letra


BALOO = VB / "web/fonts/baloo-2-latin-wght-normal.woff2"
NUNITO = VB / "web/fonts/nunito-latin-wght-normal.woff2"


def barrios() -> tuple[list[tuple[str, list[tuple[float, float]]]], tuple[int, int]]:
    lite = json.loads((VB / "web/datos/barrios-lite.json").read_text(encoding="utf-8"))
    figuras = []
    for b in lite["barrios"]:
        x = y = 0.0
        puntos: list[tuple[float, float]] = []
        for cmd, cuerpo in re.findall(r"([MmLlHhVvZz])([^MmLlHhVvZz]*)", b["p"]):
            n = [float(v) for v in re.findall(r"-?\d+\.?\d*", cuerpo)]
            if cmd in "MmLl":
                for i in range(0, len(n) - 1, 2):
                    if cmd.islower() and (puntos or cmd == "l"):
                        x, y = x + n[i], y + n[i + 1]
                    else:
                        x, y = n[i], n[i + 1]
                    puntos.append((x, y))
            elif cmd in "Hh":
                for v in n:
                    x = x + v if cmd == "h" else v
                    puntos.append((x, y))
            elif cmd in "Vv":
                for v in n:
                    y = y + v if cmd == "v" else v
                    puntos.append((x, y))
        if len(puntos) >= 3:
            figuras.append((b["k"], puntos))
    return figuras, (lite["viewBox"][2], lite["viewBox"][3])


def mapa(alto: int) -> Image.Image:
    """Los 56 barrios en su color, con borde noche, sobre fondo transparente."""
    figuras, (ancho_vb, alto_vb) = barrios()
    escala = alto / alto_vb
    sobre = 3
    lienzo = Image.new("RGBA", (int(ancho_vb * escala * sobre), int(alto * sobre)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lienzo)
    for color, puntos in figuras:
        d.polygon([(px * escala * sobre, py * escala * sobre) for px, py in puntos],
                  fill=color, outline=NOCHE, width=2 * sobre)
    return lienzo.resize((int(ancho_vb * escala), alto), Image.LANCZOS)


def fondo(ancho: int, alto: int) -> Image.Image:
    """Noche con un resplandor teal arriba a la derecha (como la marca)."""
    base = Image.new("RGB", (ancho, alto), NOCHE)
    luz = Image.new("L", (ancho, alto), 0)
    ImageDraw.Draw(luz).ellipse((ancho * 0.45, -alto * 0.9, ancho * 1.4, alto * 0.9), fill=150)
    luz = luz.filter(ImageFilter.GaussianBlur(alto * 0.35))
    return Image.composite(Image.new("RGB", (ancho, alto), TEAL), base, luz)


def portada() -> None:
    ancho, alto = 1600, 500
    img = fondo(ancho, alto).convert("RGBA")
    m = mapa(440)
    sombra = Image.new("RGBA", m.size, (0, 0, 0, 0))
    sombra.putalpha(m.getchannel("A").point(lambda a: 110 if a else 0))
    sombra = sombra.filter(ImageFilter.GaussianBlur(14))
    x = ancho - m.width - 70
    img.alpha_composite(sombra, (x + 10, 40))
    img.alpha_composite(m, (x, 30))
    d = ImageDraw.Draw(img)
    d.text((90, 120), "CHURCHDEVS", font=fuente(BALOO, 800, 118), fill=ARENA)
    d.text((94, 262), "Software con propósito para territorios reales", font=fuente(NUNITO, 700, 40), fill="#CFE7EA")
    d.text((94, 322), "Plataformas cívicas · mapas y 3D en la web · datos abiertos",
           font=fuente(NUNITO, 600, 30), fill="#9CC9CF")
    d.ellipse((94, 398, 112, 416), fill=SOL)
    d.text((126, 388), "Ciénaga · Magdalena · Colombia", font=fuente(NUNITO, 800, 30), fill=SOL)
    img.convert("RGB").save(SALIDA / "portada.png", optimize=True)


def avatar() -> None:
    lado = 1000
    img = fondo(lado, lado).convert("RGBA")
    m = mapa(760)
    capa = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    capa.alpha_composite(m, ((lado - m.width) // 2, (lado - m.height) // 2 + 10))
    # el mapa queda de fondo, apagado, para que el monograma mande
    capa.putalpha(capa.getchannel("A").point(lambda a: int(a * 0.42)))
    img.alpha_composite(capa)
    d = ImageDraw.Draw(img)
    letra = fuente(BALOO, 800, 470)
    caja = d.textbbox((0, 0), "CD", font=letra)
    tx = (lado - (caja[2] - caja[0])) // 2 - caja[0]
    ty = (lado - (caja[3] - caja[1])) // 2 - caja[1] - 20
    d.text((tx + 8, ty + 10), "CD", font=letra, fill=(2, 22, 26, 200))
    d.text((tx, ty), "CD", font=letra, fill=ARENA)
    abajo = ty + caja[3] + 46          # el punto sol va DEBAJO del monograma, centrado
    d.ellipse((lado // 2 - 24, abajo, lado // 2 + 24, abajo + 48), fill=SOL)
    img.convert("RGB").save(SALIDA / "avatar.png", optimize=True)


if __name__ == "__main__":
    portada()
    avatar()
    for f in ("portada.png", "avatar.png"):
        print(f, (SALIDA / f).stat().st_size // 1024, "KB")
