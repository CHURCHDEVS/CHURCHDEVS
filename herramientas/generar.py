#!/usr/bin/env python3
"""Genera la identidad del perfil de GitHub de CHURCHDEVS.

Uso:  uv run --with fonttools --with brotli --with pillow python -I herramientas/generar.py
Salida: assets/portada.svg (cabecera animada) y assets/avatar.png (foto de perfil, 1000×1000).

Concepto «la curva»: la curva de animación con la que se mueve una interfaz bien hecha, dibujada
como en un editor (anclas y manijas), y el punto amarillo del avatar recorriéndola con esa misma
curva. Una sola fuente, Archivo (OFL, herramientas/fuentes/), convertida a trazos: GitHub muestra
los SVG como imagen y no carga fuentes. Entrada de ~1,5 s; después solo el recorrido del punto
cada 4,2 s. Con «reducir movimiento» no se mueve nada y se ve el estado final.
"""
import io
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / "herramientas/fuentes/archivo-latin-wdth-normal.woff2"

# Paleta: cobalto y amarillo señal
FONDO, LUZ, HUESO, CIELO, SENAL = "#0E1A5C", "#2440C4", "#F4F2EC", "#B4C6FF", "#FFC93C"
CURVA, ENFASIS = "cubic-bezier(.2,0,0,1)", "cubic-bezier(.05,.7,.1,1)"
P1, P2 = (0.05, 0.7), (0.1, 1.0)  # la curva que se dibuja es la misma ENFASIS


def fuente(peso: int, ancho: int) -> TTFont:
    return instancer.instantiateVariableFont(TTFont(str(ARCHIVO)), {"wght": peso, "wdth": ancho})


NOMBRE_F, ROL_F, FRASE_F = fuente(800, 62), fuente(600, 100), fuente(500, 100)


def ancho(f: TTFont, texto: str, tam: float) -> float:
    gs, cmap, upm = f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm
    return sum(gs[cmap[ord(c)]].width for c in texto if ord(c) in cmap) * tam / upm


def trazo(f: TTFont, texto: str, x: float, y: float, tam: float) -> str:
    """Texto → atributo d de un <path>, con la línea base en y."""
    gs, cmap, upm = f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm
    s, cx, partes = tam / upm, x, []
    for c in texto:
        g = cmap.get(ord(c))
        if g is None:
            continue
        pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
        partes.append(pen.getCommands())
        cx += gs[g].width * s
    return " ".join(p for p in partes if p)


def estilo(lado: int) -> str:
    return f"""<style>
@keyframes sube{{from{{opacity:0;transform:translateY(14px)}}}}
@keyframes aparece{{from{{opacity:0}}}}
@keyframes traza{{from{{stroke-dashoffset:1}}}}
@keyframes manija{{from{{opacity:0;transform:scale(.2)}}}}
@keyframes avanza{{0%{{transform:translateX(0);animation-timing-function:linear}}45%,100%{{transform:translateX({lado}px)}}}}
@keyframes sube_y{{0%{{transform:translateY(0);animation-timing-function:{ENFASIS}}}45%,100%{{transform:translateY(-{lado}px)}}}}
@keyframes asoma{{0%{{opacity:0}}5%,82%{{opacity:1}}94%,100%{{opacity:0}}}}
.t{{animation:sube .44s {CURVA} both}}
.n{{animation:sube .6s {ENFASIS} .12s both}}
.r{{animation:aparece .5s {CURVA} both}}
.h{{transform-box:fill-box;transform-origin:center;animation:manija .44s {CURVA} both}}
.l{{stroke-dasharray:1;stroke-dashoffset:0;animation:traza .7s {CURVA} .75s both}}
.bx{{transform:translateX({lado}px);animation:avanza 4.2s 1.6s infinite both}}
.by{{transform:translateY(-{lado}px);animation:sube_y 4.2s 1.6s infinite both}}
.b{{animation:asoma 4.2s linear 1.6s infinite both}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>"""


