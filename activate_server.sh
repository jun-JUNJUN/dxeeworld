#!/bin/bash

# Startup Platform Server Activation Script
# This script sets up and runs the server using uv

set -e  # Exit on any error

echo "🚀 Starting Startup Platform Server..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create pyproject.toml if it doesn't exist
if [ ! -f "pyproject.toml" ]; then
    echo "📝 Creating pyproject.toml..."
    cat > pyproject.toml << EOF
[project]
name = "startup-platform"
version = "0.1.0"
description = "Kaggle-like startup ecosystem platform"
requires-python = ">=3.9"
dependencies = [
    "tornado==6.5.2",
    "motor==3.3.2",
    "bcrypt==4.1.2",
    "jinja2==3.1.3",
    "python-dotenv==1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest==7.4.4",
    "pytest-asyncio==0.21.1",
    "pytest-tornado==0.8.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
EOF
fi

# Install dependencies using uv
echo "📦 Installing dependencies with uv..."
uv sync --no-install-project

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file from example..."
    cp .env.example .env
fi

# Function to run server
run_server() {
    echo "🌟 Starting server with uv..."
    echo "📍 Server will be available at: http://localhost:8202"
    echo "🔍 Health check endpoint: http://localhost:8202/health"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo "----------------------------------------"
    
    uv run python run_server.py
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests with uv..."
    uv run pytest
}

# Parse command line arguments
case "${1:-server}" in
    "server"|"start")
        run_server
        ;;
    "test"|"tests")
        run_tests
        ;;
    "install")
        echo "✅ Dependencies installed successfully!"
        ;;
    "help"|"-h"|"--help")
        echo "Startup Platform Server Activation Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  server, start    Start the web server (default)"
        echo "  test, tests      Run the test suite"
        echo "  install          Install dependencies only"
        echo "  help             Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0               # Start server"
        echo "  $0 server        # Start server"
        echo "  $0 test          # Run tests"
        echo "  $0 install       # Install dependencies"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac