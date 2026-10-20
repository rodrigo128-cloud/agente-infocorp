"""Consulta precios en Compras Paraguai (mobile.comprasparaguai.com.br).

Uso:
    python buscar_precios.py buscar "notebook hp victus i7"   lista modelos con cantidad de ofertas
    python buscar_precios.py ofertas <url-del-modelo>          detalle de ofertas de un modelo

Opción: --salida archivo.json  (guarda el resultado además de imprimirlo)

Reglas de ofertas (config.json -> "min_ofertas", por defecto 2):
  - estado "OK":      el modelo tiene al menos min_ofertas ofertas.
  - estado "AVISO":   tiene menos (normalmente 1 sola oferta): avisar al usuario.
"""
import html
import json
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
SITIO = "https://mobile.comprasparaguai.com.br"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Accept-Language": "es-PY,es;q=0.9,pt-BR;q=0.8",
}


def config():
    archivo = BASE / "config.json"
    return json.loads(archivo.read_text(encoding="utf-8")) if archivo.exists() else {}


def descargar(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def texto(fragmento):
    sin_tags = re.sub(r"<[^>]+>", " ", fragmento)
    return re.sub(r"\s+", " ", html.unescape(sin_tags)).strip()


def dolares(cadena):
    m = re.search(r"US\$\s*([\d.]+,\d{2})", html.unescape(cadena).replace("\xa0", " "))
    return float(m.group(1).replace(".", "").replace(",", ".")) if m else None


def bloques(pagina):
    partes = re.split(r'<div class="promocao-produtos-item[ "]', pagina)
    return partes[1:]


def buscar(consulta):
    url = f"{SITIO}/busca/?q={urllib.parse.quote_plus(consulta)}"
    pagina = descargar(url)
    minimo = config().get("min_ofertas", 2)
    resultados = []
    for b in bloques(pagina):
        nombre = re.search(r'class="promocao-item-nome">\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b, re.S)
        if not nombre:
            continue
        cant = re.search(r"(\d+)\s+OFERTAS?", b, re.I)
        n = int(cant.group(1)) if cant else 1
        resultados.append({
            "nombre": texto(nombre.group(2)),
            "url": urllib.parse.urljoin(SITIO, nombre.group(1)),
            "desde_usd": dolares(b),
            "ofertas": n,
            "estado": "OK" if n >= minimo else "AVISO",
        })
    return {"consulta": consulta, "url": url, "min_ofertas": minimo, "resultados": resultados}


def ofertas(url):
    pagina = descargar(url)
    minimo = config().get("min_ofertas", 2)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", pagina, re.S)
    total = re.search(r"Encontramos</span>\s*(\d+)\s+ofertas?", pagina, re.I) \
        or re.search(r"Compare\s+(\d+)\s+ofertas?", pagina, re.I)

    # Solo la sección de ofertas: después vienen "productos relacionados" que no cuentan.
    seccion = pagina.split('id="container-ofertas"', 1)[-1]
    lista = []
    for b in bloques(seccion):
        nombre = re.search(r'class="promocao-item-nome">\s*<a[^>]*>(.*?)</a>', b, re.S)
        tienda = re.search(r'<a href="/lojas/([^/"]+)/">\s*(?:<img[^>]*alt="([^"]*)")?', b)
        precio = dolares(b)
        if not nombre or not tienda or precio is None:
            continue
        lista.append({
            "tienda": html.unescape(tienda.group(2) or tienda.group(1)),
            "producto": texto(nombre.group(1)),
            "precio_usd": precio,
        })
    if 'id="container-ofertas"' not in pagina:
        # Página de una sola tienda (URL con "__"): tienda y precio vienen en los metadatos.
        og = re.search(r'property="og:title" content="([^"]*)"', pagina)
        monto = re.search(r'property="product:price:amount" content="([\d.]+)"', pagina)
        titulo = html.unescape(og.group(1)) if og else ""
        m = re.search(r"(.*) na loja (.*) no Paraguai", titulo)
        lista = [{
            "tienda": m.group(2) if m else "",
            "producto": m.group(1) if m else titulo,
            "precio_usd": float(monto.group(1)),
        }] if monto else []
        total = None
    lista.sort(key=lambda o: o["precio_usd"])

    n = int(total.group(1)) if total else len(lista)
    precios = [o["precio_usd"] for o in lista]
    resultado = {
        "modelo": texto(h1.group(1)) if h1 else "",
        "url": url,
        "ofertas_totales": n,
        "ofertas_leidas": len(lista),
        "min_ofertas": minimo,
        "estado": "OK" if n >= minimo else "AVISO",
        "minimo_usd": min(precios) if precios else None,
        "mediana_usd": statistics.median(precios) if precios else None,
        "maximo_usd": max(precios) if precios else None,
        "ofertas": lista,
    }
    if resultado["estado"] == "AVISO":
        resultado["aviso"] = (f"Solo {n} oferta(s): el precio no está contrastado con otras tiendas. "
                              "Confirmar con el usuario antes de usarlo.")
    return resultado


def main():
    args = sys.argv[1:]
    salida = None
    if "--salida" in args:
        i = args.index("--salida")
        salida = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2 or args[0] not in ("buscar", "ofertas"):
        sys.exit(__doc__)

    modo, valor = args
    datos = buscar(valor) if modo == "buscar" else ofertas(valor)
    time.sleep(1)  # no saturar el sitio cuando se encadenan consultas
    salida_json = json.dumps(datos, ensure_ascii=False, indent=2)
    if salida:
        Path(salida).write_text(salida_json, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(salida_json)


if __name__ == "__main__":
    main()
