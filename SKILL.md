---
name: presupuestos-infocorp
description: Arma presupuestos (cotizaciones) de Infocorp Enterprise S.R.L. con su modelo oficial y los entrega en PDF. Busca precios de referencia en Compras Paraguai cuando no se dan. Usar cuando pidan un presupuesto, cotización o proforma para un cliente, el precio de un equipo (notebook, PC, monitor, impresora, UPS, accesorios), o rehacer/corregir un presupuesto existente.
---

# Presupuestos Infocorp

Todas las rutas son relativas a la carpeta de esta skill. Ejecuta los comandos desde aquí (`cd` a esta carpeta).

## Antes de empezar

1. **Lee las reglas completas** en `.claude/agents/presupuestos-infocorp.md`: datos obligatorios, búsqueda de precios, criterios de selección de modelos, cálculo de precios, armado de PCs por componentes, formato del JSON y respuesta al usuario. Síguelas al pie de la letra.
2. **Lee la guía de estilo** `plantilla/estilo_descripciones.md` antes de escribir las descripciones de los ítems.
3. Usa `python3` si `python` no existe en el sistema.
4. Si no hay Edge, Chrome ni Chromium instalado, en Linux ejecuta `bash instalar_nube.sh`.

## Herramientas

- `python buscar_precios.py buscar "<texto>"`: lista modelos en Compras Paraguai con cantidad de ofertas.
- `python buscar_precios.py ofertas "<url>"`: ofertas por tienda de un modelo.
- `python generar_presupuesto.py <datos.json>`: genera el PDF en `presupuestos/` e imprime `OK <ruta>` y `TOTAL ...`.
- `config.json`: tipo de cambio (6300), factor de precio (1.43), mínimo de ofertas (2).

## Entrega

La respuesta siempre es el PDF: envía el archivo generado al usuario por el canal en el que pidió el presupuesto, con un resumen breve (número, cliente, ítems, total y avisos).

## Numeración

`presupuestos/contador.txt` guarda el último número usado. Si esta carpeta es un clon de git compartido con otra máquina, haz `git pull` antes de generar y, después, commit y push de `presupuestos/contador.txt` para no repetir números.
