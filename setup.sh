#!/usr/bin/env bash
# Setup automático del proyecto MUA Biodiversidad
set -e

PROYECTO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$PROYECTO_DIR/.venv"
BACKEND="$PROYECTO_DIR/backend"

echo "========================================"
echo " MUA Biodiversidad — Setup automático"
echo "========================================"

# ── 1. Virtualenv y dependencias Python ──────────────────────────────────────
echo ""
echo "[1/5] Configurando entorno Python..."
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$BACKEND/requirements.txt"
echo "      OK"

# ── 2. PostgreSQL — crear base de datos ──────────────────────────────────────
echo ""
echo "[2/5] Configurando PostgreSQL..."
if ! psql -U postgres -lqt 2>/dev/null | cut -d'|' -f1 | grep -qw "mua_biodiversidad"; then
    psql -U postgres -c "CREATE DATABASE mua_biodiversidad ENCODING 'UTF8';" > /dev/null
    echo "      Base de datos 'mua_biodiversidad' creada"
else
    echo "      Base de datos ya existe, omitiendo"
fi

# ── 3. Ollama — iniciar servicio ──────────────────────────────────────────────
echo ""
echo "[3/5] Iniciando Ollama..."
if ! pgrep -x ollama > /dev/null 2>&1; then
    if systemctl list-units --type=service 2>/dev/null | grep -q ollama; then
        sudo systemctl start ollama
        sleep 2
    else
        ollama serve > /dev/null 2>&1 &
        sleep 3
    fi
    echo "      Ollama iniciado"
else
    echo "      Ollama ya estaba corriendo"
fi

# ── 4. Descargar modelo gemma2:2b si no existe ───────────────────────────────
echo ""
echo "[4/5] Verificando modelo gemma2:2b..."
if ollama list 2>/dev/null | grep -q "gemma2:2b"; then
    echo "      Modelo ya descargado"
else
    echo "      Descargando gemma2:2b (puede tardar unos minutos)..."
    ollama pull gemma2:2b
    echo "      Modelo descargado"
fi

# ── 5. ETL — cargar datos ─────────────────────────────────────────────────────
echo ""
echo "[5/5] Cargando datos en la base de datos..."
cd "$BACKEND"
python3 main.py --etl

# ── Listo ─────────────────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo " Setup completo."
echo ""
echo " Para iniciar la API:"
echo "   cd backend && python3 main.py"
echo ""
echo " Documentación: http://localhost:8000/docs"
echo "========================================"
