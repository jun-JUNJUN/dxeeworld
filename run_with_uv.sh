#!/bin/bash

# Simple UV-based server runner
# This script uses uv without requiring package installation

set -e  # Exit on any error

echo "🚀 Starting Startup Platform Server with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment and installing dependencies..."
    uv venv
    uv pip install -r requirements.txt
else
    echo "✅ Virtual environment already exists"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file from example..."
    cp .env.example .env
fi

# Function to run server
run_server() {
    echo "🌟 Starting server..."
    echo "📍 Server will be available at: http://localhost:8202"
    echo "🔍 Health check endpoint: http://localhost:8202/health"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo "----------------------------------------"
    
    uv run --with-requirements requirements.txt python run_server.py
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    uv run --with-requirements requirements.txt pytest
}

# Parse command line arguments
case "${1:-server}" in
    "server"|"start")
        run_server
        ;;
    "test"|"tests")
        run_tests
        ;;
    "help"|"-h"|"--help")
        echo "Simple UV-based Server Runner"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  server, start    Start the web server (default)"
        echo "  test, tests      Run the test suite"
        echo "  help             Show this help message"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac