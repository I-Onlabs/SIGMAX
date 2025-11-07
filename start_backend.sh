#!/bin/bash
# SIGMAX Backend Startup Script

echo "🚀 Starting SIGMAX Backend..."
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Please configure it before running in production."
    echo ""
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
REQUIRED_VERSION="3.11"

if (( $(echo "$PYTHON_VERSION $REQUIRED_VERSION" | awk '{print ($1 < $2)}') )); then
    echo "❌ Python $REQUIRED_VERSION or higher required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"
echo ""

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Dependencies not installed. Installing..."
    pip install -r core/requirements.txt
    pip install -r ui/api/requirements.txt
fi

echo "✅ Dependencies OK"
echo ""

# Check if Ollama is running (if LLM_PROVIDER=ollama)
if grep -q "LLM_PROVIDER=ollama" .env 2>/dev/null; then
    echo "🤖 Checking Ollama..."
    curl -s http://localhost:11434/api/tags > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "⚠️  Ollama not detected. Options:"
        echo "   1. Install Ollama: https://ollama.ai"
        echo "   2. Or use OpenAI/Anthropic (edit .env: LLM_PROVIDER=openai)"
        echo ""
    else
        echo "✅ Ollama is running"
        echo ""
    fi
fi

# Start the backend
echo "🌐 Starting FastAPI backend on http://localhost:8000"
echo "📚 API docs will be at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

uvicorn ui.api.main:app --reload --host 0.0.0.0 --port 8000
