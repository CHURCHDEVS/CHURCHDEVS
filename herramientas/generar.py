#!/usr/bin/env python3
"""Genera la identidad del perfil de GitHub de CHURCHDEVS.

Uso:  uv run --with fonttools --with brotli --with pillow python -I herramientas/generar.py
Salida: assets/portada.svg (cabecera animada) y assets/avatar.png (foto de perfil, 1000×1000).

Concepto «la señal entre el ruido»: puntos de datos sueltos (lo que se recopila), columnas
ordenadas (lo que se ordena), una línea de tendencia y una alerta amarilla (lo que se monitorea).
- Una sola fuente, Archivo (OFL, herramientas/fuentes/), convertida a trazos: GitHub muestra los
  SVG como imagen y no carga fuentes.
- Una sola secuencia de entrada (~1,7 s) y después solo el pulso de la alerta y la píldora que
  rota los servicios. Con «reducir movimiento» no se mueve nada y se ve el estado final.
"""
import io
import random
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / "herramientas/fuentes/archivo-latin-wdth-normal.woff2"

# Paleta: cobalto y amarillo señal (dato frío → señal cálida)
FONDO, LUZ, HUESO, CIELO, PUNTO, SENAL = "#0E1A5C", "#2440C4", "#F4F2EC", "#B4C6FF", "#7F97F0", "#FFC93C"
CURVA, ENFASIS = "cubic-bezier(.2,0,0,1)", "cubic-bezier(.05,.7,.1,1)"

SERVICIOS = ["Apps con IA", "Automatización", "Web scraping", "OSINT",
             "Seguimiento y monitoreo", "Marketing con datos"]
# Una serie que crece con un salto al final: es ilustración, no una métrica publicada
SERIE = [4, 5, 4, 6, 5, 5, 7, 6, 8, 7, 9, 12]


def fuente(peso: int, ancho: int) -> TTFont:
    return instancer.instantiateVariableFont(TTFont(str(ARCHIVO)), {"wght": peso, "wdth": ancho})


NOMBRE_F, ROL_F, TESIS_F, PILDORA_F = fuente(800, 62), fuente(600, 100), fuente(500, 100), fuente(700, 100)


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


def estilo(n_columnas: int) -> str:
    # pasos que se acortan (no metrónomo): la cascada de columnas dura < 500 ms
    retrasos, t = [], 360
    for i in range(n_columnas):
        retrasos.append(t)
        t += max(22, 52 - i * 3)
    cols = "".join(f".k{i}{{animation-delay:{d}ms}}" for i, d in enumerate(retrasos))
    ciclo = len(SERVICIOS) * 2.5
    a, b, c = 1.67, 100 / len(SERVICIOS) - 1.67, 100 / len(SERVICIOS)
    return f"""<style>
@keyframes sube{{from{{opacity:0;transform:translateY(14px)}}}}
@keyframes aparece{{from{{opacity:0}}}}
@keyframes traza{{from{{stroke-dashoffset:1}}}}
@keyframes alerta{{from{{opacity:0;transform:scale(.4)}}}}
@keyframes pulso{{0%{{opacity:0;transform:scale(.5)}}10%{{opacity:.9}}60%,100%{{opacity:0;transform:scale(2.4)}}}}
@keyframes rota{{0%{{opacity:0}}{a:.2f}%,{b:.2f}%{{opacity:1}}{c:.2f}%,100%{{opacity:0}}}}
.t{{animation:sube .44s {CURVA} both}}
.n{{animation:sube .6s {ENFASIS} .12s both}}
.r{{animation:aparece .5s {CURVA} both}}
.k{{animation:sube .44s {CURVA} both}}{cols}
.l{{stroke-dasharray:1;stroke-dashoffset:0;animation:traza .6s {CURVA} 1s both}}
.a{{transform-box:fill-box;transform-origin:center;animation:alerta .28s {CURVA} 1.5s both}}
.p{{transform-box:fill-box;transform-origin:center;opacity:0;animation:pulso 4s {CURVA} 1.9s infinite both}}
.c{{opacity:0;animation:rota {ciclo:g}s linear infinite both}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.c0{{opacity:1}}}}
</style>"""


