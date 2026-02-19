#!/bin/bash

# Smart Home Assistant Auto Runner (Portable)
# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install edge_tts requests
fi

# Check if ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 5
fi

# Check if required models exist
if ! ollama list | grep -q "llama3.1:8b"; then
    echo "Downloading llama3.1:8b model..."
    ollama pull llama3.1:8b
fi

# Run assistant
echo "Starting Smart Home Assistant..."
python assistant.py
