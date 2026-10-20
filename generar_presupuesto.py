"""Genera un presupuesto de Infocorp en PDF a partir de un archivo JSON.

Uso:
    python generar_presupuesto.py datos.json

Formato del JSON:
{
  "cliente": "EMPRESA S.A.",
  "ruc": "80009243-0",                    (opcional)
  "atencion": "Ing. Juan Pérez",          (opcional)
  "fecha": "2026-10-12",                  (opcional, por defecto hoy)
  "numero": 168,                          (opcional; si se omite usa el siguiente y avanza el contador)
  "items": [
    {"cantidad": 1, "descripcion": "NB HP VICTUS ...", "precio_unitario": 20398000}
  ],
  "garantia": "1 AÑO",                    (opcional)
  "plazo_entrega": "INMEDIATA",
  "forma_pago": "CONTADO",
  "validez": "8 DIAS",
  "nota_iva": "Precios IVA incluido.",    (opcional)
  "moneda": "USD",                        (opcional; por defecto guaraníes)
  "observaciones": ["texto", "texto"]     (opcional; lista bajo las condiciones)
}
"""
import html
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent
PLANTILLA = BASE / "plantilla" / "presupuesto.html"
LOGO = BASE / "assets" / "infocorp-logo.png"
SALIDA = BASE / "presupuestos"
CONTADOR = SALIDA / "contador.txt"
NAVEGADORES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",  # Windows (PC de Infocorp)
    "chromium", "chromium-browser", "google-chrome", "google-chrome-stable",  # Linux (nube)
    "msedge", "microsoft-edge",
]


def navegador():
    for candidato in NAVEGADORES:
        ruta = candidato if Path(candidato).exists() else shutil.which(candidato)
        if ruta:
            return ruta
    sys.exit("No se encontró Edge, Chrome ni Chromium para generar el PDF.")
FILAS_MINIMAS = 8


def guaranies(valor):
    return "Gs. " + f"{round(valor):,}".replace(",", ".")


def dolares(valor):
    # Formato local: punto de miles y coma decimal (US$ 16.500,00)
    texto = f"{valor:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return "US$ " + texto


def nombre_archivo(texto):
    return "".join(c for c in texto if c not in '<>:"/\\|?*').strip().rstrip(".")


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: python generar_presupuesto.py datos.json")
    datos = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

    ultimo = int(CONTADOR.read_text().strip()) if CONTADOR.exists() else 0
    numero = int(datos.get("numero") or ultimo + 1)
    fecha = date.fromisoformat(datos["fecha"]) if datos.get("fecha") else date.today()
    monto = dolares if datos.get("moneda", "GS").upper() == "USD" else guaranies

    filas, total = [], 0
    for item in datos["items"]:
        cant = item["cantidad"]
        pu = item["precio_unitario"]
        subtotal = cant * pu
        total += subtotal
        filas.append(
            f'<tr><td class="cant">{cant:g}</td><td>{html.escape(item["descripcion"])}</td>'
            f'<td class="pu">{monto(pu)}</td><td class="tot">{monto(subtotal)}</td></tr>'
        )
    observaciones = "".join(f"<li>{html.escape(o)}</li>" for o in datos.get("observaciones", []))
    # Con observaciones se usan menos filas de relleno para no pasar a una segunda hoja.
    while len(filas) < (FILAS_MINIMAS if not observaciones else 4):
        filas.append('<tr><td></td><td></td><td></td><td></td></tr>')

    campos = {
        "LOGO": LOGO.as_uri(),
        "NUMERO": f"{numero:06d}",
        "DIA": str(fecha.day),
        "MES": str(fecha.month),
        "ANIO": str(fecha.year),
        "CLIENTE": html.escape(datos.get("cliente", ""))
                   + (f" &nbsp;·&nbsp; RUC: {html.escape(datos['ruc'])}" if datos.get("ruc") else ""),
        "ATENCION": html.escape(datos.get("atencion", "")),
        "FILAS": "\n".join(filas),
        "TOTAL": monto(total),
        "OBSERVACIONES": (f'<div class="observaciones"><b>OBSERVACIONES</b><ul>{observaciones}</ul></div>'
                          if observaciones else ""),
        "NOTA_IVA": html.escape(datos.get("nota_iva", "Precios IVA incluido.")),
        "GARANTIA": html.escape(datos.get("garantia", "")),
        "PLAZO_ENTREGA": html.escape(datos.get("plazo_entrega", "")),
        "FORMA_PAGO": html.escape(datos.get("forma_pago", "")),
        "VALIDEZ": html.escape(datos.get("validez", "")),
    }
    contenido = PLANTILLA.read_text(encoding="utf-8")
    for clave, valor in campos.items():
        contenido = contenido.replace("{{" + clave + "}}", valor)

    SALIDA.mkdir(exist_ok=True)
    base = f"Presupuesto {numero:06d} {nombre_archivo(datos.get('cliente', ''))}".strip()
    html_path = SALIDA / f"{base}.html"
    pdf_path = SALIDA / f"{base}.pdf"
    html_path.write_text(contenido, encoding="utf-8")
    if pdf_path.exists():
        pdf_path.unlink()  # si no, un PDF viejo pasaría como generado

    # Perfil nuevo en cada corrida para que no se enganche a un Edge ya abierto.
    perfil = tempfile.mkdtemp(prefix="edge_presupuestos_")
    proceso = subprocess.Popen(
        [navegador(), "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
         f"--user-data-dir={perfil}", f"--print-to-pdf={pdf_path}", html_path.as_uri()],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # Edge a veces escribe el PDF y no termina: se espera al archivo, no al proceso.
    tamano_anterior, limite = -1, time.time() + 90
    while time.time() < limite:
        if pdf_path.exists():
            tamano = pdf_path.stat().st_size
            if tamano > 0 and tamano == tamano_anterior:
                break
            tamano_anterior = tamano
        elif proceso.poll() is not None:
            break
        time.sleep(1)
    if proceso.poll() is None:
        proceso.kill()
    shutil.rmtree(perfil, ignore_errors=True)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        sys.exit("No se pudo generar el PDF.")
    html_path.unlink()

    if not datos.get("numero"):
        CONTADOR.write_text(str(numero))
    print(f"OK {pdf_path}")
    print(f"TOTAL {monto(total)}")


if __name__ == "__main__":
    main()
