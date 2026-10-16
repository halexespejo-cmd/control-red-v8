#!/bin/bash

# Script para subir control-red-v8 a GitHub
# Uso: ./upload.sh TU_TOKEN_AQUI

if [ -z "$1" ]; then
    echo "❌ Error: Debes proporcionar tu GitHub token"
    echo "Uso: ./upload.sh ghp_tu_token_aqui"
    echo ""
    echo "O usa variable de entorno:"
    echo "GITHUB_TOKEN=ghp_tu_token ./upload.sh"
    exit 1
fi

TOKEN="${1:-$GITHUB_TOKEN}"
REPO="halexespejo-cmd/control-red-v8"
FILE="index.html"
SHA="b1bc78dc4fa0f85e8af109297ff1b8e6d23252f7"

echo "📦 Codificando archivo..."
CONTENT=$(base64 -w 0 index.html)

echo "🚀 Subiendo a GitHub..."
RESPONSE=$(curl -s -X PUT \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$REPO/contents/$FILE \
  -d "{
    \"message\": \"Actualizar v8 para pruebas - $(date +%Y%m%d-%H%M)\",
    \"content\": \"$CONTENT\",
    \"sha\": \"$SHA\"
  }")

if echo "$RESPONSE" | grep -q "\"commit\""; then
    echo "✅ ¡Archivo subido exitosamente!"
    echo ""
    echo "🌐 URLs para probar:"
    echo "GitHack:      https://raw.githack.com/halexespejo-cmd/control-red-v8/main/index.html"
    echo "GitHub Pages: https://halexespejo-cmd.github.io/control-red-v8/"
    echo ""
    echo "⏳ Espera 1-2 minutos para que GitHub procese los cambios"
else
    echo "❌ Error al subir:"
    echo "$RESPONSE" | grep -o '"message":"[^"]*"'
fi
