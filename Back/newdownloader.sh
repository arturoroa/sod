#!/bin/bash
# Gemma 4 26B Q2_K_XL para 12GB VRAM (Unsloth Dynamic Q2)

MODEL_NAME="gemma4-26b-q2"
GGUF_URL="https://huggingface.co/unsloth/gemma-4-26B-A4B-it-GGUF/resolve/main/gemma-4-26B-A4B-it-UD-Q2_K_XL.gguf"
GGUF_FILE="gemma-4-26B-A4B-it-UD-Q2_K_XL.gguf"

echo "🧠 Descargando Gemma 4 26B UD-Q2_K_XL (~10GB VRAM)..."
wget -c "$GGUF_URL" -O "$GGUF_FILE" --progress=bar:force:noscroll

ls -lh "$GGUF_FILE"

cat > Modelfile << EOF
FROM ./$GGUF_FILE
PARAMETER num_gpu 999  
PARAMETER temperature 0.8
PARAMETER top_p 0.9
EOF

ollama rm "$MODEL_NAME" 2>/dev/null || true
ollama create "$MODEL_NAME" -f Modelfile

rm "$GGUF_FILE" Modelfile

echo "🎉 Listo! OLLAMA_MODEL=$MODEL_NAME"
echo "ollama serve &"
echo "ollama run $MODEL_NAME 'Hola'"
