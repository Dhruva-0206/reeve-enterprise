#!/bin/bash
# Quick Start Script for Enterprise Knowledge Investigator
# Run: bash quickstart.sh

set -e

echo "========================================"
echo "Enterprise Knowledge Investigator"
echo "Quick Start Setup"
echo "========================================"
echo ""

# Check Python version
echo "1. Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python: $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "2. Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
else
    echo "   ✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "3. Activating virtual environment..."
source venv/bin/activate
echo "   ✓ Activated"

# Install dependencies
echo ""
echo "4. Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -q -r requirements.txt
echo "   ✓ Dependencies installed"

# Setup environment file
echo ""
echo "5. Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "   ✓ .env created from template"
    echo ""
    echo "   ⚠ IMPORTANT: Edit .env with your API keys"
    echo "   - Reeve: https://mcp.reeve.co.in"
    echo "   - GitHub: Personal Access Token"
    echo "   - Jira: API Token"
    echo "   - Slack: Bot Token"
else
    echo "   ✓ .env already exists"
fi

# Run validation
echo ""
echo "6. Running validation..."
python validate.py

# Show next steps
echo ""
echo "========================================"
echo "✓ Setup Complete!"
echo "========================================"
echo ""
echo "Next Steps:"
echo "  1. Edit .env with your API credentials"
echo "  2. Run: python cli.py status config"
echo "  3. Run: python cli.py ingest all"
echo "  4. Run: python cli.py server start"
echo "  5. Visit: http://localhost:8000/docs"
echo ""
echo "For more info: cat README.md"
