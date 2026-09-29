#!/bin/bash
# Script para descargar Gemma 4 26B-A4B Q4_K_M (16.8GB VRAM) e importarlo a Ollama

set -e

MODEL_NAME="gemma4-26b-q4"
GGUF_URL="https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF/resolve/main/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
GGUF_FILE="gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"

echo "🧠 Descargando Gemma 4 26B-A4B Q4_K_M (~16.8GB para 16GB VRAM)..."
echo "📁 Archivo: $GGUF_FILE"
echo "⏱️  Toma 5-20min dependiendo de tu conexión"

# Descarga con wget (resume si se interrumpe)
wget -c "$GGUF_URL" -O "$GGUF_FILE"

echo "✅ Descarga completa. Verificando..."
ls -lh "$GGUF_FILE"

# Crea Modelfile
cat > Modelfile << EOF
FROM ./$GGUF_FILE
PARAMETER temperature 0.8
PARAMETER top_p 0.9
PARAMETER top_k 40
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
EOF

# Limpia modelo anterior si existe
ollama rm "$MODEL_NAME" 2>/dev/null || true

# Importa a Ollama
echo "🔄 Importando a Ollama como '$MODEL_NAME'..."
ollama create "$MODEL_NAME" -f Modelfile

# Limpieza
rm "$GGUF_FILE" Modelfile

echo "🎉 Listo! Usa en .env: OLLAMA_MODEL=$MODEL_NAME"
echo ""
echo "Prueba:"
echo "ollama serve &"
echo "ollama run $MODEL_NAME 'Hola, responde en español'"
