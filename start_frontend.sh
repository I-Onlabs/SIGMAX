#!/bin/bash
# SIGMAX Frontend Startup Script

echo "🚀 Starting SIGMAX Frontend..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

NODE_VERSION=$(node --version | grep -oP '(?<=v)\d+')
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "⚠️  Node.js 18+ required. Found: v$NODE_VERSION"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo ""

# Navigate to frontend directory
cd ui/web

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
    echo ""
fi

echo "✅ Dependencies OK"
echo ""

# Check if backend is running
echo "🔍 Checking backend connection..."
curl -s http://localhost:8000/health > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  Backend not detected at http://localhost:8000"
    echo "   Please start the backend first:"
    echo "   ./start_backend.sh"
    echo ""
    echo "   Continuing anyway..."
    echo ""
else
    echo "✅ Backend is running"
    echo ""
fi

# Start the frontend
echo "🌐 Starting React frontend on http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

npm run dev
