#!/bin/bash
# Quick setup script for MCP Codebase Analyser

echo "🚀 MCP Codebase Analyser - Quick Setup"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Step 1: Creating .env file..."
    cp env.example .env
    echo ""
    echo "⚠️  IMPORTANT: You need to edit .env file NOW!"
    echo ""
    echo "Required: Add your OpenAI API key"
    echo "Get one here: https://platform.openai.com/api-keys"
    echo ""
    echo "Run this command to edit:"
    echo "  nano .env"
    echo ""
    echo "Then change this line:"
    echo "  LLM_API_KEY=your_api_key_here"
    echo ""
    echo "To your real key:"
    echo "  LLM_API_KEY=sk-your-actual-key-here"
    echo ""
    echo "Press Ctrl+X, then Y, then Enter to save"
    echo ""
    read -p "Press Enter after you've edited .env..."
fi

echo "✅ Step 1: .env file exists"
echo ""

# Check API key
if grep -q "your_api_key_here" .env 2>/dev/null; then
    echo "❌ ERROR: You haven't set your OpenAI API key yet!"
    echo ""
    echo "Edit .env and replace 'your_api_key_here' with your real key"
    echo "Run: nano .env"
    exit 1
fi

echo "✅ API key appears to be set"
echo ""

echo "🐳 Step 2: Building Docker image..."
echo "This will take 2-3 minutes the first time..."
echo ""

docker-compose build

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Docker build failed!"
    echo "Make sure Docker Desktop is running"
    exit 1
fi

echo ""
echo "✅ Docker image built successfully!"
echo ""

echo "🚀 Step 3: Starting server..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Failed to start server!"
    exit 1
fi

echo ""
echo "⏳ Waiting for server to start..."
sleep 3

echo ""
echo "📊 Checking server status..."
docker-compose ps
echo ""

echo "📝 Server logs:"
docker-compose logs | tail -20
echo ""

echo "✅✅✅ SUCCESS! ✅✅✅"
echo ""
echo "Your MCP Codebase Analyser is now running! 🎉"
echo ""
echo "🔍 Check full logs:"
echo "   docker-compose logs -f"
echo ""
echo "📋 Next: Configure Cursor"
echo "   See START_HERE.md - Step 4"
echo ""
echo "🎯 Then try in Cursor:"
echo "   'Analyze the jolly-commerce/jolly-sections repository'"
echo ""
