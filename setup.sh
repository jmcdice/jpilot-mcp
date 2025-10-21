#!/bin/bash
# Setup script for jpilot-mcp

set -e

echo "Setting up jpilot-mcp..."

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    echo "Error: Python 3.11+ is required but not found."
    echo "Please install Python 3.11 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install package in development mode
echo "Installing jpilot-mcp in development mode..."
pip install -e ".[dev]"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please edit .env and add your Jira credentials!"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Jira credentials"
echo "2. Run tests: pytest"
echo "3. Configure Claude Desktop (see README.md)"

