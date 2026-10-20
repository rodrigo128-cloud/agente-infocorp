# Agente de presupuestos Infocorp

Proyecto para armar presupuestos (cotizaciones) de Infocorp Enterprise S.R.L. en PDF con el modelo oficial.

- Para cualquier pedido de presupuesto, cotización o precio de un equipo, usa el subagente `presupuestos-infocorp` (`.claude/agents/presupuestos-infocorp.md`), que tiene todas las reglas.
- `generar_presupuesto.py`: genera el PDF desde un JSON. Usa Edge en Windows y Chromium/Chrome en Linux.
- `buscar_precios.py`: consulta precios en Compras Paraguai.
- `config.json`: tipo de cambio, factor de precio y mínimo de ofertas.
- `plantilla/`: diseño del PDF y guía de estilo de descripciones.
- `presupuestos/contador.txt`: último número de presupuesto usado.

## En la nube (claude.ai/code)

Si falta el navegador para generar PDFs, ejecuta `bash instalar_nube.sh` una vez por sesión.
Los PDF generados no se guardan en el repositorio (ver `.gitignore`): al terminar, envíalos al usuario.
Si se generan presupuestos en la nube, haz commit de `presupuestos/contador.txt` para no repetir números.
