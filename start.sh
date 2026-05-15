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
    export $(cat .env | grep -v '^#' | xargs)
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

if [ -z "$OPENAI_API_KEY" ]; then
    echo "ℹ️  Note: OPENAI_API_KEY not set (optional)"
else
    echo "✅ OpenAI API key configured"
fi

# Check optional configurations
if [ -z "$SMTP_HOST" ]; then
    echo "ℹ️  Email notifications not configured (optional)"
else
    echo "✅ Email notifications configured"
fi

if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo "ℹ️  Slack notifications not configured (optional)"
else
    echo "✅ Slack notifications configured"
fi

echo ""
echo "🚀 Starting AuditAura services..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker and try again"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose not found"
    echo "   Please install docker-compose and try again"
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start services
echo "🔨 Building and starting services..."
echo ""
docker-compose up --build -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check service health
echo ""
echo "🏥 Checking service health..."
echo ""

# Check backend
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend API is running"
else
    echo "⚠️  Backend API not responding yet (may still be starting)"
fi

# Check frontend
if curl -s http://localhost:3000/ > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend not responding yet (may still be starting)"
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
echo "💡 Semicolons Portal Tip:"
echo "   When deployed, remember to append '?app=<your_app_id>' to the URL."
echo "   The portal routes traffic based on this identifier."
echo ""
echo "👤 Login Flow:"
echo "   1. Navigate to http://localhost:3000"
echo "   2. Enter any email/password (demo mode)"
echo "   3. Select your role"
echo ""
echo "📊 Features:"
echo "   • Real-time compliance monitoring"
echo "   • AI-powered violation detection"
echo "   • Multi-channel alerts (UI, Email, Slack)"
echo "   • Interactive dashboards with live charts"
echo "   • PDF compliance document ingestion"
echo ""
echo "🔧 Useful Commands:"
echo "   • View logs:     docker-compose logs -f"
echo "   • Stop services: docker-compose down"
echo "   • Restart:       docker-compose restart"
echo ""
echo "📚 Documentation:"
echo "   • README.md for detailed usage"
echo "   • IMPLEMENTATION_SUMMARY.md for technical details"
echo ""
echo "Press Ctrl+C to stop viewing logs, or run 'docker-compose logs -f' to follow"
echo ""

# Follow logs
docker-compose logs -f

# Made with Bob
