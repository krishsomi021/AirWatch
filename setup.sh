#!/bin/bash

# WaterWatch Setup Script
echo "========================================="
echo "  WaterWatch Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ is required (found $python_version)"
    exit 1
fi
echo "✓ Python $python_version found"

# Check Node version
echo "Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi
echo "✓ Node.js $(node --version) found"

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
echo "✓ Virtual environment created"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
echo "✓ Python dependencies installed"

# Create .env file if it doesn't exist
cd ..
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created (please edit with your API keys)"
fi

# Train model
echo ""
echo "Training ML model with sample data..."
cd backend
python app/ml/train.py
echo "✓ Model trained"

# Install Node dependencies
echo ""
echo "Installing Node.js dependencies..."
cd ../web
npm install > /dev/null 2>&1
echo "✓ Node.js dependencies installed"

# Complete
cd ..
echo ""
echo "========================================="
echo "  Setup Complete! ✓"
echo "========================================="
echo ""
echo "To run the application:"
echo "  1. Start API:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  2. Start Web:  cd web && npm run dev"
echo ""
echo "Or use Docker:"
echo "  docker-compose up"
echo ""
echo "API Docs: http://localhost:8000/api/docs"
echo "Web UI:   http://localhost:3000"
echo ""
