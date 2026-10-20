#!/usr/bin/env bash
# Prepara el entorno de la nube (Linux) para generar PDFs.
set -e
if command -v chromium >/dev/null 2>&1 || command -v chromium-browser >/dev/null 2>&1 \
   || command -v google-chrome >/dev/null 2>&1; then
  echo "Navegador ya instalado."
  exit 0
fi
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq chromium || $SUDO apt-get install -y -qq chromium-browser
$SUDO apt-get install -y -qq fonts-liberation fonts-dejavu-core || true
echo "Listo."
