#!/bin/bash
# Test script for MCP Codebase Analyser

echo "🧪 Testing MCP Codebase Analyser Setup"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from env.example..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ Created .env file. Please edit it with your credentials."
        echo ""
        echo "Required variables:"
        echo "  - LLM_API_KEY (OpenAI API key)"
        echo "  - GITHUB_TOKEN (optional, but recommended)"
        echo ""
        echo "After editing .env, run this script again."
        exit 1
    else
        echo "❌ env.example not found!"
        exit 1
    fi
fi

echo "✅ .env file exists"
echo ""

# Check Docker
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "   Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running"
    echo "   Please start Docker Desktop"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check docker-compose
echo "Checking docker-compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose is not installed"
    exit 1
fi

echo "✅ docker-compose is available"
echo ""

# Build Docker image
echo "🐳 Building Docker image..."
echo "This may take a few minutes on first run..."
echo ""

if docker-compose build; then
    echo ""
    echo "✅ Docker image built successfully"
else
    echo ""
    echo "❌ Docker build failed"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop the server:"
echo "  docker-compose down"
echo ""
echo "Next steps:"
echo "1. Start the server: docker-compose up -d"
echo "2. Configure Cursor MCP settings (see README.md)"
echo "3. In Cursor, try: 'Analyze the facebook/react repository'"
echo ""

