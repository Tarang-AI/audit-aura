#!/bin/bash

# AuditAura - Continuous Compliance Guardian
# Startup script for Docker Compose deployment

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         AuditAura - Continuous Compliance Guardian          ║"
echo "║              Real-time Audit Readiness Platform            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it with your API keys."
        echo ""
    else
        echo "❌ Error: .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Load environment variables from .env
if [ -f .env ]; then
    # Use a safer way to export .env variables
    export $(grep -v '^#' .env | xargs)
fi

# Check for required environment variables
echo "🔍 Checking environment configuration..."
echo ""

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set (OpenCode Zen)"
    echo "   PDF extraction and AI analysis will fall back to other providers"
    echo "   Set ANTHROPIC_API_KEY in .env file for Zen integration"
    echo ""
else
    echo "✅ OpenCode Zen (Anthropic) configured"
fi

# Check for Local vs Docker mode
USE_DOCKER=false
if [[ "$1" == "--docker" ]]; then
    USE_DOCKER=true
fi

if [ "$USE_DOCKER" = true ]; then
    echo "🐳 Mode: Docker Containers"
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Error: Docker is not running"
        echo "   Please start Docker and try again"
        exit 1
    fi

    # Stop any existing containers
    echo "🛑 Stopping existing containers..."
    docker-compose down 2>/dev/null || true

    # Build and start services
    echo "🔨 Building and starting services..."
    docker-compose up --build -d
else
    echo "💻 Mode: Local Development"
    
    # Handle port conflicts
    echo "🧹 Cleaning up existing processes on ports 8000 and 3000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    
    # Check for virtual environment
    if [ -d ".venv" ]; then
        PYTHON_PATH="./.venv/bin/python"
        echo "✅ Using existing virtual environment (.venv)"
    elif [ -d "backend/venv" ]; then
        PYTHON_PATH="./backend/venv/bin/python"
        echo "✅ Using existing backend virtual environment (backend/venv)"
    else
        echo "⚠️  No virtual environment found. Using system python..."
        PYTHON_PATH="python3"
    fi

    echo "🚀 Starting AuditAura services locally..."
    
    # Start Backend
    echo "📦 Starting Backend (Port 8000)..."
    cd backend
    ../$PYTHON_PATH main.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    # Start Frontend
    echo "🎨 Starting Frontend (Port 3000)..."
    cd frontend
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # Trap exit signal to kill background processes
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
    
    echo ""
    echo "⏳ Waiting for services to initialize..."
    sleep 5
fi

# Check service health
echo ""
echo "🏥 Checking service health..."
echo ""

# Check backend
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend API is running"
else
    echo "⚠️  Backend API not responding yet (check backend.log)"
fi

# Check frontend
if curl -s http://localhost:3000/ > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend not responding yet (check frontend.log)"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   🎉 AuditAura is Ready!                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📱 Access Points:"
echo "   • Frontend:  http://localhost:3000"
echo "   • Backend:   http://localhost:8000"
echo "   • API Docs:  http://localhost:8000/docs"
echo ""
if [ "$USE_DOCKER" = false ]; then
    echo "📄 Logs:"
    echo "   • Backend:  tail -f backend.log"
    echo "   • Frontend: tail -f frontend.log"
    echo ""
    echo "💡 Keep this terminal open to keep the services running."
    echo "   Press Ctrl+C to stop all services."
    echo ""
    
    # Keep script alive and follow backend logs
    tail -f backend.log
else
    echo "🔧 Useful Commands:"
    echo "   • View logs:     docker-compose logs -f"
    echo "   • Stop services: docker-compose down"
    echo ""
    docker-compose logs -f
fi

# Made with Bob