def portada() -> str:
    w, h, x0 = 1000, 380, 52
    rnd = random.Random(7)
    # el ruido: puntos sueltos y tenues en toda la zona de la derecha
    ruido = "".join(
        f'<circle cx="{rnd.uniform(600, 975):.1f}" cy="{rnd.uniform(34, 350):.1f}" r="{rnd.uniform(1.6, 3.4):.1f}"/>'
        for _ in range(78))
    # el orden: columnas de puntos (una por periodo); la última es la señal
    base, paso_y, x_ini, paso_x = 332, 21, 642, 27.5
    cols, cima = [], []
    for i, v in enumerate(SERIE):
        x = x_ini + i * paso_x
        color = SENAL if i == len(SERIE) - 1 else PUNTO
        puntos = "".join(f'<circle cx="{x:.1f}" cy="{base - j * paso_y}" r="6"/>' for j in range(v))
        cols.append(f'<g class="k k{i}" fill="{color}">{puntos}</g>')
        cima.append((x, base - (v - 1) * paso_y))
    linea = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in cima)
    ax, ay = cima[-1]
    ay -= 30  # la alerta flota sobre la última columna
    nombre_tam = 118
    while ancho(NOMBRE_F, "CHURCHDEVS", nombre_tam) > 555:
        nombre_tam -= 2
    pildoras = []
    for i, s in enumerate(SERVICIOS):
        ancho_p = ancho(PILDORA_F, s, 20) + 36
        pildoras.append(
            f'<g class="c c{i}" style="animation-delay:{0.6 + i * 2.5:g}s">'
            f'<rect x="{x0}" y="308" width="{ancho_p:.0f}" height="40" rx="20" fill="{SENAL}"/>'
            f'<path fill="{FONDO}" d="{trazo(PILDORA_F, s, x0 + 18, 335, 20)}"/></g>')
    alt = "CHURCHDEVS, desarrollador de software: apps con IA que recopilan, ordenan y monitorean información"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
        f'aria-label="{alt}"><title>{alt}</title>{estilo(len(SERIE))}'
        f'<defs><radialGradient id="luz" cx="88%" cy="-8%" r="80%"><stop offset="0" stop-color="{LUZ}"/>'
        f'<stop offset="1" stop-color="{FONDO}" stop-opacity="0"/></radialGradient></defs>'
        f'<rect width="{w}" height="{h}" rx="20" fill="{FONDO}"/><rect width="{w}" height="{h}" rx="20" fill="url(#luz)"/>'
        f'<g class="r" fill="{CIELO}" fill-opacity=".22">{ruido}</g>'
        f'{"".join(cols)}'
        f'<path class="l" pathLength="1" d="{linea}" fill="none" stroke="{HUESO}" stroke-width="3" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle class="p" cx="{ax:.1f}" cy="{ay:.1f}" r="12" fill="none" stroke="{SENAL}" stroke-width="2.5"/>'
        f'<circle class="a" cx="{ax:.1f}" cy="{ay:.1f}" r="9" fill="{SENAL}" stroke="{FONDO}" stroke-width="3"/>'
        f'<path class="t" style="animation-delay:.05s" fill="{CIELO}" d="{trazo(ROL_F, "Desarrollador de software", x0, 84, 24)}"/>'
        f'<path class="n" fill="{HUESO}" d="{trazo(NOMBRE_F, "CHURCHDEVS", x0 - 3, 190, nombre_tam)}"/>'
        f'<path class="t" style="animation-delay:.3s" fill="{HUESO}" d="{trazo(TESIS_F, "Apps con IA que recopilan, ordenan", x0, 242, 31)}"/>'
        f'<path class="t" style="animation-delay:.36s" fill="{HUESO}" d="{trazo(TESIS_F, "y monitorean información.", x0, 282, 31)}"/>'
        f'{"".join(pildoras)}</svg>')


def letra_png(peso: int, ancho_eje: int, tam: int) -> ImageFont.FreeTypeFont:
    f = instancer.instantiateVariableFont(TTFont(str(ARCHIVO)), {"wght": peso, "wdth": ancho_eje})
    f.flavor = None
    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, tam)


def avatar() -> Image.Image:
    """Monograma CD con el punto de señal; pensado para el recorte circular de GitHub."""
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
