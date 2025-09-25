#!/bin/bash

# NegotiBot AI Startup Script
echo "🤖 Starting NegotiBot AI Professional Negotiation Assistant..."

# Check if dependencies are installed
echo "📦 Checking dependencies..."
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check environment configuration
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Please copy .env.example to .env and configure your Gemini API key."
    exit 1
fi

# Start the backend server
echo ""
echo "🚀 Starting NegotiBot edAI Backend..."
echo "   • Professional Interface: http://localhost:8000/full-interface/"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Demo Interface: http://localhost:8000/demo/"
echo "   • Seller Interface: http://localhost:8000/seller/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python3 main.py