def portada() -> str:
    w, h, x0 = 1000, 380, 52
    # el lienzo de la curva: un cuadrado con su cuadrícula, a la derecha
    lado, gx, gy = 260, 680, 60
    base_y = gy + lado
    a0, a1 = (gx, base_y), (gx + lado, gy)
    m1 = (gx + P1[0] * lado, base_y - P1[1] * lado)
    m2 = (gx + P2[0] * lado, base_y - P2[1] * lado)
    paso = lado / 5
    rejilla = "".join(
        f'<path d="M{gx + i * paso:.1f} {gy}V{base_y}M{gx} {gy + i * paso:.1f}H{gx + lado}"/>' for i in range(6))
    curva = f"M{a0[0]} {a0[1]} C{m1[0]:.1f} {m1[1]:.1f} {m2[0]:.1f} {m2[1]:.1f} {a1[0]} {a1[1]}"

    def manija(ancla, punta, retraso):
        return (f'<g class="h" style="animation-delay:{retraso}s">'
                f'<path d="M{ancla[0]:.1f} {ancla[1]:.1f}L{punta[0]:.1f} {punta[1]:.1f}" stroke="{CIELO}" stroke-width="2"/>'
                f'<circle cx="{punta[0]:.1f}" cy="{punta[1]:.1f}" r="7" fill="{FONDO}" stroke="{CIELO}" stroke-width="2.5"/></g>')

    def ancla(p, retraso):
        return (f'<rect class="h" style="animation-delay:{retraso}s" x="{p[0] - 8}" y="{p[1] - 8}" width="16" height="16" '
                f'rx="3" fill="{HUESO}"/>')

    nombre_tam = 118
    while ancho(NOMBRE_F, "CHURCHDEVS", nombre_tam) > 560:
        nombre_tam -= 2
    frase_tam = 28
    lineas = ["Enfocado en IA, automatización,", "ingeniería de datos y sistemas inteligentes."]
    while max(ancho(FRASE_F, linea, frase_tam) for linea in lineas) > 590:
        frase_tam -= 1
    alt = ("CHURCHDEVS, desarrollador web creativo: software enfocado en IA, automatización, "
           "ingeniería de datos y sistemas inteligentes")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
        f'aria-label="{alt}"><title>{alt}</title>{estilo(lado)}'
        f'<defs><radialGradient id="luz" cx="88%" cy="-8%" r="80%"><stop offset="0" stop-color="{LUZ}"/>'
        f'<stop offset="1" stop-color="{FONDO}" stop-opacity="0"/></radialGradient></defs>'
        f'<rect width="{w}" height="{h}" rx="20" fill="{FONDO}"/><rect width="{w}" height="{h}" rx="20" fill="url(#luz)"/>'
        f'<g class="r" fill="none" stroke="{CIELO}" stroke-opacity=".16" stroke-width="1">{rejilla}</g>'
        f'{manija(a0, m1, .45)}{manija(a1, m2, .55)}'
        f'<path class="l" pathLength="1" d="{curva}" fill="none" stroke="{HUESO}" stroke-width="4" stroke-linecap="round"/>'
        f'{ancla(a0, .35)}{ancla(a1, .4)}'
        f'<g class="bx"><g class="by"><circle class="b" cx="{a0[0]}" cy="{a0[1]}" r="13" fill="{SENAL}" '
        f'stroke="{FONDO}" stroke-width="4"/></g></g>'
        f'<path class="t" style="animation-delay:.05s" fill="{CIELO}" d="{trazo(ROL_F, "Desarrollador web creativo", x0, 98, 25)}"/>'
        f'<path class="n" fill="{HUESO}" d="{trazo(NOMBRE_F, "CHURCHDEVS", x0 - 3, 204, nombre_tam)}"/>'
        f'<path class="t" style="animation-delay:.3s" fill="{HUESO}" d="{trazo(FRASE_F, lineas[0], x0, 262, frase_tam)}"/>'
        f'<path class="t" style="animation-delay:.36s" fill="{HUESO}" d="{trazo(FRASE_F, lineas[1], x0, 300, frase_tam)}"/>'
        f'</svg>')


def letra_png(peso: int, ancho_eje: int, tam: int) -> ImageFont.FreeTypeFont:
    f = instancer.instantiateVariableFont(TTFont(str(ARCHIVO)), {"wght": peso, "wdth": ancho_eje})
    f.flavor = None
    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, tam)


def avatar() -> Image.Image:
    """Monograma CD con el punto amarillo; pensado para el recorte circular de GitHub."""
    lado = 1000
    img = Image.new("RGB", (lado, lado), FONDO)
    luz = Image.new("L", (lado, lado), 0)
    ImageDraw.Draw(luz).ellipse((lado * 0.35, -lado * 0.55, lado * 1.35, lado * 0.6), fill=190)
    luz = luz.filter(ImageFilter.GaussianBlur(lado * 0.18))
    img = Image.composite(Image.new("RGB", (lado, lado), LUZ), img, luz)
    d = ImageDraw.Draw(img)
    letra = letra_png(800, 72, 560)
    caja = d.textbbox((0, 0), "CD", font=letra)
    tw, th = caja[2] - caja[0], caja[3] - caja[1]
    punto = 64
    tx = (lado - (tw + 22 + punto)) // 2 - caja[0]
    ty = (lado - th) // 2 - caja[1] - 10
    d.text((tx, ty), "CD", font=letra, fill=HUESO)
    px, py = tx + caja[2] + 22, ty + caja[3] - punto  # el punto se apoya en la línea base, tras la D
    d.ellipse((px, py, px + punto, py + punto), fill=SENAL)
    return img


def main() -> None:
    (RAIZ / "assets").mkdir(exist_ok=True)
    svg = portada()
    (RAIZ / "assets/portada.svg").write_text(svg, encoding="utf-8")
    avatar().save(RAIZ / "assets/avatar.png", optimize=True)
    for f in ("portada.svg", "avatar.png"):
        print(f, (RAIZ / "assets" / f).stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
